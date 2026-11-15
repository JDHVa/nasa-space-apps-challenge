# SPEC.md — FieldTwin product & engineering spec

**FieldTwin** is our entry for NASA Space Apps Challenge 2026, challenge "Field Shift: Adapting Farms with NASA Data". Every agent working on code reads this file. **HARD DEADLINE: submission today 2026-11-15 23:59 local.** Feature freeze 21:30. Favor working, demo-safe code over ambitious code.

## 1. Product
A decision-support tool: the user clicks any point on a map, enters the current crop rotation and priorities (water use, nitrogen, erosion, soil organic matter, income). FieldTwin builds a **biophysical digital twin** of the field from NASA data, simulates the current rotation plus at least 2 alternatives over several years and climate scenarios, and shows animated 3D results with calibrated uncertainty.
Challenge requirements the product MUST satisfy:
- Combine NASA observations with local soil, crop traits and farmer priorities.
- Show when fields are typically bare and which seasons current crops are most vulnerable (heat, frost, water stress).
- Compare **≥3 rotation strategies including the current one**; for each: why proposed, supporting evidence (which NASA data), benefits, data gaps, risks needing local review.
- Never replace farmer judgment: show ranges, not prescriptions; visible disclaimer.

## 2. Architecture and folders
```
backend/                Python 3.11, FastAPI, uvicorn, numpy, pandas, httpx, earthengine-api, torch, pydantic
  app/data/power.py     NASA POWER daily point API (no auth): T2M_MAX, T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN, RH2M, WS2M, 1995-2025
  app/data/gee.py       Earth Engine point/buffer reductions: SMAP NASA/SMAP/SPL4SMGP/008 (sm_surface, sm_rootzone), GPM NASA/GPM_L3/IMERG_V07, MODIS MODIS/061/MOD13Q1 NDVI, SRTM USGS/SRTMGL1_003 (elevation, slope), GRACE NASA/GRACE/MASS_GRIDS_V04/LAND; optional GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL
  app/data/cache.py     disk cache keyed by rounded lat/lon in backend/cache/; bundled demo farm in backend/demo/ that works fully offline
  app/twin/crops.py     crop library: maize, sorghum, wheat, beans, soybean, oats, alfalfa, vetch, rye (Kc stages, GDD base/targets, root depth, heat/frost thresholds, N fixation, residue cover, water demand, relative market value)
  app/twin/engine.py    daily FAO-56 single-Kc soil water balance (ET0 Hargreaves or Penman-Monteith from POWER), GDD phenology, stress days, bare-soil days, RUSLE-lite erosion (slope from SRTM, cover factor from canopy/residue), N balance with legume fixation, soil organic matter index; initial soil moisture from SMAP
  app/twin/rotations.py current rotation parser + generator of ≥2 alternatives (e.g. legume/cover-crop insertion, lower-water-demand crop) scored against priorities
  app/twin/ensemble.py  resample 30 historic years + warming scenarios (+1.5 C, +2.5 C) → P10/P50/P90 per metric
  app/ai/emulator.py    PyTorch MLP trained on thousands of twin runs (CUDA if available, RTX 5050 8 GB) for instant what-if; split-conformal 90% intervals on a held-out calibration set
  app/ai/narrator.py    Ollama http://localhost:11434, model qwen3:4b-instruct-2507-q4_K_M; prompt receives ONLY the computed JSON; outputs why/evidence/benefits/gaps/risks per strategy in "en" or "es"; template fallback if Ollama is down
  app/api.py            routes below
  tests/                pytest
frontend/               React + Vite + TypeScript, Tailwind, Framer Motion, @react-three/fiber + drei, maplibre-gl, recharts
  screens: MapSelect → TwinView (3D) → Compare
```
API contract (JSON):
- `POST /analyze` body `{lat, lon, current_rotation: string[], priorities: {water, nitrogen, erosion, organic_matter, income}: 0..1, years: int=5, lang: "en"|"es"}` → `{site: {...nasa summaries}, strategies: [{id, name, rotation, metrics: {name: {p10,p50,p90,unit}}, bare_soil_calendar: number[12], vulnerability: [{month, type, severity}], daily_sample: [...for 3D animation]}], validation: {ndvi_observed, canopy_twin}, sources: [...]}`
- `POST /whatif` body `{strategy_id, sowing_shift_days, irrigation_mm, crop_swap}` → metrics with conformal intervals (emulator; twin fallback)
- `POST /explain` → streamed narrator text
- `GET /demo` → precomputed `/analyze` response for the bundled demo farm (offline)

