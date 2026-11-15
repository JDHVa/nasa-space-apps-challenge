# Field Shift: Adapting Farms with NASA Data
## Informe de investigación profunda (NASA Space Apps Challenge 2026)

Fecha de elaboración: 2026-11-15

---

## 0. Resumen ejecutivo

- **El reto** pide una herramienta de apoyo a la decisión que combine observaciones de la Tierra de NASA con información local de suelos, características de cultivos y prioridades del agricultor, para que el productor pruebe **rotaciones de cultivos** que mejoren la salud del suelo y se adapten a condiciones cambiantes. **No pude acceder a la página oficial** (spaceappschallenge.org) ni por WebFetch ni por PowerShell: ambos fallan con errores de certificado TLS. La descripción procede de fuentes secundarias (ver sección 1).
- **El espacio ya está saturado de proyectos "rotación + POWER"**: al menos 10 equipos publicaron en GitHub propuestas muy similares (FarmStack, FieldShift-NASA, RotaShift, ESM-FieldShift, BlinkFarms, space2earth-field-shift, entre otros). La diferenciación tendrá que venir de **incertidumbre explícita, detección de sequía/ventana de siembra con datos satelitales, enfoque en español/Latinoamérica y/o una capa de IA no trivial**.
- **Datos clave y accesibles en 48 h**: NASA POWER (API sencilla, reanálisis diario desde 1981), GPM IMERG (Early con ~4 h de latencia), SMAP L4 humedad del suelo raíz (9 km, 3 h, latencia ~2.5 días), HLS (30 m, 2–4 días de latencia), NEX-GDDP-CMIP6 (proyecciones diarias 0.25°, 1950–2100), AlphaEarth Satellite Embeddings (64 dimensiones, 10 m, anuales, en Google Earth Engine).
- **IA más prometedora para este reto (relación impacto/viabilidad)**:
  1. Modelos híbridos proceso + ML (APSIM/AquaCrop + gradient boosting) con **intervalos de predicción conformes**.
  2. **Búsqueda de análogos climáticos** con embeddings de Earth foundation models (AlphaEarth, Clay, Prithvi): "¿qué lugar de hoy se parece al clima que tendrá mi campo en 2050?".
  3. Agente LLM en español con herramientas sobre CMR/POWER (el servidor MCP oficial de NASA para CMR existe).
- **SNN (redes neuronales de pulsos)**: madurez baja para este problema. No encontré un artículo de 2025 que aplique SNN a clasificación de series temporales de teledetección agrícola. Solo sirven como demo de eficiencia energética en hardware neuromórfico; **no recomendadas como núcleo** para 48 h.

---

## 1. El reto y su verificación

### 1.1 Estado de la verificación

| Elemento | Estado |
|---|---|
| Página oficial `spaceappschallenge.org/2026/challenges/` | **No accesible** desde mis herramientas (error TLS "unable to get local issuer certificate" en WebFetch y "No se puede establecer una relación de confianza" en PowerShell). **No verificado directamente.** |
| Título "Field Shift: Adapting Farms with NASA Data" | Confirmado por varias fuentes secundarias y por la búsqueda, que menciona que una de ellas reproduce la página oficial de 2026. |
| Fechas del evento | Secundarias: 14–15 nov 2026 (registro Internshala). |
| Dificultad | Secundaria: intermedia a avanzada (listado de un Space Apps de Nepal). |
| Lista de datasets oficiales | **No verificada.** Lo que sigue son los recursos que usan los equipos que publicaron proyectos, no necesariamente la lista oficial. |

Fuentes consultadas:
- Romania Journal, listado de los 14 retos 2026: https://www.romaniajournal.ro/society-people/science/nasa-space-apps-challenge-2026-launches-14-global-challenges/
- Internshala, registro: https://internshala.com/competitions/nasa-international-space-apps-challenge-2026-registration/
- Nepvents, evento 2026: https://www.nepvents.com/events/cmvp131cy0000qtidqmehjx9h
- Página oficial de retos 2026 (no accesible): https://www.spaceappschallenge.org/2026/challenges/
- FarmStack (anirban-islam), proyecto del reto: https://github.com/anirban-islam/farmstack

**Acción recomendada para el equipo**: abrir la página oficial en un navegador normal (el problema es del entorno de esta investigación) y contrastar las secciones 1.2 y 1.3 antes de fijar el concepto.

### 1.2 Objetivo y outputs (según fuentes secundarias)

Descripción consistente en varias fuentes:
- Construir una **herramienta de apoyo a la decisión** (decision-support tool).
- Entradas: observaciones NASA de la Tierra + información de suelos local + características de cultivos + prioridades del agricultor.
- Resultado esperado: que el agricultor **pruebe rotaciones de cultivos** que mejoren la salud del suelo y se adapten a condiciones cambiantes (estacionalidad que "ya no llega a tiempo", sequía, déficit de humedad).

Outputs típicos que los equipos publicaron (no confirmados como requisito oficial): comparación de escenarios de rotación, calendario de siembra, alertas de sequía, visualizaciones, y documentación de la fuente de cada dato.

### 1.3 Recursos NASA y socios que aparecen en los proyectos del reto

