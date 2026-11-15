import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Crop:
    name: str
    kc_ini: float
    kc_mid: float
    kc_end: float
    stages: tuple[int, int, int, int]
    gdd_base: float
    gdd_maturity: float
    root_depth_m: float
    heat_thr: float
    frost_thr: float
    depletion_p: float
    ky: float
    n_fix: float
    n_removal: float
    residue_cover: float
    om_input: float
    sow_month: int
    price: float
    legume: bool = False
    cover: bool = False
    winter: bool = False
    n_fert: float = 0.0
    cost: float = 0.0

    @property
    def length(self) -> int:
        return sum(self.stages)


CROPS: dict[str, Crop] = {
    "maize": Crop("maize", 0.30, 1.20, 0.60, (20, 35, 40, 30), 10, 1500, 1.0, 35, 1.0, 0.55, 1.25, 0, 110, 0.55, 0.9, 6, 100, n_fert=140, cost=45),
    "sorghum": Crop("sorghum", 0.30, 1.00, 0.55, (20, 35, 40, 30), 10, 1500, 1.1, 38, 1.0, 0.55, 0.9, 0, 85, 0.50, 0.8, 6, 78, n_fert=80, cost=30),
    "wheat": Crop("wheat", 0.40, 1.15, 0.40, (20, 40, 50, 35), 0, 1900, 1.1, 32, -6.0, 0.55, 1.15, 0, 90, 0.45, 0.6, 11, 92, winter=True, n_fert=100, cost=38),
    "beans": Crop("beans", 0.40, 1.15, 0.35, (20, 30, 35, 20), 8, 1300, 0.6, 32, 2.0, 0.45, 1.15, 45, 60, 0.25, 0.4, 6, 140, legume=True, n_fert=20, cost=55),
    "soybean": Crop("soybean", 0.40, 1.15, 0.50, (20, 30, 60, 25), 10, 1700, 0.8, 35, 1.0, 0.50, 0.85, 90, 130, 0.30, 0.4, 6, 120, legume=True, n_fert=0, cost=45),
    "oats": Crop("oats", 0.30, 1.05, 0.25, (20, 40, 45, 30), 0, 1700, 0.9, 30, -6.0, 0.55, 1.0, 0, 55, 0.50, 0.6, 11, 55, winter=True, n_fert=60, cost=22),
    "alfalfa": Crop("alfalfa", 0.40, 1.20, 1.10, (10, 30, 100, 30), 5, 1800, 1.5, 38, -10.0, 0.55, 1.1, 180, 200, 0.40, 1.6, 10, 85, legume=True, winter=True, n_fert=0, cost=35),
    "vetch": Crop("vetch", 0.40, 1.10, 0.40, (20, 35, 50, 25), 3, 1600, 0.8, 30, -8.0, 0.50, 0.8, 90, 30, 0.55, 1.2, 11, 25, legume=True, cover=True, winter=True, n_fert=0, cost=12),
    "rye": Crop("rye", 0.30, 1.05, 0.25, (20, 40, 50, 30), 0, 1700, 1.0, 30, -15.0, 0.55, 0.8, 0, 30, 0.60, 1.0, 11, 25, cover=True, winter=True, n_fert=40, cost=12),
}

FALLOW = "fallow"

ALIASES: dict[str, str] = {
    "maiz": "maize", "corn": "maize", "sorgo": "sorghum", "trigo": "wheat", "frijol": "beans",
    "bean": "beans", "frijoles": "beans", "soya": "soybean", "soja": "soybean", "avena": "oats",
    "oat": "oats", "veza": "vetch", "centeno": "rye", "barbecho": FALLOW, "fallow": FALLOW,
}


def normalize_crop(name: str) -> str | None:
    folded = unicodedata.normalize("NFKD", name.strip().lower())
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    if folded in CROPS or folded == FALLOW:
        return folded
    return ALIASES.get(folded)


def cover_crops_of(crops: list[str]) -> set[str]:
    cash = {c for c in crops if c in CROPS and not CROPS[c].cover}
    return {c for c in crops if c in CROPS and CROPS[c].cover and (CROPS[c].legume or len(cash) >= 2)}


def sowing_month(crop: Crop, lat: float) -> int:
    return crop.sow_month if lat >= 0 else (crop.sow_month + 5) % 12 + 1
