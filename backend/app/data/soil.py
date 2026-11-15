import json
import math
from pathlib import Path

from app.schemas import Soil

DATA_RAW = Path(__file__).resolve().parents[2] / "data_raw"
SOILGRIDS_LAYER_WEIGHTS: dict[str, float] = {"0-5cm": 5.0, "5-15cm": 10.0, "15-30cm": 15.0}
OM_PER_ORGANIC_CARBON = 1.724
EPIC_TO_US_K = 1.0
BARE_CURVE_NUMBER = {"A": 77.0, "B": 86.0, "C": 91.0, "D": 94.0}


def default_soil() -> Soil:
    return Soil(
        source="Default loam assumption (no soil data for this point)",
        texture="loam",
        sand_pct=40.0,
        clay_pct=20.0,
        om_pct=2.5,
        awc_mm_per_m=150.0,
        field_capacity=0.27,
        wilting_point=0.12,
        k_factor=0.30,
        hydrologic_group="B",
        curve_number=BARE_CURVE_NUMBER["B"],
    )


def saxton_rawls(sand_pct: float, clay_pct: float, om_pct: float) -> tuple[float, float]:
    sand, clay, om = sand_pct / 100.0, clay_pct / 100.0, min(max(om_pct, 0.1), 8.0)
    wilting_t = -0.024 * sand + 0.487 * clay + 0.006 * om + 0.005 * sand * om - 0.013 * clay * om + 0.068 * sand * clay + 0.031
    wilting = wilting_t + (0.14 * wilting_t - 0.02)
    field_t = -0.251 * sand + 0.195 * clay + 0.011 * om + 0.006 * sand * om - 0.027 * clay * om + 0.452 * sand * clay + 0.299
    field = field_t + (1.283 * field_t**2 - 0.374 * field_t - 0.015)
    return round(float(field), 3), round(float(wilting), 3)


def texture_class(sand: float, clay: float) -> str:
    silt = 100.0 - sand - clay
    if clay >= 40:
        return "silty clay" if silt >= 40 else ("sandy clay" if sand >= 45 else "clay")
    if clay >= 27:
        if sand <= 20:
            return "silty clay loam"
        if sand <= 45:
            return "clay loam"
        return "sandy clay" if clay >= 35 else "sandy clay loam"
    if clay >= 20 and silt < 28 and sand > 45:
        return "sandy clay loam"
    if silt >= 80 and clay < 12:
        return "silt"
    if silt >= 50:
        return "silt loam"
    if clay < 20 and sand >= 85:
        return "sand"
    if clay < 20 and sand >= 70:
        return "loamy sand"
    if sand > 52:
        return "sandy loam"
    return "loam"


def group_from_texture(sand: float, clay: float) -> str:
    if clay >= 40:
        return "D"
    if clay >= 27:
        return "C"
    if sand >= 50 and clay < 20:
        return "A"
    return "B"


def k_factor_us(sand: float, silt: float, clay: float, om_pct: float) -> float:
    carbon = om_pct / OM_PER_ORGANIC_CARBON
    sn1 = 1.0 - sand / 100.0
    factor_coarse = 0.2 + 0.3 * math.exp(-0.0256 * sand * (1.0 - silt / 100.0))
    factor_ratio = (silt / max(clay + silt, 1e-6)) ** 0.3
    factor_carbon = 1.0 - 0.25 * carbon / (carbon + math.exp(3.72 - 2.95 * carbon))
    factor_sand = 1.0 - 0.7 * sn1 / (sn1 + math.exp(-5.51 + 22.9 * sn1))
    return round(float(min(max(factor_coarse * factor_ratio * factor_carbon * factor_sand * EPIC_TO_US_K, 0.05), 0.5)), 3)


def soilgrids_profile(raw: dict) -> dict[str, float] | None:
    values: dict[str, float] = {}
    for layer in raw["properties"]["layers"]:
        factor = layer["unit_measure"]["d_factor"]
        total, weight = 0.0, 0.0
        for depth in layer["depths"]:
            mean = depth["values"]["mean"]
            w = SOILGRIDS_LAYER_WEIGHTS.get(depth["label"])
            if mean is None or w is None:
                continue
            total += w * mean / factor
            weight += w
        if weight > 0:
            values[layer["name"]] = total / weight
    if not all(k in values for k in ("sand", "clay", "silt", "soc")):
        return None
    return {
        "sand": values["sand"],
        "clay": values["clay"],
        "silt": values["silt"],
        "om": values["soc"] / 10.0 * OM_PER_ORGANIC_CARBON,
    }