| Recurso | Uso reportado | Fuente |
|---|---|---|
| NASA POWER | Presente en casi todos los proyectos (clima diario) | https://github.com/sagar25446-prog/FieldShift-NASA ; https://github.com/XtremeseOISHEE/RotaShift |
| SMAP L4 humedad del suelo | Humedad de raíz; alerta de déficit de germinación | https://github.com/ethiomaths2-ctrl/ESM-FieldShift ; búsqueda de equipos 2026 |
| GPM IMERG | Sequía histórica y frecuencia de eventos extremos | Búsqueda de equipos 2026 |
| MODIS NDVI, ECOSTRESS, HLS | Verdor y evapotranspiración | https://github.com/samuelakosaonyejekwe/fieldshift ; https://github.com/umar-essayed/BlinkFarms-NASA-SpaceApps |
| NASA Earthdata CMR, NASA GIBS | Descubrimiento de datos y teselas | https://github.com/anirban-islam/farmstack |
| GRACE-FO, FLDAS/GLDAS | Agua subterránea / modelos de superficie | Búsqueda de equipos 2026 |
| SoilGrids | Suelos globales | Búsqueda de equipos 2026 (FarmStack) |

---

## 2. Trabajo previo

### 2.1 Retos de Space Apps anteriores en agricultura

- **2024 (ganadores globales)**: NASA anunció 10 ganadores globales de 9.996 proyectos. Uno, *GaamaRamma*, buscaba que los agricultores gestionaran la disponibilidad de agua en sequía, plagas y enfermedades. https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-international-space-apps-challenge-announces-2024-global-winners/
- **2024 Galactic Impact Award**: Nave Analytics (Nebraska) y VITech (Ucrania) ganaron con una herramienta de **ventana de siembra** ("2Plant or not 2Plant") que usa humedad del suelo, predicción meteorológica y datos satelitales. Es el antecedente más directo de "decidir cuándo sembrar". https://siliconprairienews.com/2025/02/nebraska-startup-wins-nasas-galactic-impact-award-in-the-2024-space-apps-challenge/ ; https://vitechteam.com/blog/how-vitech-s-agtech-innovation-won-the-nasa-space-apps-challenge
- **2024 reto de agua agrícola**: "herramienta para explorar, analizar y usar datasets NASA sobre preocupaciones hídricas". Equipo de agricultura: https://www.spaceappschallenge.org/nasa-space-apps-2024/find-a-team/agri-vision/
- **2021**: una app de equipo fue adoptada por el Ministerio de Agricultura de Colombia para conectar pequeños productores con compradores locales (fuente secundaria: resultados de búsqueda).
- **2023 y 2025**: **no encontré** ganadores de agricultura/sequía verificables. Confirmar en los listados oficiales de Space Apps.

**Lección**: los ganadores agrícolas valoran un **resultado accionable para el productor** (cuándo sembrar, qué sembrar, cuánta agua) más que un mapa bonito.

### 2.2 Herramientas existentes

| Herramienta | Qué hace | Limitación para Field Shift | Fuente |
|---|---|---|---|
| **NASA Harvest** | Consorcio de más de 50 socios que aplica observación de la Tierra a agricultura y seguridad alimentaria. Plataforma Harvest2Market (EO + mercados). | Orientada a análisis regional y mercados, no a decisiones de finca. | https://www.nasaharvest.org/news/launch-of-updated-harvest2market-agricultural-supply-chains-monitoring-tool |
| **NASA Acres** | Consorcio nacional (EE. UU.) de agricultura; dashboards que dependen del aporte de productores. | Enfocado a EE. UU. | Taller LEAD Maryland 2025: https://climate.umd.edu/the-future-of-agriculture-includes-satellites-and-ai-5-lessons-learned-from-the-2025-lead-maryland-workshop/ |
| **GEOGLAM Crop Monitor** | Evaluaciones mensuales por consenso de condición de cultivos; cubre >97% de tierras de cultivo. | Escala global/mensual; no da recomendaciones de finca. | https://www.nasaharvest.org/news/2025-geoglam-crop-outlook-what-to-expect-for-wheat-maize-and-soybeans ; https://geoglam.org/ag-monitoring/ |
| **OpenET** | Ensamble de 6 modelos de evapotranspiración a 30 m (Landsat): ALEXI/DisALEXI, eeMETRIC, geeSEBAL, PT-JPL, SIMS, SSEBop. Licencia CC-BY-4.0 (SSEBop). En cultivos: MAE ~15.8 mm/mes. | Cobertura temporal fragmentada según el catálogo (ensamble con datos hasta 2024-12 en v2.0; geeSEBAL v2.1 hasta 2026-02). Sin pronóstico. | https://developers.google.com/earth-engine/datasets/catalog/OpenET_ENSEMBLE_CONUS_GRIDMET_MONTHLY_v2_0 ; https://developers.google.com/earth-engine/datasets/catalog/OpenET_SSEBOP_CONUS_GRIDMET_MONTHLY_v2_0?hl=he |
| **Microsoft FarmVibes.AI** | Código abierto (oct 2022) de modelos multimodales para agricultura: ejecución local con operadores y flujos; fusión dron/satélite/sensores; descargadores de datos. | Componentes FarmVibes.Connect y .Edge anunciados y no verificados como publicados; mantenimiento reciente incierto. | https://microsoft.github.io/farmvibes-ai ; https://www.microsoft.com/en-us/research/wp-content/uploads/2022/11/farmvibes_intro.pdf |
| **CropWatch (China)** | Boletín de monitoreo de cultivos, citado junto a Crop Monitor. | Sin detalles verificados de métodos en esta búsqueda. | Resultado de búsqueda GEOGLAM |
| **FAO Crop Calendar** | Calendarios de siembra y cosecha por país, cultivo y zona agroecológica (incluye Chile, Colombia, Ecuador). | No usa NASA; sin clima en tiempo real ni escenarios. | https://agritechobservatory.review.fao.org/en/crop-calendar |
| **SIMA (Argentina) + NASA Harvest** | Función de predicción de rendimiento en app de agricultores, con datos satelitales. | Enfocada en rendimiento, no en sequía ni calendario. | Resultado de búsqueda Latinoamérica |
| **NicaAgua (Nicaragua)** | App móvil con pronósticos a corto/medio plazo para planificar siembra y cosecha; alertas de inundación. | No usa NASA; no encontré versión con sequía en español vinculada a NASA. | https://www.scu.edu/engineering/labs--research/labs/frugal-innovation-hub/water-climate-lab/central-america/forecasting-app/ |
| **Agrosmart (Brasil)** | Sensores y satélite para recomendar riego y fertilización; reportan >100.000 agricultores en LatAm. | Comercial; no open data. | Resultado de búsqueda Latinoamérica |

