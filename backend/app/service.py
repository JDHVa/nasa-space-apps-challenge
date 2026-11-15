import json
from datetime import datetime, timezone

import numpy as np

from app.ai.emulator import METRIC_KEYS, get_emulator
from app.data.farms import (
    DEFAULT_FARM,
    cdl_summary,
    default_rotation,
    demo_path,
    farm_for,
    load_farm_site,
    nearest_farm,
    observed_soil_moisture,
)
from app.data.site import HistoricWeather, SiteData, load_site
from app.data.soil import default_soil
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Band,
    Priorities,
    Season,
    Site,
    SourceRef,
    Strategy,
    Validation,
    WhatIfRequest,
    WhatIfResponse,
)
from app.twin.crops import normalize_crop
from app.twin.engine import reference_et0
from app.twin.ensemble import METRIC_UNITS, SiteParams, bands, build_samples, run_strategy, score_strategies
from app.twin.narrative import LIVE_UNAVAILABLE_GAP, cdl_text, describe_strategy, validation_evidence
from app.twin.rotations import STRATEGY_NAMES, generate_alternatives, month_of_day, parse_rotation

DEMO_PRIORITIES = Priorities(water=0.8, nitrogen=0.6, erosion=0.7, organic_matter=0.6, income=0.5)
ENSEMBLE_SIZE = 40

_REGISTRY: dict[tuple[str, str], list[str]] = {}


def site_key(lat: float, lon: float) -> str:
    return f"{lat:.2f}_{lon:.2f}"


def cycle_of(crops: list[str]) -> list[str]:
    for period in range(1, len(crops) + 1):
        if all(crops[i] == crops[i % period] for i in range(len(crops))):
            return crops[:period]
    return crops


def crops_of_seasons(seasons: list[Season]) -> list[str]:
    ordered = sorted(seasons, key=lambda s: (s.year_index, s.start_month))
    return cycle_of([s.crop for s in ordered])


def register(key: str, strategies: list[Strategy]) -> None:
    for strategy in strategies:
        _REGISTRY[(key, strategy.id)] = crops_of_seasons(strategy.rotation)


def _flat(array: np.ndarray | None) -> np.ndarray | None:
    return None if array is None else array.reshape(-1, 1)


def climate_summary(weather: HistoricWeather, lat: float, elevation: float = 0.0) -> dict[str, float]:
    years = weather.tmax.shape[0]
    et0 = reference_et0(
        weather.tmax.reshape(-1, 1), weather.tmin.reshape(-1, 1), lat, _flat(weather.srad), _flat(weather.rh), _flat(weather.ws), elevation
    )
    return {
        "tmax_mean": round(float(weather.tmax.mean()), 1),
        "tmin_mean": round(float(weather.tmin.mean()), 1),
        "precip_annual_mm": round(float(weather.precip.sum() / years), 1),
        "et0_annual_mm": round(float(et0.sum() / years), 1),
        "frost_days": round(float((weather.tmin < 0).sum() / years), 1),
        "heat_days": round(float((weather.tmax >= 35).sum() / years), 1),
    }


def build_site(data: SiteData) -> Site:
    gee = data.gee
    return Site(
        lat=data.lat,
        lon=data.lon,
        elevation_m=gee.elevation_m,
        slope_deg=gee.slope_deg,
        sm_surface=gee.sm_surface,
        sm_rootzone=gee.sm_rootzone,
        gpm_annual_mm=gee.gpm_annual_mm if data.satellite_available else None,
        grace_lwe_cm=gee.grace_lwe_cm if data.satellite_available else None,
        climate=climate_summary(data.weather, data.lat, gee.elevation_m),
        data_mode=data.data_mode,
        soil=data.soil,
        satellite_available=data.satellite_available,
    )


def seasons_of(plantings: list) -> list[Season]:
    return [
        Season(
            crop=p.crop,
            year_index=p.year_index,
            start_month=month_of_day(p.start),
            end_month=month_of_day(p.end - 1),
        )
        for p in plantings
    ]


