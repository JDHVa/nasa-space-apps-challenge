from dataclasses import dataclass, field

import numpy as np

from app.data.soil import default_soil
from app.data.site import HistoricWeather
from app.schemas import Soil
from app.twin.crops import CROPS, cover_crops_of
from app.twin.engine import (
    BARE_CANOPY,
    DAYS_PER_YEAR,
    MONTH_OF_DOY,
    MONTH_STARTS,
    SampleWeather,
    SimResult,
    build_timeline,
    planting_yields,
    simulate,
)
from app.twin.rotations import COLD_CLIMATE_FROST_DAYS, build_plan

METRIC_UNITS: dict[str, str] = {
    "water_use_mm": "mm/yr",
    "irrigation_need_mm": "mm/yr",
    "yield_index": "%",
    "n_balance_kg_ha": "kg/ha/yr",
    "erosion_t_ha": "t/ha/yr",
    "soil_om_index": "idx",
    "income_index": "idx",
    "water_stress_days": "days/yr",
    "bare_soil_days": "days/yr",
}

IRRIGATION_EFFICIENCY = 0.7
LEACHING_FRACTION = 0.08
SEVERE_STRESS_FRACTION = 0.35
STRESS_SPAN_DAYS = 60.0
IRRIGATION_SPAN_MM = 200.0
RISK_PENALTY_POINTS = 75.0
RISK_WEIGHT_FLOOR = 0.4

HIGHER_IS_BETTER = {"yield_index", "n_balance_kg_ha", "soil_om_index", "income_index"}
PRIORITY_METRICS: dict[str, list[str]] = {
    "water": ["water_use_mm", "irrigation_need_mm"],
    "nitrogen": ["n_balance_kg_ha"],
    "erosion": ["erosion_t_ha", "bare_soil_days"],
    "organic_matter": ["soil_om_index"],
    "income": ["income_index"],
}


@dataclass
class StrategyRun:
    crops: list[str]
    plantings: list
    metrics: dict[str, np.ndarray]
    bare_calendar: list[float]
    vulnerability: list[dict]
    canopy_monthly: list[float]
    moisture_monthly: list[float]
    daily_sample: list[dict]
    balance_residual: float


@dataclass
class SiteParams:
    lat: float
    slope_deg: float
    sm_rootzone: float
    soil: Soil = field(default_factory=default_soil)
    frost_days: float = 0.0


def build_samples(
    hist: HistoricWeather, lat: float, years: int, n_samples: int = 40, seed: int = 7, elevation: float = 0.0
) -> SampleWeather:
    rng = np.random.default_rng(seed)
    hist_years = hist.tmax.shape[0]
    idx = rng.integers(0, hist_years, size=(n_samples, years))
    tail = np.arange(hist_years - years, hist_years) if years <= hist_years else np.arange(years) % hist_years
    idx[0] = tail
    n_base = int(round(n_samples * 0.6))
    n_mid = (n_samples - n_base) // 2
    warming = np.zeros(n_samples)
    warming[n_base : n_base + n_mid] = 1.5
    warming[n_base + n_mid :] = 2.5

    def gather(array: np.ndarray) -> np.ndarray:
        return array[idx].reshape(n_samples, years * DAYS_PER_YEAR).T

    tmax = gather(hist.tmax) + warming[None, :]
    tmin = gather(hist.tmin) + warming[None, :]
    precip = gather(hist.precip) * (1.0 - 0.02 * warming[None, :])
    has_pm = hist.rh is not None and hist.ws is not None
    srad = gather(hist.srad) if has_pm else None
    rh = gather(hist.rh) if has_pm else None
    ws = gather(hist.ws) if has_pm else None
    samples = SampleWeather(tmax, tmin, precip, np.zeros_like(tmax), warming, srad, rh, ws, lat, elevation)
    samples.et0 = samples.et0_for(tmax, tmin)
    return samples


def _monthly_cells(daily: np.ndarray, years: int) -> np.ndarray:
    cube = daily.reshape(years, DAYS_PER_YEAR, -1).astype(float)
    return np.add.reduceat(cube, MONTH_STARTS[:-1], axis=1)