### 2.3 Literatura académica relevante

- **Diversidad de cultivos y adaptación (Nature Food, 2025)**: Heikonen et al. evalúan la idoneidad climática de 30 cultivos bajo 1.5–4 °C. La diversidad potencial aumenta en latitudes medias-altas y disminuye en bajas. Volumen 6, páginas 331–342. https://www.nature.com/articles/s43016-025-01135-w
- **Siembra temprana no siempre basta (Communications Earth & Environment, 2025)**: en trigo de primavera de EE. UU., la siembra temprana (para desplazar la temporada a periodos más frescos) se sobrestima como adaptación en los modelos de cultivo. Muy relevante para "ventana de siembra". https://www.nature.com/articles/s43247-025-02716-0
- **Impacto del cambio climático con adaptación (Nature, 2025)**: Hultgren et al. proyectan pérdidas de rendimiento aun contando la adaptación de los agricultores. Nature 630. Fuente: https://aces.illinois.edu/news/climate-change-cuts-global-crop-yields-even-when-farmers-adapt
- **Modelos híbridos proceso + ML**:
  - Revisión 2025 (Agriculture): los híbridos APSIM+redes neuronales y DSSAT+gradient boosting tienen mejor desempeño en su comparación (R² promedio 0.91; los valores son agregados de la propia revisión). https://doi.org/10.3390/agriculture15232438
  - Dryland wheat 2024 (Agronomy): usar salidas de APSIM como variables de entrada de ML supera a APSIM y a 12 modelos ML puros; el mejor fue un ensamble ponderado por error. https://doi.org/10.3390/agronomy14040777
  - Corn Belt (PMC): añadir variables de APSIM como entrada redujo el error de predicción de rendimiento en ~7–20%. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7810832/
  - AgriPINN (arXiv 2026): red neuronal informada por procesos para biomasa bajo estrés hídrico (no revisado a fondo). https://arxiv.org/pdf/2601.16045
- **Riego con RL**: PPO acoplado a AquaCrop-OSPy, con resultados cercanos al óptimo con "oráculo" sin pronóstico (EGU 2026); un caso de invernadero con ~15% menos riego que la regla de AquaCrop (2026). https://meetingorganizer.copernicus.org/EGU26/EGU26-21783.html ; Gym-DSSAT y CyclesGym como entornos de RL para fertilización y riego. Fuentes: resultados de búsqueda; casi todo son preprints o tesis.
- **Conformal en rendimiento**: un artículo de 2026 (MDPI *Information*, HSE-GNN-CP) muestra que los bootstrap sufren de baja cobertura en rendimiento (40% frente al 80.7% nominal con CQR). https://www.mdpi.com/2078-2489/17/2/141

### 2.4 Otros proyectos del reto 2026 (para diferenciarse)

- FieldShift-NASA (POWER, planificación de rotación con transparencia): https://github.com/sagar25446-prog/FieldShift-NASA
- RotaShift (Bangladesh; ventana de calendario frente a 22 años de lluvia de POWER/MERRA-2): https://github.com/XtremeseOISHEE/RotaShift
- BlinkFarms (detección temprana de sequía flash con SMAP, IMERG, memoria de campo): https://github.com/umar-essayed/BlinkFarms-NASA-SpaceApps
- ESM-FieldShift (SMAP, IMERG, rotación): https://github.com/ethiomaths2-ctrl/ESM-FieldShift
- space2earth-field-shift (bilingüe inglés/urdu, POWER): https://github.com/shahkhalid030056-prog/space2earth-field-shift
- Crop Care (PWA para agricultores bangladesíes): https://github.com/mdshirajulislam/crop-care-nasa-spaceapps-2026
- FarmStack (CMR, POWER, GIBS, SoilGrids): https://github.com/anirban-islam/farmstack
- Otros: fieldshift (samuelakosaonyejekwe), farmshift (xosirat), Field-Shift (ALBOU517, Nilkamal21).

