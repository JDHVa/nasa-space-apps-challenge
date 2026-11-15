from typing import Literal

from pydantic import BaseModel, Field

MetricKey = Literal[
    "water_use_mm",
    "irrigation_need_mm",
    "yield_index",
    "n_balance_kg_ha",
    "erosion_t_ha",
    "soil_om_index",
    "income_index",
    "water_stress_days",
    "bare_soil_days",
]


class Band(BaseModel):
    p10: float
    p50: float
    p90: float
    unit: str


class Season(BaseModel):
    crop: str
    year_index: int
    start_month: int
    end_month: int


class Vulnerability(BaseModel):
    month: int
    type: Literal["heat", "frost", "drought", "waterlogging", "erosion"]
    severity: float
    soil_loss_t_ha: float | None = None


class DailyPoint(BaseModel):
    day: int
    crop: str | None
    canopy: float
    soil_moisture: float
    rain_mm: float
    et_mm: float


class Strategy(BaseModel):
    id: str
    name: str
    is_current: bool
    rotation: list[Season]
    score: float
    why: str
    evidence: list[str]
    benefits: list[str]
    gaps: list[str]
    risks: list[str]
    metrics: dict[MetricKey, Band]
    bare_soil_calendar: list[float]
    vulnerability: list[Vulnerability]
    daily_sample: list[DailyPoint]


class Climate(BaseModel):
    tmax_mean: float
    tmin_mean: float
    precip_annual_mm: float
    et0_annual_mm: float
    frost_days: float
    heat_days: float


class Soil(BaseModel):
    source: str
    texture: str
    sand_pct: float
    clay_pct: float
    om_pct: float
    awc_mm_per_m: float
    field_capacity: float
    wilting_point: float
    k_factor: float
    hydrologic_group: str
    curve_number: float
    notes: list[str] = []


class Site(BaseModel):
    lat: float
    lon: float
    elevation_m: float
    slope_deg: float
    sm_surface: float
    sm_rootzone: float
    gpm_annual_mm: float | None = None
    grace_lwe_cm: float | None = None
    climate: Climate
    data_mode: Literal["live", "cache", "demo"]
    soil: Soil | None = None
    satellite_available: bool = True


class Priorities(BaseModel):
    water: float = Field(0.5, ge=0, le=1)
    nitrogen: float = Field(0.5, ge=0, le=1)
    erosion: float = Field(0.5, ge=0, le=1)
    organic_matter: float = Field(0.5, ge=0, le=1)
    income: float = Field(0.5, ge=0, le=1)


class AnalyzeRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    current_rotation: list[str]
    priorities: Priorities = Priorities()
    years: int = Field(5, ge=1, le=10)
    lang: Literal["en", "es"] = "en"


class Validation(BaseModel):
    ndvi_observed: list[float]
    canopy_twin: list[float]
    soil_moisture_observed: list[float] | None = None
    soil_moisture_twin: list[float] | None = None
    fit: dict[str, float] | None = None


class SourceRef(BaseModel):
    name: str
    dataset: str
    use: str


class AnalyzeResponse(BaseModel):
    site: Site
    strategies: list[Strategy]
    validation: Validation
    sources: list[SourceRef]
    generated_at: str


class WhatIfRequest(BaseModel):
    strategy_id: str
    sowing_shift_days: int = 0
    irrigation_mm: float = 0.0
    crop_swap: str | None = None
    site: Site
    rotation: list[Season] | None = None


class WhatIfResponse(BaseModel):
    metrics: dict[MetricKey, Band]
    method: Literal["emulator", "twin"]
    coverage: float


class ExplainRequest(BaseModel):
    strategy_id: str
    analysis: AnalyzeResponse
    lang: Literal["en", "es"] = "en"
