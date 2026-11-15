import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache

from app.data.cache import DEMO_DIR, read_demo_json
from app.data.gee import GeeSiteSummary
from app.data.power import PowerDataset, _parse_power_payload
from app.data.site import SiteData, to_historic
from app.data.soil import DATA_RAW, load_farm_soil

FARMS: dict[str, tuple[float, float]] = {"iowa": (41.95, -93.71), "bajio": (20.52, -100.81)}
FARM_TOLERANCE_DEG = 0.1
DEFAULT_FARM = "iowa"
DEFAULT_ROTATIONS: dict[str, list[str]] = {"iowa": ["maize", "soybean"], "bajio": ["maize", "beans"]}
MONTH_KEYS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
CDL_CROPS: dict[str, str] = {
    "Corn": "maize",
    "Soybeans": "soybean",
    "Winter Wheat": "wheat",
    "Spring Wheat": "wheat",
    "Oats": "oats",
    "Sorghum": "sorghum",
    "Alfalfa": "alfalfa",
    "Rye": "rye",
    "Dry Beans": "beans",
}
CDL_CATEGORY = re.compile(r'category:\s*"([^"]+)"')
MIN_CROP_YEARS = 8
CDL_FIRST_YEAR = 2010


@dataclass(frozen=True)
class CdlSummary:
    first_year: int
    last_year: int
    total_years: int
    crop_years: int
    alternation_years: int
    non_crop_label: str
    crops: list[str]
    is_cropland: bool


def farm_for(lat: float, lon: float) -> str | None:
    for name, (farm_lat, farm_lon) in FARMS.items():
        if abs(lat - farm_lat) <= FARM_TOLERANCE_DEG and abs(lon - farm_lon) <= FARM_TOLERANCE_DEG:
            return name
    return None


def nearest_farm(lat: float, lon: float) -> str:
    def distance(item: tuple[str, tuple[float, float]]) -> float:
        farm_lat, farm_lon = item[1]
        return math.hypot(lat - farm_lat, (lon - farm_lon) * math.cos(math.radians(lat)))

    return min(FARMS.items(), key=distance)[0]


def _power_dataset(farm: str) -> PowerDataset:
    lat, lon = FARMS[farm]
    if farm == "bajio":
        return PowerDataset(**read_demo_json("bajio_power.json"))
    raw = json.loads((DATA_RAW / farm / "power_daily.json").read_text(encoding="utf-8"))
    return _parse_power_payload(lat, lon, raw)


def _climatology(farm: str) -> dict[str, dict[str, float]]:
    raw = json.loads((DATA_RAW / farm / "power_climatology.json").read_text(encoding="utf-8"))
    return raw["properties"]["parameter"]


def observed_soil_moisture(farm: str) -> list[float]:
    values = _climatology(farm)["GWETROOT"]
    return [round(float(values[key]), 3) for key in MONTH_KEYS]


def _power_elevation(farm: str) -> float:
    for name in ("power_daily.json", "power_climatology.json"):
        path = DATA_RAW / farm / name
        if path.exists():
            coordinates = json.loads(path.read_text(encoding="utf-8")).get("geometry", {}).get("coordinates", [])
            if len(coordinates) >= 3:
                return float(coordinates[2])
    return 0.0


def _verified_gee(farm: str) -> GeeSiteSummary | None:
    path = DATA_RAW / farm / "gee.json"
    if not path.exists():
        return None
    try:
        summary = GeeSiteSummary(**json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None
    return summary if summary.verified else None


@lru_cache(maxsize=4)
def load_farm_site(farm: str) -> SiteData:
    lat, lon = FARMS[farm]
    weather = to_historic(_power_dataset(farm))
    soil, slope_deg = load_farm_soil(farm)
    verified = _verified_gee(farm)
    if verified is not None:
        return SiteData(lat, lon, weather, verified, "demo", soil, True)
    climatology = _climatology(farm)
    span = soil.field_capacity - soil.wilting_point
    gee = GeeSiteSummary(
        source="power_derived",
        lat=lat,
        lon=lon,
        elevation_m=round(_power_elevation(farm), 1),
        slope_deg=slope_deg if slope_deg is not None else 1.0,
        sm_surface=round(soil.wilting_point + float(climatology["GWETTOP"]["ANN"]) * span, 3),
        sm_rootzone=round(soil.wilting_point + float(climatology["GWETROOT"]["ANN"]) * span, 3),
        gpm_annual_mm=None,
        modis_ndvi_monthly=[],
        grace_lwe_cm=None,
        verified=False,
    )
    return SiteData(lat, lon, weather, gee, "demo", soil, False)


def _cdl_crop(entry: str) -> tuple[str, str | None]:
    match = CDL_CATEGORY.search(entry or "")
    label = match.group(1) if match else (entry or "Unknown")
    return label, CDL_CROPS.get(label)


@lru_cache(maxsize=4)
def cdl_summary(farm: str) -> CdlSummary | None:
    path = DATA_RAW / farm / "cdl_history.json"
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    years = sorted(y for y in raw["grid"] if int(y) >= CDL_FIRST_YEAR)
    cells = len(raw["grid"][years[0]])
    best: list[tuple[str, str | None]] = []
    best_count = -1
    for cell in [4] + [c for c in range(cells) if c != 4]:
        sequence = [_cdl_crop(raw["grid"][year][cell]) for year in years]
        count = sum(1 for _, crop in sequence if crop)
        if count > best_count:
            best, best_count = sequence, count
    labels: dict[str, int] = {}
    for label, crop in best:
        if crop is None:
            labels[label] = labels.get(label, 0) + 1
    non_crop = max(labels, key=lambda k: labels[k]) if labels else "n/a"
    crops_seq = [crop for _, crop in best]
    alternation = sum(
        1 for a, b in zip(crops_seq, crops_seq[1:]) if {a, b} == {"maize", "soybean"}
    )
    counts: dict[str, int] = {}
    for crop in crops_seq:
        if crop:
            counts[crop] = counts.get(crop, 0) + 1
    is_cropland = best_count >= MIN_CROP_YEARS
    if is_cropland and alternation >= best_count // 2:
        last = next(c for c in reversed(crops_seq) if c)
        crops = ["soybean", "maize"] if last == "maize" else ["maize", "soybean"]
    elif is_cropland:
        crops = [c for c, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:2]]
    else:
        crops = list(DEFAULT_ROTATIONS[farm])
    return CdlSummary(int(years[0]), int(years[-1]), len(years), best_count, alternation, non_crop, crops, is_cropland)


def default_rotation(farm: str) -> list[str]:
    summary = cdl_summary(farm)
    return list(summary.crops) if summary else list(DEFAULT_ROTATIONS[farm])


def demo_path(farm: str):
    return DEMO_DIR / f"demo_{farm}.json"