---

## 3. Catálogo de datos NASA y complementarios

Los valores marcados con "(verificado)" provienen de las fuentes citadas. Los marcados con "(no verificado)" no los pude confirmar en esta investigación y deben comprobarse en la documentación de cada producto.

| Fuente | Qué ofrece | Resolución | Latencia | Acceso | Notas |
|---|---|---|---|---|---|
| **SMAP L4 (SPL4SMGP)** | Humedad superficial (0–5 cm) y de raíz (0–100 cm); meta de error no sesgado de 0.04 m³/m³ | 9 km, 3 horas, desde 31-mar-2015 (verificado) | ~2.5 días (verificado) | NSIDC, Earthdata; versión 8 es la más reciente (verificado) | Ideal para déficit de humedad de raíz. https://nsidc.org/data/spl4smgp/versions/7 ; https://doi.org/10.5067/9LNYIYOBNBR5 |
| **GPM IMERG** | Precipitación casi global | 0.1°, 30 min (verificado) | Early ~4 h; Late ~12–14 h; Final ~3–3.5 meses (verificado, con discrepancia entre fuentes) | Earthdata/GES DISC | Early/Late para tiempo real; Final para investigación. https://gpm.nasa.gov/data/IMERG |
| **HLS (HLSL30/HLSS30)** | Landsat + Sentinel-2 armonizados | 30 m; revisita combinada ~2–3 días (verificado) | 2–4 días (verificado, con discrepancia) | LP DAAC, COG; también Google Earth Engine | Base para NDVI/EVI de campo. https://www.earthdata.nasa.gov/data/projects/hls |
| **MODIS / VIIRS (NDVI, EVI, LST)** | Verdor y temperatura de superficie | 250 m–1 km (no verificado en esta búsqueda) | Días (no verificado) | LP DAAC, AppEEARS | Serie histórica larga para anomalías. |
| **ECOSTRESS (ET y estrés hídrico)** | Evapotranspiración y estrés, muy alta resolución | 70 m (verificado), entre 52°N y 52°S; sigue el paso de la ISS | No hay cifra verificada | LP DAAC, Earthdata | Muestreo irregular; difícil como serie diaria. https://data.nasa.gov/dataset/ecostress-gridded-evaporative-stress-index-pt-jpl-instantaneous-l4-global-70-m |
| **GRACE-FO (agua subterránea)** | Anomalías de almacenamiento de agua | ~300 km efectivos; mensual (verificado) | Semanas a meses (no verificado) | JPL, GFZ | Muy grueso para una finca; útil como contexto regional. https://grace.jpl.nasa.gov/data/get-data/monthly-mass-grids-land |
| **NASA POWER (AG / daily)** | Clima diario: temperatura, precipitación, radiación, humedad, viento, y variables agroclimáticas (ICASA para modelos de cultivo) | 0.5° en rejilla; punto con API; desde 1981 (verificado) | Actualización NRT, sin cifra específica (verificado) | API `power.larc.nasa.gov/api/temporal/daily/point` y `regional`; máximo 20 parámetros por punto | Base del reto. Limitado en nº de parámetros y por bloqueo ante peticiones repetidas. https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| **NEX-GDDP-CMIP6** | Proyecciones diarias bias-corregidas; tmax, tmin, precipitación, humedad; SSP1-2.6 a SSP5-8.5 | 0.25° (~25 km), 1950–2100 (verificado) | No aplica | AWS S3, THREDDS del NCCS | 35 GCM. Licencia: CC0 según nota técnica de 2022, pero otras fuentes indican CC-BY-SA 4.0: verificar. Tamaño de 18 a 38 TB según fuente. https://www.nccs.nasa.gov/services/data-collections/land-based-products/nex-gddp-cmip6 ; https://doi.org/10.1038/s41597-022-01393-4 |
| **Earthdata CMR / Harmony / AppEEARS** | Búsqueda de metadatos, subsetting en la nube, extracción de puntos y áreas | Depende del producto | Inmediata (API) | CMR: `cmr.earthdata.nasa.gov`; servidor MCP oficial `nasa/earthdata-mcp`; AppEEARS: `appeears.earthdatacloud.nasa.gov/api/`; Harmony: harmony.earthdata.nasa.gov | Documentación de CMR no encontrada en la búsqueda. https://github.com/nasa/earthdata-mcp ; https://www.earthdata.nasa.gov/data/tools/appeears |
| **AlphaEarth Foundations (Satellite Embeddings)** | Vector de 64 dimensiones por píxel, resumen anual | 10 m (verificado); cobertura 2017–2024/2025 (fuentes discrepan) | Anual | Earth Engine `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`; COG en GCS | Clave para análogos climáticos. https://developers.google.com/earth-engine ; https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/ |
| **OpenET (ensamble)** | ET mensual a 30 m | 30 m; mensual | Varía | Earth Engine | Ver tabla 2.2 para cobertura. |
| **Sentinel-2 / Sentinel-1 (Copernicus)** | Óptico y radar | 10 m; 6–12 días (no verificado) | Días | Copernicus Data Space | Complemento a HLS. |
| **ERA5 (ECMWF)** | Reanálisis horario global | ~31 km (no verificado) | ~5 días (no verificado) | Copernicus CDS | Alternativa a POWER para clima horario. |
| **SoilGrids (ISRIC)** | Propiedades de suelo globales | 250 m (no verificado) | Estático | REST / descarga | Mencionado por FarmStack. |
| **FAOSTAT** | Estadísticas de producción y área | País/año (no verificado) | Anual | API | Para validar rendimientos regionales. |