def _vulnerability(
    timeline,
    weather: SampleWeather,
    result: SimResult,
    years: int,
) -> list[dict]:
    active = timeline.active[:, None]
    flags = {
        "heat": (weather.tmax > timeline.heat_thr[:, None], 3),
        "frost": (weather.tmin < timeline.frost_thr[:, None], 1),
        "drought": ((result.ks < 0.7) & active, 7),
        "waterlogging": ((result.drainage > 20.0) & active, 2),
    }
    found: list[dict] = []
    for kind, (mask, minimum) in flags.items():
        cells = _monthly_cells(mask, years)
        probability = (cells >= minimum).mean(axis=(0, 2))
        for month in range(12):
            if probability[month] >= 0.15:
                found.append({"month": month + 1, "type": kind, "severity": round(float(probability[month]), 2)})
    monthly_erosion = _monthly_cells(result.erosion, years).mean(axis=(0, 2))
    for month in range(12):
        severity = min(1.0, float(monthly_erosion[month]) / 0.3)
        if monthly_erosion[month] >= 0.01:
            found.append(
                {"month": month + 1, "type": "erosion", "severity": round(severity, 2), "soil_loss_t_ha": round(float(monthly_erosion[month]), 3)}
            )
    return sorted(found, key=lambda v: (v["month"], v["type"]))


def run_strategy(
    crops: list[str],
    samples: SampleWeather,
    site: SiteParams,
    years: int,
    irrigation_mm: float = 0.0,
    sowing_shift_days: int = 0,
) -> StrategyRun:
    total_days = years * DAYS_PER_YEAR
    month_shift = -1 if site.frost_days >= COLD_CLIMATE_FROST_DAYS else 0
    plantings = build_plan(crops, years, site.lat, sowing_shift_days, month_shift)
    timeline = build_timeline(plantings, total_days)
    soil = site.soil
    initial = float(np.clip((site.sm_rootzone - soil.wilting_point) / max(soil.field_capacity - soil.wilting_point, 1e-6), 0.05, 1.0))
    result = simulate(samples, timeline, initial, site.slope_deg, soil, irrigation_mm)
    n_samples = samples.precip.shape[1]
    yields = planting_yields(plantings, result, samples, total_days)
    income = np.zeros(n_samples)
    fertilizer = 0.0
    fixation = np.zeros(n_samples)
    removal = np.zeros(n_samples)
    om_input = np.zeros(n_samples)
    relatives = []
    covers = cover_crops_of(crops)
    for index, relative in yields:
        planting = plantings[index]
        crop = CROPS[planting.crop]
        if planting.crop not in covers:
            relatives.append(relative)
        contribution = crop.price * relative - crop.cost
        if irrigation_mm <= 0 and crop.winter:
            window = slice(max(planting.start, 0), planting.end)
            stressed = ((result.ks[window] < 0.7).sum(axis=0) / max(planting.end - max(planting.start, 0), 1)) > SEVERE_STRESS_FRACTION
            contribution = np.where(stressed, -crop.cost, contribution)
        income += contribution
        fertilizer += crop.n_fert
        fixation += crop.n_fix * relative
        removal += crop.n_removal * relative
        om_input += crop.om_input * (0.5 + 0.5 * relative)
    bare = timeline.canopy < BARE_CANOPY
    bare_days = np.full(n_samples, bare.sum() / years)
    erosion_total = result.erosion.sum(axis=0)
    metrics = {
        "water_use_mm": result.eta.sum(axis=0) / years,
        "irrigation_need_mm": (result.transp_pot - result.transp).sum(axis=0) / years / IRRIGATION_EFFICIENCY,
        "yield_index": (np.mean(relatives, axis=0) * 100) if relatives else np.zeros(n_samples),
        "n_balance_kg_ha": (fixation + fertilizer - removal - LEACHING_FRACTION * result.drainage.sum(axis=0)) / years,
        "erosion_t_ha": erosion_total / years,
        "soil_om_index": 100.0 + om_input - 1.5 * years - 0.004 * bare.sum() - 0.5 * erosion_total,
        "income_index": income / years,
        "water_stress_days": ((result.ks < 0.7) & timeline.active[:, None]).sum(axis=0) / years,
        "bare_soil_days": bare_days,
    }
    bare_cube = bare.reshape(years, DAYS_PER_YEAR)
    canopy_cube = timeline.canopy.reshape(years, DAYS_PER_YEAR)
    month_len = np.diff(MONTH_STARTS)
    bare_calendar = [round(float(v), 3) for v in np.add.reduceat(bare_cube.mean(axis=0), MONTH_STARTS[:-1]) / month_len]
    canopy_monthly = [round(float(v), 3) for v in np.add.reduceat(canopy_cube.mean(axis=0), MONTH_STARTS[:-1]) / month_len]
    baseline = samples.warming == 0
    if not baseline.any():
        baseline = np.ones_like(baseline)
    moisture_cube = result.moisture[:, baseline].mean(axis=1).reshape(years, DAYS_PER_YEAR).mean(axis=0)
    moisture_monthly = [round(float(v), 3) for v in np.add.reduceat(moisture_cube, MONTH_STARTS[:-1]) / month_len]
    daily_sample = []
    for t in range(0, total_days, 7):
        window = slice(t, min(t + 7, total_days))
        pid = int(timeline.pid[t])
        daily_sample.append(
            {
                "day": t,
                "crop": plantings[pid].crop if pid >= 0 else None,
                "canopy": round(float(timeline.canopy[t]), 3),
                "soil_moisture": round(float(result.moisture[t, 0]), 3),
                "rain_mm": round(float(samples.precip[window, 0].mean()), 2),
                "et_mm": round(float(result.eta[window, 0].mean()), 2),
            }
        )
    return StrategyRun(
        crops, plantings, metrics, bare_calendar, _vulnerability(timeline, samples, result, years),
        canopy_monthly, moisture_monthly, daily_sample, result.balance_residual,
    )


