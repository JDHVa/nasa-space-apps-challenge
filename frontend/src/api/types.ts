export type Band = { p10: number; p50: number; p90: number; unit: string };
export type Season = { crop: string; year_index: number; start_month: number; end_month: number };
export type MetricKey =
  | "water_use_mm"
  | "irrigation_need_mm"
  | "yield_index"
  | "n_balance_kg_ha"
  | "erosion_t_ha"
  | "soil_om_index"
  | "income_index"
  | "water_stress_days"
  | "bare_soil_days";
export type Vulnerability = {
  month: number;
  type: "heat" | "frost" | "drought" | "waterlogging" | "erosion";
  severity: number;
};
export type DailyPoint = {
  day: number;
  crop: string | null;
  canopy: number;
  soil_moisture: number;
  rain_mm: number;
  et_mm: number;
};
export type Strategy = {
  id: string;
  name: string;
  is_current: boolean;
  rotation: Season[];
  score: number;
  why: string;
  evidence: string[];
  benefits: string[];
  gaps: string[];
  risks: string[];
  metrics: Record<MetricKey, Band>;
  bare_soil_calendar: number[];
  vulnerability: Vulnerability[];
  daily_sample: DailyPoint[];
};
export type Site = {
  lat: number;
  lon: number;
  elevation_m: number;
  slope_deg: number;
  sm_surface: number;
  sm_rootzone: number;
  gpm_annual_mm: number | null;
  grace_lwe_cm: number | null;
  climate: {
    tmax_mean: number;
    tmin_mean: number;
    precip_annual_mm: number;
    et0_annual_mm: number;
    frost_days: number;
    heat_days: number;
  };
  data_mode: "live" | "cache" | "demo";
  soil?: Soil;
  satellite_available?: boolean;
};
export type Soil = {
  source?: string;
  texture?: string;
  sand_pct?: number;
  clay_pct?: number;
  om_pct?: number;
  awc_mm_per_m?: number;
  field_capacity?: number;
  wilting_point?: number;
  k_factor?: number;
  hydrologic_group?: string;
  curve_number?: number;
  notes?: string[];
};
export type Fit = {
  soil_moisture_r?: number;
  soil_moisture_mae?: number;
  canopy_r?: number;
  canopy_mae?: number;
};
export type Validation = {
  ndvi_observed: number[];
  canopy_twin: number[];
  soil_moisture_observed?: number[];
  soil_moisture_twin?: number[];
  fit?: Fit;
};
export type Priorities = {
  water: number;
  nitrogen: number;
  erosion: number;
  organic_matter: number;
  income: number;
};
export type Lang = "en" | "es";
export type AnalyzeRequest = {
  lat: number;
  lon: number;
  current_rotation: string[];
  priorities: Priorities;
  years: number;
  lang: Lang;
};
export type AnalyzeResponse = {
  site: Site;
  strategies: Strategy[];
  validation: Validation;
  sources: { name: string; dataset: string; use: string }[];
  generated_at: string;
};
export type WhatIfRequest = {
  strategy_id: string;
  sowing_shift_days: number;
  irrigation_mm: number;
  crop_swap: string | null;
  rotation?: Season[];
  site: Site;
};
export type WhatIfResponse = {
  metrics: Record<MetricKey, Band>;
  method: "emulator" | "twin";
  coverage: number;
};
export type ExplainRequest = { strategy_id: string; analysis: AnalyzeResponse; lang: Lang };