---

## 4. Gaps: lo que las herramientas actuales no hacen bien

1. **Recomendación accionable para la finca**: Harvest, Crop Monitor y OpenET miden o describen; casi ninguno traduce a "siembra esta semana, este cultivo, este riego".
2. **Escala local con proyecciones**: NEX-GDDP tiene 0.25° (~25 km). Para una parcela, falta downscaling o un modelo de paisaje; los trabajos de difusión lo intentan, pero no hay herramienta abierta lista para usar.
3. **Incertidumbre comunicada**: la mayoría de tableros dan un número sin intervalo. Ningún proyecto del reto encontrado publica intervalos calibrados.
4. **Conexión limitada**: pocas herramientas funcionan sin conexión. FarmVibes.Connect (conectividad rural) se anunció pero no encontré que esté publicado.
5. **Español y Latinoamérica**: las herramientas NASA son en inglés; NicaAgua y FAO Crop Calendar son regionales pero sin NASA; la mayoría de proyectos del reto son de Bangladesh, Etiopía o Nepal.
6. **Sequía flash y ventanas de siembra con SMAP**: SMAP se usa en varios proyectos, pero con reglas simples. Un modelo que combine humedad de raíz, pronóstico corto y calendario del cultivo con incertidumbre sería diferenciador.
7. **Explicabilidad y trazabilidad de fuentes**: FieldShift-NASA hace esto explícitamente; es un punto a igualar.

---

## 5. Enfoques de IA para Field Shift

Evaluación: **viabilidad en 48 h** (alta / media / baja), **cómputo** y **impacto de demo**. "Wow" indica el efecto esperado en jueces.

### 5.1 Foundation models de observación de la Tierra

| Modelo | Qué es | Por qué encaja | Código / pesos | Cómputo | Viabilidad | Wow |
|---|---|---|---|---|---|---|
| **Prithvi-EO-2.0** (NASA-IBM) | Modelo multitemporal de observación de la Tierra, 300M y 600M parámetros | Tiene conjunto de datos de segmentación de cultivos en EE. UU. y un benchmark GEO-Bench. Útil para clasificar tipos de cultivo en HLS | Hugging Face (publicado 4-dic-2024), TerraTorch, repo NASA-IMPACT. Las cifras de mIoU encontradas (50.7% en cultivos EE. UU., 600M) vienen de una página personal; verificar en el paper | GPU para afinar; inferencia en CPU para 300M con pocos parches | Media | Alta (es de NASA) |
| **AlphaEarth Foundations Satellite Embeddings** | Embeddings de 64 dimensiones a 10 m, anuales, en Earth Engine | Búsqueda de análogos: "parcelas con firma espectral similar" o "lugares de hoy con el clima de 2050" (combinado con NEX-GDDP). No requiere entrenar | Earth Engine y COG en GCS | Mínimo (es un dataset) | **Alta** | **Muy alta** |
| **Clay** | Modelo abierto (datos abiertos) con embeddings de 768 dimensiones por chip | Alternativa a AlphaEarth con licencia clara; buen para clasificación con pocos datos | Hugging Face, Development Seed | GPU ligera | Alta | Media |
| **OlmoEarth** (Ai2, nov-2025) | Familia de modelos de observación de la Tierra con código, datos y pesos | Reporta mejor desempeño que Clay y Galileo en su benchmark (autoreportado) | Código y pesos publicados según Ai2 | GPU | Media | Media |
| **SatMAE / Galileo** | MAE para imágenes satelitales multiespectrales y temporales | Referencia académica; más pesado para el reto | Varios repos | GPU | Baja-media | Baja |

Fuentes: https://www.alphaxiv.org/abs/2412.02732v3 ; https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL-Sen1Floods11 ; https://developmentseed.org/projects/clay/ ; https://allenai.org/blog/olmoearth-models ; https://arxiv.org/pdf/2601.00857 (AlphaEarth en agricultura: benchmark en tareas agrícolas).

### 5.2 Modelos del tiempo y "world models" para escenarios

| Modelo | Qué es | Encaje | Pesos | Cómputo | Viabilidad | Wow |
|---|---|---|---|---|---|---|
| **Aurora (Microsoft)** | Modelo del sistema terrestre; Aurora 1.5 con 22 variables, horario y ensamble probabilístico | Pronóstico de 1–10 días para decisiones de siembra; no sirve para escenarios climáticos largos | MIT según una fuente (verificar); checkpoints en Hugging Face | GPU para inferencia; pesado | Baja-media | Alta |
| **WeatherNext 2 (Google DeepMind)** | Modelo de pronóstico, según Earthmover, de código abierto; 18 pesos, ~11.4 GiB | Igual que Aurora | Bucket de Google y espejo en Hugging Face (CONGG/weathernext-weight) | GPU | Baja-media | Alta |
| **GenCast** | Pronóstico probabilístico por conjuntos | Igual que lo anterior; útil para incertidumbre | Pesos y licencia **no verificados** en esta investigación | GPU | Baja | Alta |
| **Prithvi WxC** | Modelo meteorológico de NASA-IBM | Tiene vínculo con downscaling (un paper lo usa como condicionante) | Hugging Face | GPU | Baja | Media |

