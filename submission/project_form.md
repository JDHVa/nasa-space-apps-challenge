# Project submission form drafts

## Project name
FieldTwin

## High-level summary (<= 200 words)
FieldTwin is a decision-support tool that builds a NASA-data digital twin of any field on a map and compares crop rotation strategies under a changing climate. A farmer clicks a location, enters the current rotation and priorities (water, nitrogen, erosion, soil organic matter, income), and FieldTwin simulates the current rotation plus alternatives such as a legume cover crop, a double crop or a lower-water crop over 30 historic weather years and warming scenarios. It reports P10-P90 ranges for water use, irrigation need, yield index, nitrogen balance, erosion and soil organic matter, shows when the field is typically bare and when crops are vulnerable to heat, frost or water stress, and lists data gaps and risks that need local review. A PyTorch emulator with conformal 90% intervals answers what-if questions instantly, and a local language model explains each strategy using only the computed numbers. Everything is presented in an animated 3D field. FieldTwin never prescribes: it shows ranges and asks for local agronomic judgment.

## Project details
**What it does.** Turns a map click into a simulated field and compares at least three rotations (the current one and generated alternatives) with uncertainty, bare-soil calendar, vulnerability months, evidence, benefits, gaps and risks.

**How it works.** NASA POWER daily weather and soil data (SoilGrids, SSURGO) drive a daily biophysical twin: FAO-56 water balance, growing-degree-day phenology, RUSLE-lite erosion, nitrogen balance with legume fixation and an organic matter index. An ensemble over 30 historic years and +1.5 C / +2.5 C warming gives P10/P50/P90. A PyTorch emulator trained on 4,000 twin runs (test R2 0.954-0.978; conformal 90% coverage 0.907 on average) provides instant what-ifs. A local Ollama LLM (qwen3:4b) narrates results and is checked against the twin's numbers, with a template fallback. The React/Three.js interface animates crops, soil moisture, rain and bare soil along a timeline, in English and Spanish.

**Validation.** Twin monthly soil moisture vs NASA POWER root-zone wetness: r = 0.94 (Iowa), r = 0.65 (Bajio, Mexico).

**Benefits.** Makes NASA data usable for field-level adaptation planning, shows trade-offs across priorities, runs offline with a bundled demo and a local LLM (no data leaves the machine), and is transparent about uncertainty and data gaps.

**Intended impact.** Help farmers, extension agents and advisors explore climate-adaptive rotations (less bare soil and erosion, lower water demand, better nitrogen and soil carbon) before committing, and know what to verify locally.

**Tools, languages, hardware.** Python 3.11, FastAPI, numpy, pandas, PyTorch (trained on an NVIDIA GPU), Ollama (qwen3:4b), TypeScript, React, Vite, Tailwind, Framer Motion, React Three Fiber, MapLibre, Recharts. Google Earth Engine client implemented. Runs on a laptop.

## Use of NASA data
- **NASA POWER daily (AG community, 1995-2024):** Tmax, Tmin, precipitation, solar radiation, humidity and wind drive ET0, crop water balance, GDD, frost/heat days and the 30-year ensemble.
- **NASA POWER climatology (MERRA-2 GWETROOT/GWETTOP):** initial soil wetness and the validation target for the twin's soil moisture.
- **Implemented, pending credentials (not used in reported results):** SMAP SPL4SMGP (initial root-zone/surface moisture), GPM IMERG V07 (precipitation), MODIS MOD13Q1 (NDVI vs twin canopy validation), SRTM (elevation, slope for erosion and 3D terrain), GRACE (groundwater storage context), through Google Earth Engine.

## Space agency partner and other data
NASA. Other data: ISRIC SoilGrids v2.0, USDA NRCS SSURGO (Soil Data Access), USDA NASS Cropland Data Layer (CropScape).

## References
- NASA POWER: https://power.larc.nasa.gov
- SoilGrids: https://soilgrids.org
- SSURGO / Soil Data Access: https://sdmdataaccess.sc.egov.usda.gov
- CropScape CDL: https://nassgeodata.gmu.edu/CropScape
- Implemented, pending credentials (GEE catalog):
  - SMAP SPL4SMGP: https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008
  - GPM IMERG V07: https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07
  - MODIS MOD13Q1: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1
  - SRTM: https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003
  - GRACE: https://developers.google.com/earth-engine/datasets/catalog/NASA_GRACE_MASS_GRIDS_V04_LAND
- FAO-56: Allen et al., Crop evapotranspiration, FAO Irrigation and Drainage Paper 56.

## Use of Artificial Intelligence
Yes. (1) Our code was written with AI coding assistants (Claude and Gemini) under human direction and review. (2) A local LLM, qwen3:4b via Ollama, writes the narration of results, constrained to numbers computed by the twin (with a number-grounding check and template fallback). (3) The PyTorch emulator was designed and trained by us on our own simulations. (4) Any AI-generated images or video in the submission carry a visible watermark.