Frontend experience (must look great; this is what judges see):
1. **MapSelect**: dark satellite-style basemap, click → animated fly-to and pulsing marker, side panel with rotation chips and priority sliders, "Build twin" button with progress steps showing which NASA dataset is loading.
2. **TwinView**: 3D field parcel (terrain from SRTM when available, stylized plane otherwise), crops that grow and get harvested along a year timeline scrubber, soil cross-section with animated moisture layers, rain particles from precipitation data, bare-soil periods shown as exposed soil; switch strategies A/B/C with smooth transitions.
3. **Compare**: strategy cards with metric P10–P90 bands, radar chart vs priorities, 12-month bare-soil heatmap, vulnerability ribbon, MODIS NDVI vs twin canopy chart, narrator explanation, "Data gaps & local review" box, disclaimer. EN/ES toggle.

## 3. Coding rules (mandatory)
- **NO comments and NO docstrings in code.** Use descriptive names and type hints instead.
- Python: type hints everywhere, pydantic models for API I/O, small focused modules, no global mutable state except caches.
- TypeScript: strict mode, typed API client in one file, components small.
- Every network call has a timeout and a fallback to cache or demo data. The demo must work with internet off.
- Secrets only in `.env` (`GEE_PROJECT=...`); add `.env.example`; never commit secrets.
- Do not install heavy extras beyond the stack above without asking via `Q`.
- Do not `git commit` or `git push` unless the human asks.
- Run what you write before reporting `DONE` (pytest, `uvicorn` boot, `npm run build`).

## 4. Team
Claude (main session) orchestrates; subagents in `.claude/agents/` do the work. See `CLAUDE.md`.

## 5. Existing code
Gemini already scaffolded M1 and parts of M2 (`backend/app/data/*`, `backend/demo/bajio_gee.json`, `frontend/src/*`). Reuse and fix it; do not start over.

## 6. Milestones (in order)
1. M1 scaffold: folders, backend FastAPI boot with `/health`, frontend Vite app with routing for the 3 screens, `.env.example`, `README.md` run instructions.
2. M2 data layer + cache + bundled demo farm.
3. M3 twin engine + rotations + ensemble + `/analyze` + `/demo`.
4. M4 emulator + conformal + `/whatif`; narrator + `/explain`.
5. M5 3D TwinView, animations, Compare screen, EN/ES.
6. M6 polish, fixes from final review, freeze 21:30.
Cut order if late: AlphaEarth → emulator (use twin directly) → SRTM terrain (stylized plane).

## 7. Exact API schema (source of truth for backend + frontend)
```ts
type Band = { p10: number; p50: number; p90: number; unit: string }
type Season = { crop: string; year_index: number; start_month: number; end_month: number }
type MetricKey = "water_use_mm" | "irrigation_need_mm" | "yield_index" | "n_balance_kg_ha" | "erosion_t_ha" | "soil_om_index" | "income_index" | "water_stress_days" | "bare_soil_days"
type Vulnerability = { month: number; type: "heat" | "frost" | "drought" | "waterlogging" | "erosion"; severity: number }
type DailyPoint = { day: number; crop: string | null; canopy: number; soil_moisture: number; rain_mm: number; et_mm: number }
type Strategy = {
  id: string; name: string; is_current: boolean; rotation: Season[]; score: number
  why: string; evidence: string[]; benefits: string[]; gaps: string[]; risks: string[]
  metrics: Record<MetricKey, Band>
  bare_soil_calendar: number[]
  vulnerability: Vulnerability[]
  daily_sample: DailyPoint[]
}
type Site = {
  lat: number; lon: number; elevation_m: number; slope_deg: number
  sm_surface: number; sm_rootzone: number; gpm_annual_mm: number; grace_lwe_cm: number
  climate: { tmax_mean: number; tmin_mean: number; precip_annual_mm: number; et0_annual_mm: number; frost_days: number; heat_days: number }
  data_mode: "live" | "cache" | "demo"
}
type AnalyzeRequest = { lat: number; lon: number; current_rotation: string[]; priorities: { water: number; nitrogen: number; erosion: number; organic_matter: number; income: number }; years: number; lang: "en" | "es" }
type AnalyzeResponse = { site: Site; strategies: Strategy[]; validation: { ndvi_observed: number[]; canopy_twin: number[] }; sources: { name: string; dataset: string; use: string }[]; generated_at: string }
type WhatIfRequest = { strategy_id: string; sowing_shift_days: number; irrigation_mm: number; crop_swap: string | null; site: Site }
type WhatIfResponse = { metrics: Record<MetricKey, Band>; method: "emulator" | "twin"; coverage: number }
```
- `bare_soil_calendar`: 12 values 0..1, fraction of the month with bare soil (averaged over years).
- `daily_sample`: weekly points (every 7 days) across all simulated years, for 3D animation.
- `soil_moisture` relative 0..1 of available water; `canopy` 0..1 (comparable to scaled NDVI).
- Strategies: index 0 is the current rotation (`is_current: true`); at least 2 alternatives; sorted by `score` desc after the current one.
- Routes: `POST /analyze`, `POST /whatif`, `POST /explain` (body `{strategy_id, analysis: AnalyzeResponse, lang}` → `text/plain` stream), `GET /demo` (AnalyzeResponse, offline), `GET /health`. CORS open for `http://localhost:5173`.