Fuentes: https://www.microsoft.com/en-us/research/blog/aurora-1-5-extending-open-foundation-models-for-weather-and-earth-system-applications/ ; https://www.earthmover.io/blog/making-open-source-ai-weather-forecasting-models-easy-to-run ; https://pypi.org/project/weathernext-download/0.1.7/

**Lectura**: un "world model" de finca completo (simular la finca día a día con física y IA) no cabe en 48 h. Lo factible es un **modelo de escenarios** que usa modelos de cultivo existentes como simulador y un surrogate ML para velocidad.

### 5.3 Modelos híbridos proceso + ML (física informada)

- **Qué es**: un simulador de cultivo (APSIM, DSSAT, WOFOST, AquaCrop) da variables físicas; un modelo ML aprende la corrección o el rendimiento.
- **Por qué encaja**: el reto pide "probar rotaciones"; el simulador responde ante escenarios que no se han observado, y el ML lo hace rápido e interpretable.
- **Evidencia**: mejoras de 7–20% en error reportadas (ver 2.3).
- **Código**: AquaCrop-OSPy (Python), gym-DSSAT, CyclesGym; APSIM tiene interfaz Python.
- **Cómputo**: CPU.
- **Viabilidad**: **media-alta** si se usa AquaCrop-OSPy o un modelo sencillo y se entrenan 1–2 modelos ML pequeños.
- **Wow**: medio-alto ("la IA se apoya en física, no es caja negra").

### 5.4 Redes neuronales de operadores (FNO) y difusión para downscaling

- **Qué es**: FNO aprende mapas entre campos a cualquier resolución; los modelos de difusión generan campos finos condicionados a un campo grueso.
- **Evidencia**: difusión condicionada supera a CNN/GAN en precipitación extrema según revisiones de arXiv; un trabajo de 2026 (JGR: ML) aplica difusión a un emulador climático para recuperar lluvia orográfica en el subcontinente indio. Un trabajo de 2608.25858 condiciona difusión con Prithvi WxC.
- **Lo que no encontré**: un trabajo que aplique FNO+difusión al downscaling de proyecciones CMIP para precipitación agrícola.
- **Código**: se encuentra en arXiv y repos académicos; no investigué repos concretos.
- **Cómputo**: GPU para entrenar; en 48 h, solo factible como prueba de concepto con datos pequeños.
- **Viabilidad**: **baja** para entrenar; **media** para usar pesos preentrenados si existen. Fuente: https://arxiv.org/html/2602.13416 ; https://arxiv.org/html/2608.25858v1

### 5.5 Redes neuronales de pulsos (SNN) y hardware neuromórfico

- **Qué es**: redes que se comunican con pulsos en el tiempo; consumen energía solo cuando "disparan".
- **Madurez para este caso**:
  - **No encontré** un paper de 2025 que aplique SNN a clasificación de series temporales de teledetección agrícola. Sí hay una SNN para predicción de rendimiento con MODIS de 2016 (IEEE TGRS 54(11)): https://ieeexplore.ieee.org/document/7524771/similar
  - Hay resultados de energía sólidos en Loihi 2 frente a GPU/Jetson (hasta 18x más rápido y 250x menos energía en clasificación, según un paper de 2025 con pipeline GPU→Loihi 2 de Mészáros et al.), pero son benchmarks de tareas de visión, no de agricultura.
  - **Fricción de herramientas**: pasar de snnTorch a Loihi 2 exige neuronas en microcódigo y cuantización de punto fijo (tesis del Politécnico de Turín). Lava es el camino nativo; Norse sin datos claros.
  - Ejemplo de SNN con PyTorch y Lava: un SNN en Loihi con ANN en Jetson Nano (híbrido).
- **Viabilidad en 48 h**: **baja** para un sistema completo; **media** como demo de clasificación SNN en PC con snnTorch sobre una serie NDVI o humedad. Hardware neuromórfico no disponible para un equipo típico.
- **Wow**: alto en el discurso (energía en el campo, sin nube), bajo en resultados demostrables.
- **Recomendación**: si el equipo quiere SNN, plantearla como **línea de trabajo futura de hardware en campo**, no como núcleo de la predicción.

Fuentes: https://arxiv.org/pdf/2505.11418 (energía de SNN para aplicaciones espaciales); https://webthesis.biblio.polito.it/38652/1/tesi.pdf ; https://arxiv.org/html/2407.08704v1

### 5.6 Series temporales foundation models (TimesFM, Chronos, Moirai)

- **Qué son**: modelos preentrenados para pronosticar series sin entrenamiento adicional.
- **Evidencia**: en precios agrícolas de USDA (1997–2025), modelos zero-shot (Chronos, Chronos-2, TimesFM 2.5, Time-MoE, Moirai-2) superan a modelos entrenados desde cero; Time-MoE es el mejor en RMSE. No encontré evaluaciones sobre rendimiento de cultivos o clima agrícola.
- **Encaje**: pronosticar humedad de suelo SMAP o lluvia IMERG a 2–4 semanas para alertas de sequía.
- **Cómputo**: CPU/GPU ligera.
- **Viabilidad**: **alta** (Chronos-Bolt o TimesFM por API). **Wow**: medio.
- Fuentes: https://arxiv.org/pdf/2601.06371 ; https://arxiv.org/pdf/2602.12147

