import os
from typing import Any

from pydantic import BaseModel

from app.data.cache import BACKEND_ROOT, read_cache, read_demo_json, write_cache


class GeeSiteSummary(BaseModel):
    source: str
    lat: float
    lon: float
    elevation_m: float
    slope_deg: float
    sm_surface: float
    sm_rootzone: float
    gpm_annual_mm: float | None = None
    modis_ndvi_monthly: list[float]
    grace_lwe_cm: float | None = None
    embedding_available: bool = False
    verified: bool = False


def _env_project() -> str:
    value = os.getenv("GEE_PROJECT", "").strip()
    if value:
        return value
    for env_file in (BACKEND_ROOT / ".env", BACKEND_ROOT.parent / ".env"):
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEE_PROJECT="):
                    return line.split("=", 1)[1].strip()
        except OSError:
            continue
    return ""


def _try_init_ee() -> Any:
    project = _env_project()
    if not project:
        return None
    try:
        import ee

        ee.Initialize(project=project)
        return ee
    except Exception:
        return None


def _reduce_point(ee: Any, image: Any, point: Any, scale: int) -> dict[str, Any]:
    return image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point.buffer(500),
        scale=scale,
        maxPixels=1e7,
    ).getInfo() or {}


def _required(values: dict[str, Any], key: str) -> float:
    value = values.get(key)
    if value is None:
        raise ValueError(f"Earth Engine returned no value for {key}")
    return float(value)


def fetch_live_summary(ee: Any, lat: float, lon: float) -> GeeSiteSummary:
    point = ee.Geometry.Point([lon, lat])
    terrain = ee.Terrain.products(ee.Image("USGS/SRTMGL1_003"))
    topo = _reduce_point(ee, terrain.select(["elevation", "slope"]), point, 30)

    smap = (
        ee.ImageCollection("NASA/SMAP/SPL4SMGP/008")
        .filterDate("2023-01-01", "2024-12-31")
        .select(["sm_surface", "sm_rootzone"])
        .mean()
    )
    smap_vals = _reduce_point(ee, smap, point, 9000)

    gpm = (
        ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
        .filterDate("2023-01-01", "2023-12-31")
        .select("precipitation")
        .sum()
        .multiply(0.5)
    )
    gpm_vals = _reduce_point(ee, gpm, point, 11000)

    modis_monthly: list[float] = []
    modis_col = ee.ImageCollection("MODIS/061/MOD13Q1").filterDate("2020-01-01", "2024-12-31").select("NDVI")
    for month in range(1, 13):
        m_img = modis_col.filter(ee.Filter.calendarRange(month, month, "month")).mean()
        modis_monthly.append(round(_required(_reduce_point(ee, m_img, point, 250), "NDVI") * 0.0001, 3))

    grace = (
        ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/LAND")
        .filterDate("2015-01-01", "2017-06-30")
        .select("lwe_thickness")
        .mean()
    )
    grace_vals = _reduce_point(ee, grace, point, 50000)

    embedding_available = False
    try:
        embedding_available = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").first() is not None
    except Exception:
        embedding_available = False

    return GeeSiteSummary(
        source="google_earth_engine",
        lat=lat,
        lon=lon,
        elevation_m=round(_required(topo, "elevation"), 1),
        slope_deg=round(_required(topo, "slope"), 2),
        sm_surface=round(_required(smap_vals, "sm_surface"), 3),
        sm_rootzone=round(_required(smap_vals, "sm_rootzone"), 3),
        gpm_annual_mm=round(_required(gpm_vals, "precipitation"), 1),
        modis_ndvi_monthly=modis_monthly,
        grace_lwe_cm=round(_required(grace_vals, "lwe_thickness"), 2),
        embedding_available=embedding_available,
        verified=True,
    )


def unverified_fallback(lat: float, lon: float) -> GeeSiteSummary:
    demo = read_demo_json("bajio_gee.json")
    demo["source"] = "demo_fallback"
    demo["verified"] = False
    demo["lat"] = lat
    demo["lon"] = lon
    return GeeSiteSummary(**demo)


def fetch_gee_summary(lat: float, lon: float) -> GeeSiteSummary:
    cached = read_cache("gee", lat, lon)
    if cached is not None and cached.get("verified") is True:
        cached["source"] = "cache"
        return GeeSiteSummary(**cached)

    ee = _try_init_ee()
    if ee is None:
        return unverified_fallback(lat, lon)

    try:
        summary = fetch_live_summary(ee, lat, lon)
        write_cache("gee", lat, lon, summary.model_dump())
        return summary
    except Exception:
        return unverified_fallback(lat, lon)
