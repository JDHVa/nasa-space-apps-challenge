# FieldTwin: respuestas para el formulario (Team R3V0LUT11ON)

Copia cada bloque en su campo. Todo está en inglés, como pide el formulario.

---

## Summary *

FieldTwin is a decision-support tool that turns NASA Earth data into a 3D digital twin of any farm field. A user clicks a point on the map, enters the current crop rotation and sets their priorities: water, nitrogen, erosion and income. FieldTwin then simulates that rotation alongside three adaptive alternatives with a biophysical model: an FAO-56 water balance driven by NASA POWER daily weather (1995–2024), crop phenology, erosion, nitrogen and soil organic matter. Soil data comes from USDA SSURGO and ISRIC SoilGrids, and crop history from the USDA Cropland Data Layer. Thirty historic years plus +1.5 °C and +2.5 °C warming scenarios produce P10–P90 uncertainty ranges. The tool shows when the soil is bare, which seasons are vulnerable, the trade-offs between strategies, the supporting evidence, the data gaps and the risks that need local review. A GPU-trained neural emulator answers what-if questions instantly, and a local LLM explains the results using only numbers the twin produced. As the climate shifts, farmers need transparent, evidence-based ways to explore change. FieldTwin supports their decision and never replaces it.

---

## Project Demonstration *

https://github.com/JDHVa/nasa-space-apps-challenge/blob/main/submission/FieldTwin_R3V0LUT11ON.pptx

(7 diapositivas. Ábrelo en una ventana de incógnito para confirmar que es público.)

## Project *

https://github.com/JDHVa/nasa-space-apps-challenge

---

## Project Details *

**What it does.** FieldTwin turns a click on the map into a simulated field. It compares the current rotation with three generated alternatives (a legume cover crop, a winter cereal cover and a double crop or lower-water crop). For each one it shows P10–P90 uncertainty ranges, a calendar of bare-soil days, the months when crops are vulnerable to heat, frost or water stress, and the evidence, benefits, data gaps and risks that need local review.

**How it works.** NASA POWER daily weather (1995–2024) and soil data from SSURGO and SoilGrids drive a daily biophysical digital twin with these parts:
- FAO-56 Penman-Monteith water balance
- growing-degree-day phenology
- curve-number runoff
- RUSLE-lite erosion
- nitrogen balance with legume fixation
- a soil organic matter index

An ensemble of 40 runs (30 historic years resampled, plus +1.5 °C and +2.5 °C warming) produces P10, P50 and P90 values. A PyTorch emulator trained on thousands of twin runs on a laptop GPU (RTX 5050) makes the what-if lab instant. It reaches a test R² of 0.954–0.978, with split-conformal 90% intervals and an empirical coverage of 0.907. A local Ollama LLM (qwen3:4b) narrates each strategy, and a check rejects any number that the twin did not produce; when that happens, a template is used instead. The React and Three.js interface animates crop growth, soil moisture, rain and bare soil along a timeline, in English and Spanish.

**Validation.** We compared the twin's monthly soil moisture with NASA POWER root-zone wetness (GWETROOT): r = 0.94 in Iowa, USA, and r = 0.65 in the Bajío, Mexico. The Iowa rotation comes from real Cropland Data Layer history for 2010–2024.

**Benefits.** FieldTwin makes NASA data usable for adaptation planning at field level and shows the trade-offs between priorities, for example soil protection against yield and water use. It is honest about uncertainty and data gaps. It runs offline with bundled demo farms, and because the LLM is local, no data leaves the machine.

**Intended impact.** Farmers, extension agents and advisors can explore climate-adaptive rotations before committing to them: less bare soil and erosion, lower water demand, better nitrogen and soil carbon. They also learn exactly what to verify locally. FieldTwin is decision support; the farmer decides.

**Creativity.** FieldTwin uses a physics-first digital twin that answers causal what-if questions, which a purely statistical model cannot do. On top of it sits an AI emulator with calibrated uncertainty and a narrator whose numbers are checked against the twin. Everything is shown as an animated 3D field instead of a static report.

**Factors we considered.**
- Scientific validity: standard FAO-56 methods and validation against NASA data.
- Transparency: ranges instead of single numbers, and data gaps listed explicitly.
- Accessibility: runs offline on a laptop and is bilingual.
- The farmer's own priorities.

**Tools, languages, hardware.**
- Backend: Python 3.11, FastAPI, NumPy, pandas, PyTorch (CUDA, NVIDIA RTX 5050 laptop GPU).
- Narration: Ollama with qwen3:4b-instruct.
- Frontend: TypeScript, React, Vite, Tailwind CSS, Framer Motion, React Three Fiber and drei, MapLibre GL, Recharts.
- Earth Engine: the Google Earth Engine client is implemented for future satellite layers.

---

## Use of Super Intelligence (SI) *

Marca estas opciones:
- [x] Code generation / coding assistant
- [x] Text / LLM (chatbot, large language model)
- [ ] Image generation, solo si existe la opción y la usaron; las capturas son reales de la app

Si hay un campo de texto:

Code was written with AI coding assistants (Anthropic Claude, and Google Gemini for the initial scaffold) under the direction and review of the team. The team defined the idea, design and scientific approach. A local LLM (qwen3:4b through Ollama) generates the narrative explanations inside the app; it is constrained to numbers computed by the digital twin, with an automatic number-grounding check and a template fallback. The neural emulator was designed and trained by the team on our own simulations. The screenshots are real captures of the app; no AI-generated images or video are used.

---

## NASA Data *

Una fila por dato (Link Text → Link Url):

| Link Text | Link Url |
|---|---|
| NASA POWER Daily API (Agroclimatology, 1995–2024) | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| NASA POWER Climatology (incl. GWETROOT root-zone soil wetness) | https://power.larc.nasa.gov/docs/services/api/temporal/climatology/ |
| NASA POWER Data Access Viewer | https://power.larc.nasa.gov/data-access-viewer/ |

Opcional, porque está implementado pero no se usó en los resultados. Si lo pones, agrega "(integration implemented, not used in reported results)":

| Link Text | Link Url |
|---|---|
| SMAP L4 Soil Moisture (SPL4SMGP) – integration implemented | https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008 |
| GPM IMERG V07 – integration implemented | https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07 |
| MODIS MOD13Q1 NDVI – integration implemented | https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1 |

---

## Space Agency Partner & Other Data

| Link Text | Link Url |
|---|---|
| ISRIC SoilGrids v2.0 | https://soilgrids.org |
| USDA NRCS SSURGO – Soil Data Access | https://sdmdataaccess.sc.egov.usda.gov |
| USDA NASS Cropland Data Layer (CropScape) | https://nassgeodata.gmu.edu/CropScape/ |
| FAO-56 Crop Evapotranspiration (Allen et al., 1998) | https://www.fao.org/4/x0490e/x0490e00.htm |
| Esri World Imagery basemap | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 |
| Ollama + Qwen3 4B | https://ollama.com/library/qwen3 |
| PyTorch | https://pytorch.org |
| React Three Fiber | https://github.com/pmndrs/react-three-fiber |
| MapLibre GL JS | https://maplibre.org |
| FastAPI | https://fastapi.tiangolo.com |

---

## Verificación final
- [ ] Agree to Terms and Conditions
- [ ] Confirm All Work is Original
- [ ] Probar los dos links en incógnito
- [ ] **Submit for Judging antes de las 23:59**