### 5.7 Inferencia causal y contrafactuales ("¿qué pasa si cambio de cultivo?")

- **Qué es**: estimar el efecto de cambiar un cultivo sobre rendimiento, agua o suelo, controlando por clima y suelo, usando datos observados o simulados.
- **Estado**: la búsqueda no cubrió directamente este tema; la idea es general y se apoya en las evaluaciones de modelos híbridos.
- **Viabilidad**: **media**; más realista como **análisis observacional** con datos del reto (rendimientos de FAOSTAT o simulaciones) que como modelo causal completo.
- **Wow**: alto si se presenta con un "contrafactual" visual: "con maíz tras frijol, el déficit baja X%".

### 5.8 Aprendizaje por refuerzo (RL) para siembra y riego

- **Evidencia**: PPO con AquaCrop-OSPy (EGU 2026); reducción de ~15% de riego en un caso de invernadero (2026); Gym-DSSAT y CyclesGym como entornos.
- **Viabilidad en 48 h**: **baja** para entrenar bien; **media** si se usa un entorno existente y un agente simple. Para rotación de cultivos a largo plazo, el espacio de acciones es grande y el entrenamiento lento.
- **Wow**: alto ("la IA aprendió a regar").

### 5.9 Agentes LLM con datos NASA (RAG + herramientas)

- **Qué es**: un LLM que consulta POWER, CMR o un catálogo local y explica el resultado en español.
- **Infraestructura existente**: `nasa/earthdata-mcp`, servidor MCP oficial para CMR con herramientas get_collections, get_granules, get_services, etc. Ojo: el endpoint hospedado y las herramientas vienen de descripciones de terceros; verificar en el repo. Otros: `podaac/cmr-mcp` (oficial de PO.DAAC según Glama). https://github.com/nasa/earthdata-mcp ; https://github.com/podaac/cmr-mcp
- **Encaje**: explicación en lenguaje llano para agricultores; trazabilidad de cada dato a su fuente.
- **Riesgo**: alucinaciones de cifras. Mitigar haciendo que el LLM solo narre números que vengan de una herramienta.
- **Viabilidad**: **alta**. **Wow**: alto si es en español y offline (modelo local pequeño con tablas precargadas).

### 5.10 Predicción con incertidumbre (conformal prediction)

- **Qué es**: intervalos con cobertura garantizada (1 − α) bajo intercambiabilidad; CQR para regresión.
- **Evidencia**: CQR corrige cobertura de bootstrap de 40% a 80.7% (MDPI 2026); el riesgo es la autocorrelación espacial y los cambios de distribución entre regiones o años. Las versiones por grupo son la respuesta.
- **Viabilidad**: **alta** (paquete MAPIE o implementación de 30 líneas). **Wow**: medio-alto para jueces técnicos, porque responde a "¿qué tan seguro estás?".
- Fuentes: https://arxiv.org/pdf/2501.07185 ; https://www.mdpi.com/2078-2489/17/2/141

### 5.11 Otras técnicas

| Técnica | Estado en esta investigación | Viabilidad 48 h | Comentario |
|---|---|---|---|
| **Redes de grafos (GNN)** | No investigado en detalle; el paper HSE-GNN-CP (MDPI 2026) las usa para rendimiento global. | Media | Útiles si hay una red de parcelas o estaciones; sobredimensionado para el reto. |
| **KAN (Kolmogorov-Arnold Networks)** | No investigado en esta búsqueda. | Media-baja | Interpretabilidad de funciones; apoyo a explicabilidad, no principal. |
| **Aprendizaje federado** | No investigado en esta búsqueda. | Baja | Interesante para privacidad de datos de finca; costoso de montar. |
| **Diffusion / FNO** | Ver 5.4. | Baja (entrenar) | — |

---

## 6. Recomendaciones: conceptos de proyecto

Ordenados por **impacto × viabilidad × originalidad** (criterio cualitativo, a partir de la evidencia de esta investigación).

### Concepto 1 (recomendado): "Análogos climáticos para rotación": ¿dónde ya se parece mi clima futuro?

**Idea**: el agricultor elige su finca y el año objetivo (2030/2050). La herramienta busca **lugares actuales con clima y firma satelital parecidos al escenario futuro** usando AlphaEarth Embeddings y NEX-GDDP, y muestra qué rotaciones funcionan allí hoy. Responde a "adaptación" sin depender de simulaciones largas.

**Arquitectura**:
1. Entrada: ubicación, suelo (SoilGrids), cultivos actuales, prioridades (agua, suelo, ingreso).
2. Clima histórico: NASA POWER (1981–2025) para la finca.
3. Clima futuro: NEX-GDDP-CMIP6 (SSP2-4.5 / SSP5-8.5) en el punto, 0.25°, promedio de 3–5 GCM.
4. Análogos: para cada celda de la región, distancia entre su clima histórico y el clima futuro de la finca; firma satelital con AlphaEarth (64-d) para restringir a cobertura agrícola.
5. Rotaciones: para los análogos, tasa de éxito de cada rotación con datos observados (rendimiento FAOSTAT o simulación AquaCrop) y calendario de siembra.
6. Salida: ranking de rotaciones con **intervalo conforme (CQR)**, mapa de análogos y fuentes.

