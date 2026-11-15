# FieldTwin slides (7)

## 1. Title
**FieldTwin** - A NASA-data digital twin to adapt your farm's rotation.
NASA Space Apps Challenge 2026 - Field Shift: Adapting Farms with NASA Data. Team names.

*Speaker notes:* Introduce the team and the one-line idea: click a field, see how rotations behave under a warmer climate, with honest uncertainty.

## 2. The problem
- Warmer, more erratic weather; rotations built for the old climate.
- Evidence is scattered: satellites, soil surveys, local knowledge.
- Farmers need to know: when is my soil bare? when are crops exposed to heat, frost, water stress? what would a change do, and how sure are we?

*Speaker notes:* Frame the challenge. Tools often give one number; farmers need ranges and caveats.

## 3. The solution
- Click a point, enter rotation and priorities.
- Twin simulates the current rotation plus 3 alternatives with P10-P90.
- Bare-soil calendar, vulnerability months, evidence, gaps, risks.
- Animated 3D field. Never prescribes.

*Speaker notes:* Walk through the user flow. Mention EN/ES and the offline demo.

## 4. How it works
NASA data -> biophysical twin (FAO-56 water, GDD, RUSLE-lite erosion, N, soil OM) -> 30 historic years + 1.5/2.5 C warming -> PyTorch emulator with conformal 90% intervals -> local LLM narrator (qwen3:4b, twin numbers only) -> 3D UI.

*Speaker notes:* The narrator can only cite twin numbers (checked, with template fallback). The emulator gives instant what-ifs; test R2 0.954-0.978, conformal coverage 0.907 on average.

## 5. NASA data and validation
- Used: NASA POWER daily and climatology (MERRA-2 soil wetness), plus SoilGrids, SSURGO, CDL.
- Implemented via Google Earth Engine, pending credentials: SMAP, GPM IMERG, MODIS NDVI, SRTM, GRACE.
- Validation, twin soil moisture vs POWER GWETROOT: r 0.94 Iowa (MAE 0.223), r 0.65 Bajio (MAE 0.098).

*Speaker notes:* Be candid: satellite layers are not in the reported results; validation is against a reanalysis product, not in-situ data. Iowa shows a level offset despite good seasonality.

## 6. Demo and key results
[Screenshot placeholders: Map, 3D twin, Compare, What-if lab]
- Iowa soybean > maize: erosion 13.57 t/ha/yr, bare soil 261 days. Soybean > rye: erosion 10.18, bare soil 158 days, SOM index 67.9 vs 55.9, yield index 45.9 vs 76.7.
- Bajio maize > beans: irrigation 16.7 mm/yr; beans > oats 258.9 mm/yr (score 2.0 vs 52.8 for the current rotation); sorghum > beans 5.4 mm/yr.

*Speaker notes:* Show the trade-off between soil benefits and yield or water. All values are P50 from the demo files.

## 7. Impact and next steps
- Impact: fast, transparent exploration of adaptive rotations; local, private, offline-capable.
- Next: enable GEE credentials (SMAP, MODIS NDVI validation, SRTM terrain), calibrate with field yields, more crops and regions, farmer feedback.
- AI disclosure: built with Claude/Gemini coding assistants; local LLM narrator.

*Speaker notes:* Close on "decision support, not a replacement for farmer judgment". Thank the judges.
