from typing import Any

import httpx
from pydantic import BaseModel

from app.data.cache import read_cache, read_demo_json, write_cache

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_PARAMS = "T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M"


class DailyWeather(BaseModel):
    date: str
    tmax: float
    tmin: float
    precip: float
    srad: float
    rh: float
    ws: float


class PowerDataset(BaseModel):
    source: str
    lat: float
    lon: float
    days: list[DailyWeather]


def _clean_value(val: float | int | None, default: float) -> float:
    if val is None or float(val) <= -900.0:
        return default
    return float(val)


def _parse_power_payload(
    lat: float,
    lon: float,
    raw: dict[str, Any],
) -> PowerDataset:
    params = raw["properties"]["parameter"]
    dates = sorted(params["T2M_MAX"].keys())
    days: list[DailyWeather] = []
    prev_tmax, prev_tmin, prev_srad, prev_rh, prev_ws = 25.0, 11.0, 18.0, 55.0, 2.2
    for d in dates:
        tmax = _clean_value(params["T2M_MAX"].get(d), prev_tmax)
        tmin = _clean_value(params["T2M_MIN"].get(d), prev_tmin)
        precip = max(0.0, _clean_value(params["PRECTOTCORR"].get(d), 0.0))
        srad = max(1.0, _clean_value(params["ALLSKY_SFC_SW_DWN"].get(d), prev_srad))
        rh = min(100.0, max(5.0, _clean_value(params["RH2M"].get(d), prev_rh)))
        ws = max(0.2, _clean_value(params["WS2M"].get(d), prev_ws))
        prev_tmax, prev_tmin, prev_srad, prev_rh, prev_ws = tmax, tmin, srad, rh, ws
        iso = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        days.append(
            DailyWeather(
                date=iso,
                tmax=round(tmax, 2),
                tmin=round(tmin, 2),
                precip=round(precip, 2),
                srad=round(srad, 2),
                rh=round(rh, 2),
                ws=round(ws, 2),
            )
        )
    return PowerDataset(source="nasa_power", lat=lat, lon=lon, days=days)


def fetch_power_daily(
    lat: float,
    lon: float,
    start: str = "19950101",
    end: str = "20241231",
    timeout_s: float = 30.0,
) -> PowerDataset:
    cached = read_cache("power", lat, lon)
    if cached is not None:
        cached["source"] = "cache"
        return PowerDataset(**cached)

    query = {
        "parameters": POWER_PARAMS,
        "community": "AG",
        "longitude": round(lon, 4),
        "latitude": round(lat, 4),
        "start": start,
        "end": end,
        "format": "JSON",
    }
    try:
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.get(POWER_URL, params=query)
            resp.raise_for_status()
            dataset = _parse_power_payload(lat, lon, resp.json())
            write_cache("power", lat, lon, dataset.model_dump())
            return dataset
    except Exception:
        demo = read_demo_json("bajio_power.json")
        demo["source"] = "demo_fallback"
        demo["lat"] = lat
        demo["lon"] = lon
        return PowerDataset(**demo)
