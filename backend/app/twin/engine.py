from dataclasses import dataclass

import numpy as np

from app.schemas import Soil
from app.twin.crops import CROPS, Crop

DAYS_PER_YEAR = 365
LAYER1_DEPTH_M = 0.3
LAYER2_DEPTH_M = 0.9
BARE_KC = 0.35
BARE_CANOPY = 0.15
EROSION_R_COEF = 0.075
MONTH_STARTS = np.array([0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365])
MONTH_OF_DOY = np.searchsorted(MONTH_STARTS, np.arange(DAYS_PER_YEAR), side="right") - 1


@dataclass(frozen=True)
class Planting:
    crop: str
    start: int
    end: int
    year_index: int


@dataclass
class Timeline:
    pid: np.ndarray
    kc: np.ndarray
    canopy: np.ndarray
    root_depth: np.ndarray
    depletion_p: np.ndarray
    heat_thr: np.ndarray
    frost_thr: np.ndarray
    residue: np.ndarray
    active: np.ndarray


@dataclass
class SampleWeather:
    tmax: np.ndarray
    tmin: np.ndarray
    precip: np.ndarray
    et0: np.ndarray
    warming: np.ndarray
    srad: np.ndarray | None = None
    rh: np.ndarray | None = None
    ws: np.ndarray | None = None
    lat: float = 0.0
    elevation: float = 0.0

    def et0_for(self, tmax: np.ndarray, tmin: np.ndarray) -> np.ndarray:
        return reference_et0(tmax, tmin, self.lat, self.srad, self.rh, self.ws, self.elevation)


@dataclass
class SimResult:
    eta: np.ndarray
    etc: np.ndarray
    transp: np.ndarray
    transp_pot: np.ndarray
    ks: np.ndarray
    runoff: np.ndarray
    drainage: np.ndarray
    moisture: np.ndarray
    erosion: np.ndarray
    balance_residual: float


def extraterrestrial_radiation(lat: float) -> np.ndarray:
    doy = np.arange(1, DAYS_PER_YEAR + 1)
    phi = np.radians(lat)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    ra = (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))
    return ra * 0.408


def hargreaves_et0(tmax: np.ndarray, tmin: np.ndarray, lat: float) -> np.ndarray:
    years = tmax.shape[0] // DAYS_PER_YEAR
    ra = np.tile(extraterrestrial_radiation(lat), years)[:, None]
    tmean = (tmax + tmin) / 2
    return np.maximum(0.0023 * ra * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0.1)), 0.0)


def saturation_vapour_pressure(temperature: np.ndarray) -> np.ndarray:
    return 0.6108 * np.exp(17.27 * temperature / (temperature + 237.3))


def penman_monteith_et0(
    tmax: np.ndarray,
    tmin: np.ndarray,
    lat: float,
    srad: np.ndarray,
    rh: np.ndarray,
    ws: np.ndarray,
    elevation: float,
) -> np.ndarray:
    years = tmax.shape[0] // DAYS_PER_YEAR
    ra = np.tile(extraterrestrial_radiation(lat) / 0.408, years)[:, None]
    tmean = (tmax + tmin) / 2
    pressure = 101.3 * ((293.0 - 0.0065 * elevation) / 293.0) ** 5.26
    gamma = 0.000665 * pressure
    es = (saturation_vapour_pressure(tmax) + saturation_vapour_pressure(tmin)) / 2
    ea = np.clip(rh, 5.0, 100.0) / 100.0 * es
    delta = 4098.0 * saturation_vapour_pressure(tmean) / (tmean + 237.3) ** 2
    rso = np.maximum((0.75 + 2e-5 * elevation) * ra, 1e-3)
    ratio = np.clip(srad / rso, 0.3, 1.0)
    rns = 0.77 * srad
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * ratio - 0.35)
    net = rns - rnl
    wind = np.maximum(ws, 0.2)
    et0 = (0.408 * delta * net + gamma * 900.0 / (tmean + 273.0) * wind * (es - ea)) / (delta + gamma * (1.0 + 0.34 * wind))
    return np.maximum(et0, 0.0)


