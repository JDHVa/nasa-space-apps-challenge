from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import pandas as pd

from app.data.cache import read_demo_json
from app.data.gee import GeeSiteSummary, fetch_gee_summary
from app.data.power import PowerDataset, fetch_power_daily
from app.data.soil import default_soil
from app.schemas import Soil


@dataclass
class HistoricWeather:
    tmax: np.ndarray
    tmin: np.ndarray
    precip: np.ndarray
    srad: np.ndarray
    years: np.ndarray
    rh: np.ndarray | None = None
    ws: np.ndarray | None = None


@dataclass
class SiteData:
    lat: float
    lon: float
    weather: HistoricWeather
    gee: GeeSiteSummary
    data_mode: str
    soil: Soil = field(default_factory=default_soil)
    satellite_available: bool = True


def to_historic(dataset: PowerDataset) -> HistoricWeather:
    frame = pd.DataFrame([d.model_dump() for d in dataset.days])
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame[~((frame["date"].dt.month == 2) & (frame["date"].dt.day == 29))]
    frame["year"] = frame["date"].dt.year
    counts = frame.groupby("year")["date"].count()
    full_years = counts[counts == 365].index.to_numpy()
    frame = frame[frame["year"].isin(full_years)].sort_values("date")
    shape = (len(full_years), 365)
    return HistoricWeather(
        tmax=frame["tmax"].to_numpy(dtype=float).reshape(shape),
        tmin=frame["tmin"].to_numpy(dtype=float).reshape(shape),
        precip=frame["precip"].to_numpy(dtype=float).reshape(shape),
        srad=frame["srad"].to_numpy(dtype=float).reshape(shape),
        years=full_years,
        rh=frame["rh"].to_numpy(dtype=float).reshape(shape),
        ws=frame["ws"].to_numpy(dtype=float).reshape(shape),
    )


def _mode(sources: list[str]) -> str:
    if any(s.startswith("demo") for s in sources):
        return "demo"
    if any(s == "cache" for s in sources):
        return "cache"
    return "live"


@lru_cache(maxsize=16)
def _demo_weather() -> HistoricWeather:
    return to_historic(PowerDataset(**read_demo_json("bajio_power.json")))


def load_demo_site() -> SiteData:
    gee = GeeSiteSummary(**read_demo_json("bajio_gee.json"))
    return SiteData(gee.lat, gee.lon, _demo_weather(), gee, "demo", satellite_available=gee.verified)


_LIVE: dict[str, tuple[HistoricWeather, str]] = {}


def load_site(lat: float, lon: float) -> SiteData:
    key = f"{lat:.2f}_{lon:.2f}"
    gee = fetch_gee_summary(lat, lon)
    if key not in _LIVE:
        power = fetch_power_daily(lat, lon)
        _LIVE[key] = (to_historic(power), power.source)
    weather, power_source = _LIVE[key]
    return SiteData(lat, lon, weather, gee, _mode([power_source, gee.source]), satellite_available=gee.verified)