def bands(run_metrics: dict[str, np.ndarray]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for key, values in run_metrics.items():
        p10, p50, p90 = np.percentile(values, [10, 50, 90])
        out[key] = {"p10": round(float(p10), 2), "p50": round(float(p50), 2), "p90": round(float(p90), 2), "unit": METRIC_UNITS[key]}
    return out


def score_strategies(all_bands: list[dict[str, dict]], priorities: dict[str, float]) -> list[float]:
    weights = {k: max(float(v), 0.0) for k, v in priorities.items()}
    if sum(weights.values()) <= 0:
        weights = {k: 1.0 for k in weights}
    metric_weights: dict[str, float] = {"yield_index": 0.5}
    for priority, metric_keys in PRIORITY_METRICS.items():
        for key in metric_keys:
            metric_weights[key] = metric_weights.get(key, 0.0) + weights.get(priority, 0.0) / len(metric_keys)
    total = sum(metric_weights.values())
    scores = np.zeros(len(all_bands))
    for key, weight in metric_weights.items():
        values = np.array([b[key]["p50"] for b in all_bands])
        span = values.max() - values.min()
        norm = np.full(len(values), 0.5) if span < 1e-9 else (values - values.min()) / span
        if key not in HIGHER_IS_BETTER:
            norm = 1.0 - norm
        scores += weight * norm
    scores = scores / total * 100
    if len(all_bands) > 1:
        water_weight = max(min(weights.get("water", 0.0), 1.0), RISK_WEIGHT_FLOOR)
        baseline = all_bands[0]
        for i, band in enumerate(all_bands):
            stress_excess = max(band["water_stress_days"]["p50"] - baseline["water_stress_days"]["p50"], 0.0)
            irrigation_excess = max(band["irrigation_need_mm"]["p50"] - baseline["irrigation_need_mm"]["p50"], 0.0)
            risk = 0.5 * min(stress_excess / STRESS_SPAN_DAYS, 1.0) + 0.5 * min(irrigation_excess / IRRIGATION_SPAN_MM, 1.0)
            scores[i] -= RISK_PENALTY_POINTS * water_weight * risk
    return [round(float(s), 1) for s in scores]