def reference_et0(
    tmax: np.ndarray,
    tmin: np.ndarray,
    lat: float,
    srad: np.ndarray | None = None,
    rh: np.ndarray | None = None,
    ws: np.ndarray | None = None,
    elevation: float = 0.0,
) -> np.ndarray:
    if srad is not None and rh is not None and ws is not None:
        return penman_monteith_et0(tmax, tmin, lat, srad, rh, ws, elevation)
    return hargreaves_et0(tmax, tmin, lat)


def build_timeline(plantings: list[Planting], total_days: int) -> Timeline:
    pid = np.full(total_days, -1, dtype=int)
    kc = np.full(total_days, BARE_KC)
    canopy = np.zeros(total_days)
    root = np.full(total_days, 0.3)
    dep_p = np.full(total_days, 0.5)
    heat = np.full(total_days, np.inf)
    frost = np.full(total_days, -np.inf)
    residue = np.zeros(total_days)
    for index, planting in enumerate(plantings):
        crop = CROPS[planting.crop]
        ini, dev, mid, late = crop.stages
        for offset in range(min(crop.length, planting.end - planting.start)):
            day = planting.start + offset
            if day < 0 or day >= total_days:
                continue
            if offset < ini:
                k, c = crop.kc_ini, 0.05
            elif offset < ini + dev:
                f = (offset - ini) / dev
                k, c = crop.kc_ini + f * (crop.kc_mid - crop.kc_ini), 0.05 + 0.95 * f * f * (3 - 2 * f)
            elif offset < ini + dev + mid:
                k, c = crop.kc_mid, 1.0
            else:
                f = (offset - ini - dev - mid) / late
                k, c = crop.kc_mid + f * (crop.kc_end - crop.kc_mid), 1.0 - 0.7 * f
            growth = min(1.0, offset / (ini + dev))
            pid[day], kc[day], canopy[day] = index, k, c
            root[day] = 0.25 + (crop.root_depth_m - 0.25) * growth
            dep_p[day], heat[day], frost[day] = crop.depletion_p, crop.heat_thr, crop.frost_thr
    boundaries = {min(p.end, total_days): CROPS[p.crop].residue_cover for p in plantings}
    cover = 0.3
    for day in range(total_days):
        if day in boundaries:
            cover = max(cover * 0.5, boundaries[day])
        residue[day] = cover
        cover *= 0.993
    return Timeline(pid, kc, canopy, root, dep_p, heat, frost, residue, pid >= 0)


def slope_ls_factor(slope_deg: float) -> float:
    s = np.tan(np.radians(max(slope_deg, 0.1))) * 100
    return float(0.065 + 0.045 * s + 0.0065 * s * s)


