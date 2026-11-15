from dataclasses import dataclass

from app.twin.crops import CROPS, FALLOW, cover_crops_of, normalize_crop, sowing_month
from app.twin.engine import DAYS_PER_YEAR, MONTH_STARTS, Planting

LOW_WATER_SWAP = {"maize": "sorghum", "wheat": "oats", "soybean": "beans", "alfalfa": "vetch"}
COLD_CLIMATE_FROST_DAYS = 30.0
COVER_TERMINATION_DAYS = 14

STRATEGY_NAMES = {
    "en": {
        "current": "Current rotation",
        "cover_crop": "Add a legume cover crop",
        "low_water": "Lower-water crop swap",
        "double_crop": "Legume + winter cereal double crop",
        "extra_a": "Sorghum + vetch",
        "extra_b": "Legume + winter rye",
    },
    "es": {
        "current": "Rotación actual",
        "cover_crop": "Añadir cultivo de cobertura leguminoso",
        "low_water": "Cambio a cultivos de menor demanda hídrica",
        "double_crop": "Doble cultivo leguminosa + cereal de invierno",
        "extra_a": "Sorgo + veza",
        "extra_b": "Leguminosa + centeno de invierno",
    },
}


@dataclass(frozen=True)
class StrategyPlan:
    strategy_id: str
    crops: tuple[str, ...]


@dataclass(frozen=True)
class ParsedRotation:
    crops: list[str]
    gaps: list[str]


def parse_rotation(names: list[str]) -> ParsedRotation:
    crops: list[str] = []
    gaps: list[str] = []
    for name in names:
        crop = normalize_crop(name)
        if crop is None:
            gaps.append(f"Unrecognized crop: {name}")
        else:
            crops.append(crop)
    if not crops:
        crops = [FALLOW]
        gaps.append("No recognized crop in the rotation; simulated as fallow")
    return ParsedRotation(crops, gaps)


def build_plan(crops: list[str], years: int, lat: float, shift_days: int = 0, month_shift: int = 0) -> list[Planting]:
    total_days = years * DAYS_PER_YEAR
    plantings: list[Planting] = []
    cursor, index = 0, 0
    while index < 80:
        name = crops[index % len(crops)]
        index += 1
        if name == FALLOW:
            cursor += 180
            if cursor >= total_days:
                break
            continue
        crop = CROPS[name]
        sow_month = (sowing_month(crop, lat) - 1 + month_shift) % 12 + 1
        sow_doy = int(MONTH_STARTS[sow_month - 1]) + 14
        start = (cursor // DAYS_PER_YEAR) * DAYS_PER_YEAR + sow_doy
        if start < cursor:
            start += DAYS_PER_YEAR
        start += shift_days
        if start >= total_days:
            break
        plantings.append(Planting(name, start, start + crop.length, start // DAYS_PER_YEAR))
        cursor = start + crop.length + 5
    covers = cover_crops_of(crops)
    for position, planting in enumerate(plantings):
        if planting.crop not in covers:
            continue
        following = next((p for p in plantings[position + 1 :] if p.crop not in covers), None)
        if following is not None and planting.end > following.start - COVER_TERMINATION_DAYS:
            plantings[position] = Planting(planting.crop, planting.start, max(planting.start + 1, following.start - COVER_TERMINATION_DAYS), planting.year_index)
    return plantings


def month_of_day(day: int) -> int:
    doy = day % DAYS_PER_YEAR
    return int(sum(1 for edge in MONTH_STARTS[1:-1] if doy >= edge)) + 1


def generate_alternatives(current: list[str], frost_days: float = 0.0) -> list[StrategyPlan]:
    cold = frost_days >= COLD_CLIMATE_FROST_DAYS
    legume = "soybean" if cold else "beans"
    winter = "rye" if cold else "oats"
    candidates: list[StrategyPlan] = []
    cover = list(current) + ([legume] if "vetch" in current else ["vetch"])
    candidates.append(StrategyPlan("cover_crop", tuple(cover)))
    swaps = {k: v for k, v in LOW_WATER_SWAP.items() if not (cold and k == "soybean")}
    candidates.append(StrategyPlan("low_water", tuple(swaps.get(c, c) for c in current)))
    candidates.append(StrategyPlan("double_crop", (legume, winter)))
    candidates.append(StrategyPlan("extra_a", ("sorghum", "vetch")))
    candidates.append(StrategyPlan("extra_b", (legume, "rye")))
    chosen: list[StrategyPlan] = []
    seen = {tuple(current)}
    for candidate in candidates:
        if candidate.crops in seen:
            continue
        seen.add(candidate.crops)
        chosen.append(candidate)
        if len(chosen) == 3:
            break
    return chosen