def sources_for(data: SiteData, farm: str | None, et0_method: str) -> list[SourceRef]:
    et0_text = (
        "ET0 by FAO-56 Penman-Monteith (RH2M, WS2M, ALLSKY), Hargreaves fallback"
        if et0_method == "penman_monteith"
        else "ET0 by Hargreaves (humidity, wind or radiation unavailable)"
    )
    sources = [
        SourceRef(name="NASA POWER", dataset="POWER Daily API (AG community)", use=f"30-year daily weather: Tmax, Tmin, rain, radiation, humidity, wind; {et0_text}"),
    ]
    if data.satellite_available:
        sources += [
            SourceRef(name="NASA SMAP", dataset="NASA/SMAP/SPL4SMGP/008", use="Initial surface and root-zone soil moisture"),
            SourceRef(name="NASA GPM IMERG", dataset="NASA/GPM_L3/IMERG_V07", use="Satellite rainfall cross-check"),
            SourceRef(name="MODIS NDVI", dataset="MODIS/061/MOD13Q1", use="Observed greenness vs twin canopy validation and bare-soil windows"),
            SourceRef(name="SRTM", dataset="USGS/SRTMGL1_003", use="Elevation and slope for erosion"),
            SourceRef(name="NASA GRACE", dataset="NASA/GRACE/MASS_GRIDS_V04/LAND", use="Regional terrestrial water storage anomaly"),
        ]
    if farm is not None:
        extra = "" if data.satellite_available else "; initial soil water and elevation"
        sources.append(
            SourceRef(
                name="NASA POWER soil wetness",
                dataset="POWER Climatology GWETROOT/GWETTOP (MERRA-2)",
                use="Observed root-zone wetness climatology to validate twin soil moisture" + extra,
            )
        )
    soil_source = data.soil.source
    if "SSURGO" in soil_source:
        sources.append(
            SourceRef(
                name="USDA NRCS SSURGO",
                dataset="Soil Data Access tabular API (component/chorizon)",
                use="Available water capacity, texture, organic matter, K factor, hydrologic group (curve number) and slope",
            )
        )
    if "SoilGrids" in soil_source or any("SoilGrids" in note for note in data.soil.notes):
        suffix = " (cross-check)" if "SSURGO" in soil_source else ""
        sources.append(
            SourceRef(
                name="ISRIC SoilGrids",
                dataset="SoilGrids v2.0 point query, 0-30 cm",
                use="Sand, silt, clay, organic carbon with Saxton-Rawls pedotransfer for available water capacity" + suffix,
            )
        )
    if farm is not None and cdl_summary(farm) is not None:
        sources.append(
            SourceRef(name="USDA NASS CDL", dataset="CropScape GetCDLValue 2008-2024 (300 m grid)", use="Cropping history used to set the default current rotation")
        )
    return sources


def pearson(a: list[float], b: list[float]) -> float | None:
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(x) != len(y) or len(x) < 3 or x.std() < 1e-9 or y.std() < 1e-9:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def build_validation(farm: str | None, ndvi: list[float], canopy: list[float], moisture_twin: list[float]) -> Validation:
    fit: dict[str, float] = {}
    observed_moisture: list[float] | None = None
    if farm is not None:
        observed_moisture = observed_soil_moisture(farm)
        r = pearson(moisture_twin, observed_moisture)
        if r is not None:
            fit["soil_moisture_r"] = round(r, 2)
            fit["soil_moisture_mae"] = round(float(np.abs(np.array(moisture_twin) - np.array(observed_moisture)).mean()), 3)
    if ndvi:
        r = pearson(canopy, ndvi)
        if r is not None:
            fit["canopy_r"] = round(r, 2)
            fit["canopy_mae"] = round(float(np.abs(np.array(canopy) - np.array(ndvi)).mean()), 3)
    return Validation(
        ndvi_observed=ndvi,
        canopy_twin=canopy,
        soil_moisture_observed=observed_moisture,
        soil_moisture_twin=moisture_twin if farm is not None else None,
        fit=fit or None,
    )