def simulate(
    weather: SampleWeather,
    timeline: Timeline,
    initial_relative_moisture: float,
    slope_deg: float,
    soil: Soil,
    irrigation_mm_per_year: float = 0.0,
) -> SimResult:
    total_days, samples = weather.precip.shape
    shape = (total_days, samples)
    eta, etc, transp, transp_pot = (np.zeros(shape) for _ in range(4))
    ks_out = np.ones(shape)
    runoff_out, drain_out, moist_out, erosion_out = (np.zeros(shape) for _ in range(4))
    layer1_mm = soil.awc_mm_per_m * LAYER1_DEPTH_M
    layer2_mm = soil.awc_mm_per_m * LAYER2_DEPTH_M
    k_factor = soil.k_factor
    s1 = np.full(samples, initial_relative_moisture * layer1_mm)
    s2 = np.full(samples, initial_relative_moisture * layer2_mm)
    ls = slope_ls_factor(slope_deg)
    active_days = np.maximum(timeline.active.reshape(-1, DAYS_PER_YEAR).sum(axis=1), 1)
    irrigation_daily = np.where(
        timeline.active,
        irrigation_mm_per_year / np.repeat(active_days, DAYS_PER_YEAR)[:total_days],
        0.0,
    )
    worst = 0.0
    for t in range(total_days):
        rain = weather.precip[t]
        irr = irrigation_daily[t]
        c = timeline.canopy[t]
        res = timeline.residue[t]
        cn = np.clip(soil.curve_number - 12.0 * c - 5.0 * res, 30.0, 98.0)
        retention = 25400.0 / cn - 254.0
        ia = 0.2 * retention
        runoff = np.where(rain > ia, (rain - ia) ** 2 / (rain + 0.8 * retention), 0.0)
        before = s1 + s2
        s1 = s1 + rain - runoff + irr
        over1 = np.maximum(s1 - layer1_mm, 0.0)
        s1 = s1 - over1
        s2 = s2 + over1
        drain = np.maximum(s2 - layer2_mm, 0.0)
        s2 = s2 - drain
        et_crop = timeline.kc[t] * weather.et0[t]
        evap_pot = (1.0 - c) * et_crop * (1.0 - 0.5 * res)
        evap = np.minimum(evap_pot * np.clip(s1 / (0.4 * layer1_mm), 0.0, 1.0), s1)
        s1 = s1 - evap
        deep = float(np.clip((timeline.root_depth[t] - 0.3) / 0.9, 0.0, 1.0))
        root_water = s1 + deep * s2
        root_capacity = layer1_mm + deep * layer2_mm
        tp = c * et_crop
        if c > 0:
            ks = np.clip(root_water / root_capacity / (1.0 - timeline.depletion_p[t]), 0.0, 1.0)
        else:
            ks = np.ones(samples)
        ta = np.minimum(tp * ks, root_water)
        share = np.where(root_water > 1e-9, s1 / np.maximum(root_water, 1e-9), 1.0)
        s1 = s1 - ta * share
        s2 = s2 - ta * (1.0 - share)
        residual = rain + irr - runoff - evap - ta - drain - (s1 + s2 - before)
        worst = max(worst, float(np.abs(residual).max()))
        eta[t], etc[t], transp[t], transp_pot[t] = evap + ta, et_crop, ta, tp
        ks_out[t], runoff_out[t], drain_out[t] = ks, runoff, drain
        moist_out[t] = (s1 + s2) / (layer1_mm + layer2_mm)
        cover_factor = float(np.clip(np.exp(-3.0 * c) * (1.0 - 0.7 * res), 0.001, 1.0))
        erosion_out[t] = EROSION_R_COEF * np.where(rain >= 5.0, rain ** 1.7, 0.0) * k_factor * ls * cover_factor
    return SimResult(eta, etc, transp, transp_pot, ks_out, runoff_out, drain_out, moist_out, erosion_out, worst)


def planting_yields(
    plantings: list[Planting],
    result: SimResult,
    weather: SampleWeather,
    total_days: int,
) -> list[tuple[int, np.ndarray]]:
    outputs: list[tuple[int, np.ndarray]] = []
    for index, planting in enumerate(plantings):
        crop: Crop = CROPS[planting.crop]
        a, b = max(planting.start, 0), planting.end
        if b > total_days:
            continue
        ta = result.transp[a:b].sum(axis=0)
        tp = np.maximum(result.transp_pot[a:b].sum(axis=0), 1e-6)
        heat_days = (weather.tmax[a:b] > crop.heat_thr).sum(axis=0)
        frost_days = (weather.tmin[a:b] < crop.frost_thr).sum(axis=0)
        daily_gdd = np.clip((np.minimum(weather.tmax[a:b], 30.0) + np.maximum(weather.tmin[a:b], crop.gdd_base)) / 2 - crop.gdd_base, 0.0, None)
        ratio = daily_gdd.sum(axis=0) / crop.gdd_maturity
        water_term = 1.0 - crop.ky * (1.0 - np.minimum(ta / tp, 1.0))
        heat_term = 1.0 - np.minimum(0.02 * heat_days, 0.5)
        frost_term = 1.0 - np.minimum(0.08 * frost_days, 0.8)
        gdd_term = np.minimum(1.0, ratio) ** 0.7 * (1.0 - 0.5 * np.maximum(ratio - 1.2, 0.0))
        relative = np.clip(water_term * heat_term * frost_term * gdd_term, 0.0, 1.0)
        outputs.append((index, relative))
    return outputs