**Viabilidad**: alta. **Wow**: alto ("el futuro de tu campo existe hoy en algún lugar del mapa"). **Originalidad**: alta; no vi proyectos del reto que usen análogos.

### Concepto 2: Ventana de siembra y sequía con pronóstico y conformal

**Idea**: alerta diaria de "siembra sí/no" y "déficit de humedad de raíz en 14 días" combinando SMAP L4 (humedad de raíz), IMERG (lluvia), POWER (temperatura) y un pronóstico de series temporales (Chronos/TimesFM), con intervalos conformes. Se distingue de BlinkFarms y de la ventana de siembra de 2024 por el intervalo calibrado.

**Arquitectura**: SMAP + IMERG + POWER → features por finca → Chronos-Bolt (zero-shot) para la serie de humedad → CQR sobre el error histórico → reglas de siembra (ventana térmica + humedad) → tablero simple.

**Viabilidad**: alta. **Wow**: medio-alto. **Originalidad**: media (el concepto existe en 2024 y en BlinkFarms, la novedad está en el intervalo).

### Concepto 3: Simulador de rotación híbrido (física + ML) con contrafactuales

**Idea**: "¿qué pasa si cambio de cultivo?". AquaCrop-OSPy (o un modelo sencillo) simula agua y rendimiento; un surrogate ML aprende en segundos; la app muestra el contrafactual del déficit hídrico y del balance de suelo por rotación.

**Arquitectura**: POWER → entrada de AquaCrop-OSPy (suelo y cultivo) → 1000–5000 simulaciones → ML (GBM) como surrogate → contrafactuales por rotación → conformal.

**Viabilidad**: media-alta. **Wow**: medio-alto. **Originalidad**: media-alta.

### Concepto 4: Asistente en español con datos NASA, offline

**Idea**: un asistente de voz o texto en español que responde "¿cuándo siembro frijol en mi zona?" usando un paquete de datos precargado (POWER, IMERG, SMAP, calendarios FAO) y un LLM pequeño que solo narra cifras que vienen de herramientas.

**Arquitectura**: descarga previa (CMR/POWER) → SQLite local → herramientas (consulta, calendario, riesgo) → LLM local o API con restricción de cifras → PWA sin conexión.

**Viabilidad**: alta. **Wow**: alto por accesibilidad, medio por novedad técnica. **Originalidad**: alta en Latinoamérica.

**Combinación sugerida**: Concepto 1 como núcleo, Concepto 2 como alerta, Concepto 4 como interfaz. Concepto 3 si el equipo tiene experiencia con modelos de cultivo.

### Concepto 5 (exploratorio, baja viabilidad): SNN para alerta de sequía en campo

**Idea**: clasificador SNN (snnTorch) sobre series de humedad, con despliegue futuro en Loihi 2 o microcontrolador.

**Viabilidad**: baja (no hay madurez de herramientas ni hardware para 48 h). **Wow**: alto en el discurso. **Recomendación**: solo como demo de eficiencia con simulación de energía, no como resultado principal.

---

## 7. Flags y datos no verificados

1. **Página oficial del reto**: no accesible desde las herramientas de esta investigación (error TLS). El resumen del reto viene de fuentes secundarias y de proyectos de otros equipos. Verificar objetivos, entregables y lista de datasets en spaceappschallenge.org.
2. **Ganadores 2023 y 2025 de agricultura**: no encontrados.
3. **Latencias**: IMERG Late (12 vs 14 h) y HLS (2–3 vs 2–4 días) tienen discrepancias entre fuentes. ECOSTRESS y GRACE-FO: sin cifra de latencia verificada.
4. **Cobertura de AlphaEarth**: las fuentes dan 2017–2024 o 2017–2025.
5. **OpenET**: cobertura temporal discrepante entre catálogos.
6. **NEX-GDDP-CMIP6**: licencia (CC0 o CC-BY-SA 4.0) y tamaño (18–38 TB) con discrepancias.
7. **Prithvi-EO-2.0**: las cifras de mIoU vienen de una página personal; verificar en el paper.
8. **Aurora 1.5**: fecha de lanzamiento y licencia MIT vienen de fuentes secundarias.
9. **GenCast**: pesos y licencia no verificados.
10. **MODIS/VIIRS, Sentinel, ERA5, SoilGrids, FAOSTAT**: no investigados en detalle; los datos de la tabla 3 para estas fuentes no están verificados.
11. **FarmVibes**: no confirmé si los componentes Connect y Edge se publicaron.
12. **SNN**: no se encontró un paper de 2025 de SNN en teledetección agrícola; la madurez se valora por analogía con otros dominios.
13. **Causal ML, KAN, GNN, aprendizaje federado, RL para rotaciones**: evaluación cualitativa, sin fuentes específicas verificadas en esta investigación.
14. **Servidor MCP de Earthdata**: el endpoint hospedado y las herramientas proceden de listados de terceros; verificar en `github.com/nasa/earthdata-mcp`.