def analyze_site(data: SiteData, request: AnalyzeRequest, farm: str | None = None, extra_gaps: list[str] | None = None) -> AnalyzeResponse:
    parsed = parse_rotation(request.current_rotation)
    current = parsed.crops
    site = build_site(data)
    plans = [("current", current)] + [(p.strategy_id, list(p.crops)) for p in generate_alternatives(current, site.climate.frost_days)]
    samples = build_samples(data.weather, data.lat, request.years, ENSEMBLE_SIZE, elevation=data.gee.elevation_m)
    params = SiteParams(data.lat, data.gee.slope_deg, data.gee.sm_rootzone, data.soil, site.climate.frost_days)
    runs = [run_strategy(crops, samples, params, request.years) for _, crops in plans]
    all_bands = [bands(run.metrics) for run in runs]
    scores = score_strategies(all_bands, request.priorities.model_dump())
    site_dict = site.model_dump()
    ndvi = list(data.gee.modis_ndvi_monthly) if data.satellite_available else []
    validation = build_validation(farm, ndvi, runs[0].canopy_monthly, runs[0].moisture_monthly)
    extra_evidence = validation_evidence(validation.fit, request.lang)
    gaps = list(parsed.gaps) + list(extra_gaps or [])
    summary = cdl_summary(farm) if farm is not None else None
    if summary is not None:
        cdl_evidence, cdl_gaps = cdl_text(summary, request.lang)
        extra_evidence = cdl_evidence + extra_evidence
        gaps += cdl_gaps
    et0_method = "penman_monteith" if data.weather.rh is not None and data.weather.ws is not None else "hargreaves"
    names = STRATEGY_NAMES[request.lang]
    strategies: list[Strategy] = []
    for (key, crops), run, band, score in zip(plans, runs, all_bands, scores):
        text = describe_strategy(
            key, crops, current, band, all_bands[0], run.vulnerability, site_dict, ndvi, request.lang,
            et0_method, extra_evidence, gaps, runs[0].vulnerability,
        )
        strategies.append(
            Strategy(
                id=key,
                name=f"{names[key]} ({' > '.join(crops)})",
                is_current=key == "current",
                rotation=seasons_of(run.plantings),
                score=score,
                metrics=band,
                bare_soil_calendar=run.bare_calendar,
                vulnerability=run.vulnerability,
                daily_sample=run.daily_sample,
                **text,
            )
        )
    register(site_key(data.lat, data.lon), strategies)
    ordered = [strategies[0]] + sorted(strategies[1:], key=lambda s: -s.score)
    return AnalyzeResponse(
        site=site,
        strategies=ordered,
        validation=validation,
        sources=sources_for(data, farm, et0_method),
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def demo_fallback_site(lat: float, lon: float) -> SiteData:
    base = load_farm_site(nearest_farm(lat, lon))
    gee = base.gee.model_copy(update={"lat": lat, "lon": lon})
    return SiteData(lat, lon, base.weather, gee, "demo", default_soil(), base.satellite_available)


def resolve_site(lat: float, lon: float, lang: str = "en") -> tuple[SiteData, str | None, list[str]]:
    farm = farm_for(lat, lon)
    if farm is not None:
        return load_farm_site(farm), farm, []
    gap = [LIVE_UNAVAILABLE_GAP[lang]]
    try:
        data = load_site(lat, lon)
    except Exception:
        return demo_fallback_site(lat, lon), None, gap
    if data.data_mode == "demo":
        data = SiteData(lat, lon, data.weather, data.gee.model_copy(update={"lat": lat, "lon": lon}), "demo", data.soil, data.satellite_available)
        return data, None, gap
    return data, None, []


def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    data, farm, gaps = resolve_site(request.lat, request.lon, request.lang)
    return analyze_site(data, request, farm, gaps)


def compute_demo(farm: str = DEFAULT_FARM, lang: str = "en") -> AnalyzeResponse:
    data = load_farm_site(farm)
    request = AnalyzeRequest(
        lat=data.lat, lon=data.lon, current_rotation=default_rotation(farm), priorities=DEMO_PRIORITIES, years=5, lang=lang
    )
    return analyze_site(data, request, farm)


def get_demo(farm: str = DEFAULT_FARM) -> AnalyzeResponse:
    path = demo_path(farm)
    if path.exists():
        try:
            response = AnalyzeResponse(**json.loads(path.read_text(encoding="utf-8")))
            register(site_key(response.site.lat, response.site.lon), response.strategies)
            return response
        except (OSError, ValueError):
            pass
    response = compute_demo(farm)
    try:
        path.write_text(response.model_dump_json(), encoding="utf-8")
    except OSError:
        pass
    return response


def default_registry(farm: str) -> dict[str, list[str]]:
    data = load_farm_site(farm)
    current = default_rotation(farm)
    frost = climate_summary(data.weather, data.lat, data.gee.elevation_m)["frost_days"]
    registry = {"current": list(current)}
    for plan in generate_alternatives(current, frost):
        registry[plan.strategy_id] = list(plan.crops)
    return registry


def what_if(request: WhatIfRequest) -> WhatIfResponse:
    site = request.site
    key = site_key(site.lat, site.lon)
    farm = farm_for(site.lat, site.lon)
    fallback_farm = farm or nearest_farm(site.lat, site.lon)
    if request.rotation:
        crops = crops_of_seasons(request.rotation)
    else:
        known = _REGISTRY.get((key, request.strategy_id)) or default_registry(fallback_farm).get(request.strategy_id)
        crops = list(known or default_rotation(fallback_farm))
    swap = normalize_crop(request.crop_swap) if request.crop_swap else None
    if swap:
        crops[0] = swap
    soil = site.soil or (load_farm_site(farm).soil if farm else default_soil())
    emulator = get_emulator()
    if emulator is not None:
        prediction = emulator.predict(crops, request.sowing_shift_days, max(request.irrigation_mm, 0.0), 0.0, site, soil)
        if prediction is not None:
            metrics = {
                name: Band(
                    p10=round(prediction.p50[name] - prediction.quantile[name], 2),
                    p50=round(prediction.p50[name], 2),
                    p90=round(prediction.p50[name] + prediction.quantile[name], 2),
                    unit=METRIC_UNITS[name],
                )
                for name in METRIC_KEYS
            }
            return WhatIfResponse(metrics=metrics, method="emulator", coverage=round(prediction.coverage, 3))
    data = load_farm_site(farm) if farm else None
    if data is None:
        try:
            data = demo_fallback_site(site.lat, site.lon) if site.data_mode == "demo" else load_site(site.lat, site.lon)
        except Exception:
            data = demo_fallback_site(site.lat, site.lon)
    years = 5
    samples = build_samples(data.weather, site.lat, years, ENSEMBLE_SIZE, elevation=site.elevation_m)
    params = SiteParams(site.lat, site.slope_deg, site.sm_rootzone, soil, site.climate.frost_days)
    run = run_strategy(crops, samples, params, years, max(request.irrigation_mm, 0.0), request.sowing_shift_days)
    return WhatIfResponse(metrics=bands(run.metrics), method="twin", coverage=0.8)


def explain_text(strategy: Strategy, lang: str) -> str:
    heads = {
        "en": ("Why", "Evidence", "Benefits", "Data gaps", "Risks for local review"),
        "es": ("Por qué", "Evidencia", "Beneficios", "Vacíos de datos", "Riesgos para revisión local"),
    }[lang]
    def block(title: str, items: list[str]) -> str:
        return f"{title}\n" + "\n".join(f"- {item}" for item in items) + "\n\n"
    out = f"{strategy.name}\n\n{heads[0]}\n{strategy.why}\n\n"
    out += block(heads[1], strategy.evidence) + block(heads[2], strategy.benefits)
    out += block(heads[3], strategy.gaps) + block(heads[4], strategy.risks)
    return out