def soil_from_soilgrids(raw: dict, note: str | None = None) -> Soil | None:
    profile = soilgrids_profile(raw)
    if profile is None:
        return None
    field, wilting = saxton_rawls(profile["sand"], profile["clay"], profile["om"])
    group = group_from_texture(profile["sand"], profile["clay"])
    notes = ["SoilGrids 0-30 cm depth-weighted sand/silt/clay and organic carbon; AWC from Saxton-Rawls pedotransfer"]
    if note:
        notes.append(note)
    return Soil(
        source="ISRIC SoilGrids v2.0 + Saxton-Rawls pedotransfer",
        texture=texture_class(profile["sand"], profile["clay"]),
        sand_pct=round(profile["sand"], 1),
        clay_pct=round(profile["clay"], 1),
        om_pct=round(profile["om"], 2),
        awc_mm_per_m=round((field - wilting) * 1000.0, 1),
        field_capacity=field,
        wilting_point=wilting,
        k_factor=k_factor_us(profile["sand"], profile["silt"], profile["clay"], profile["om"]),
        hydrologic_group=group,
        curve_number=BARE_CURVE_NUMBER[group],
        notes=notes,
    )


def _weighted(rows: list[dict], key: str) -> float | None:
    pairs = [(float(r[key]), float(r["comppct_r"])) for r in rows if r.get(key) not in (None, "")]
    total = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / total if total > 0 else None


def ssurgo_rows(raw: dict) -> list[dict]:
    table = raw["result"]["Table"]
    return [dict(zip(table[0], row)) for row in table[1:]]


def ssurgo_slope_deg(raw: dict) -> float | None:
    percent = _weighted(ssurgo_rows(raw), "slope_r")
    return None if percent is None else round(math.degrees(math.atan(percent / 100.0)), 2)


def soil_from_ssurgo(raw: dict, cross_check: Soil | None = None) -> Soil | None:
    rows = ssurgo_rows(raw)
    awc = _weighted(rows, "awc_r")
    sand = _weighted(rows, "sandtotal_r")
    clay = _weighted(rows, "claytotal_r")
    om = _weighted(rows, "om_r")
    k_factor = _weighted(rows, "kwfact")
    if awc is None or sand is None or clay is None or om is None:
        return None
    groups = [(r["hydgrp"][0], float(r["comppct_r"])) for r in rows if r.get("hydgrp")]
    weights: dict[str, float] = {}
    for group, pct in groups:
        weights[group] = weights.get(group, 0.0) + pct
    group = max(weights, key=lambda g: weights[g])
    curve = sum(BARE_CURVE_NUMBER[g] * w for g, w in weights.items()) / sum(weights.values())
    _, wilting = saxton_rawls(sand, clay, om)
    awc_mm = awc * 1000.0
    notes = [
        f"SSURGO map unit {rows[0]['muname']}: area-weighted top-horizon components ({', '.join(sorted({r['compname'] for r in rows}))})",
        "Wilting point from Saxton-Rawls pedotransfer on SSURGO sand, clay and organic matter",
    ]
    if cross_check is not None:
        notes.append(
            f"SoilGrids cross-check: {cross_check.texture} (sand {cross_check.sand_pct:.0f}%, clay {cross_check.clay_pct:.0f}%), "
            f"pedotransfer AWC {cross_check.awc_mm_per_m:.0f} mm/m vs SSURGO {awc_mm:.0f} mm/m"
        )
    return Soil(
        source="USDA NRCS SSURGO (Soil Data Access)",
        texture=texture_class(sand, clay),
        sand_pct=round(sand, 1),
        clay_pct=round(clay, 1),
        om_pct=round(om, 2),
        awc_mm_per_m=round(awc_mm, 1),
        field_capacity=round(wilting + awc, 3),
        wilting_point=wilting,
        k_factor=round(k_factor if k_factor is not None else k_factor_us(sand, 100 - sand - clay, clay, om), 3),
        hydrologic_group=group,
        curve_number=round(curve, 1),
        notes=notes,
    )


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_farm_soil(farm: str) -> tuple[Soil, float | None]:
    folder = DATA_RAW / farm
    grids = _read(folder / "soilgrids.json")
    grid_soil = soil_from_soilgrids(grids) if grids else None
    nearby_soil = None
    if grid_soil is None:
        nearby = _read(folder / "soilgrids_nearby.json")
        if nearby:
            lon, lat = nearby["geometry"]["coordinates"][:2]
            nearby_soil = soil_from_soilgrids(
                nearby, f"SoilGrids returned no data at the farm cell; nearest valid cell ({lat:.2f}, {lon:.2f}) used"
            )
    ssurgo = _read(folder / "ssurgo.json")
    if ssurgo:
        soil = soil_from_ssurgo(ssurgo, grid_soil)
        if soil is not None:
            return soil, ssurgo_slope_deg(ssurgo)
    return (grid_soil or nearby_soil or default_soil()), None
