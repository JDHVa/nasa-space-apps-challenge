from app.twin.crops import CROPS

MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
}

WHY = {
    "en": {
        "current": "Baseline: the rotation you entered, simulated against 30 years of NASA POWER weather and the NASA POWER root-zone wetness (GWETROOT) as starting soil water.",
        "cover_crop": "Fills the bare-soil window ({bare:.0f} days/yr in the current plan) with a legume or winter cover so the soil stays protected and nitrogen is fixed.",
        "low_water": "Swaps the thirstiest crops for lower-water-demand alternatives ({swaps}) to cut water use and drought exposure.",
        "double_crop": "Keeps living roots on the field most of the year: a rainy-season legume followed by a winter cereal.",
        "extra_a": "A drought-tolerant summer cereal followed by a winter legume cover to protect soil and add nitrogen.",
        "extra_b": "A rainy-season legume followed by a winter rye cover to reduce bare soil and erosion.",
    },
    "es": {
        "current": "Línea base: la rotación indicada, simulada con 30 años de clima NASA POWER y la humedad de zona radicular de NASA POWER (GWETROOT) como agua inicial del suelo.",
        "cover_crop": "Cubre la ventana de suelo desnudo ({bare:.0f} días/año en el plan actual) con una leguminosa o cobertura de invierno que protege el suelo y fija nitrógeno.",
        "low_water": "Sustituye los cultivos más demandantes de agua por alternativas de menor consumo ({swaps}) para reducir el uso de agua y la exposición a sequía.",
        "double_crop": "Mantiene raíces vivas la mayor parte del año: una leguminosa de temporal seguida de un cereal de invierno.",
        "extra_a": "Un cereal de verano tolerante a sequía seguido de una leguminosa de cobertura invernal que protege el suelo y aporta nitrógeno.",
        "extra_b": "Una leguminosa de temporal seguida de una cobertura de centeno invernal para reducir suelo desnudo y erosión.",
    },
}

TEXT = {
    "en": {
        "ev_power": "NASA POWER 1995-2024: {precip:.0f} mm/yr rain, {et0:.0f} mm/yr reference ET ({method}), {frost:.1f} frost days/yr, {heat:.1f} days/yr at or above 35 C.",
        "ev_smap": "NASA SMAP L4: root-zone soil moisture {smrz:.2f} m3/m3 and surface {sms:.2f} m3/m3 set the initial soil water of the twin.",
        "ev_gpm": "GPM IMERG V07: {gpm:.0f} mm/yr satellite rainfall cross-checks the POWER rainfall.",
        "ev_modis": "MODIS NDVI: minimum {nmin:.2f} in {mmin}, peak {nmax:.2f} in {mmax}; compared against twin canopy.",
        "ev_srtm": "SRTM: {slope:.1f} deg slope at {elev:.0f} m elevation drives the erosion slope factor.",
        "ev_grace": "GRACE-FO: terrestrial water storage anomaly of {grace:.1f} cm LWE (an anomaly relative to the mission mean, not a trend) hints at the regional groundwater buffer for irrigation.",
        "ev_delta": "Twin P50 vs current: water use {dw:+.0f} mm/yr, erosion {de:+.2f} t/ha/yr, N balance {dn:+.0f} kg/ha/yr, bare soil {db:+.0f} days/yr.",
        "ben_water": "Uses about {v:.0f} mm/yr less water than the current rotation.",
        "ben_irrig": "Needs about {v:.0f} mm/yr less supplemental irrigation.",
        "ben_n": "Improves the nitrogen balance by about {v:.0f} kg/ha/yr.",
        "ben_erosion": "Cuts modelled soil loss by {v:.0f}%.",
        "ben_bare": "Reduces bare-soil time by about {v:.0f} days/yr.",
        "ben_om": "Raises the soil organic matter index by {v:.1f} points over the horizon.",
        "ben_income": "Raises the relative income index by {v:.0f}%.",
        "ben_base": "Expected yield index {y:.0f}% of potential with {w:.0f} water-stress days/yr (P50).",
        "ben_similar": "Comparable overall performance with a different risk profile.",
        "gap_soil": "Soil texture and depth are assumed loam (field capacity 0.27, wilting point 0.12 m3/m3); local soil tests are needed.",
        "gap_mgmt": "No field data on fertilization, tillage, residue handling or irrigation access.",
        "gap_res": "NASA POWER (about 50 km grid) and a single soil-survey point are coarse compared with a single field.",
        "gap_price": "Income is a relative net index (generic price minus generic cost), not local market prices.",
        "gap_seed": "Seed availability, termination method and equipment for {crops} need local confirmation.",
        "risk_vuln": "{kind} risk in {month} (probability about {p:.0f}% in simulated years).",
        "risk_erosion": "Soil loss concentrates in {months} ({values} t/ha per month on average); the current rotation loses {current} t/ha in the same months.",
        "risk_deficit": "Seasonal water deficit equivalent to {v:.0f} mm/yr of supplemental water in the P50 case; check water availability.",
        "risk_n": "Negative nitrogen balance (P50 {v:.0f} kg/ha/yr): the soil nitrogen stock is being drawn down; plan fertilizer or legumes.",
        "risk_irrig": "Winter or dry-season crops may need about {v:.0f} mm/yr of irrigation in the P50 case; check water availability.",
        "risk_cover": "A cover crop can compete for stored soil water before the next main crop.",
        "risk_warm": "Under +2.5 C warming the P90 water-stress days reach {v:.0f} days/yr.",
        "risk_review": "Results are ranges from a simplified model; review with a local agronomist.",
        "et0_pm": "FAO-56 Penman-Monteith from POWER RH2M, WS2M and ALLSKY radiation",
        "et0_hg": "Hargreaves, humidity, wind and radiation not available",
        "ev_power_sm": "NASA POWER GWETROOT/GWETTOP (MERRA-2 soil wetness): root-zone {smrz:.2f} and surface {sms:.2f} m3/m3 equivalent set the initial soil water of the twin.",
        "ev_slope_only": "Terrain: {slope:.1f} deg slope at {elev:.0f} m elevation (soil survey slope and POWER elevation) drives the erosion slope factor.",
        "ev_soil": "Soil ({source}): {texture}, available water {awc:.0f} mm/m, hydrologic group {group} (bare curve number {cn:.0f}), K factor {k:.2f}, organic matter {om:.1f}%.",
        "ev_bands": "P10-P90 bands pool 40 weather members: 60% resampled historic years and 40% with +1.5 C or +2.5 C warming, so they mix climate variability with scenario uncertainty.",
        "ev_val_sm": "Validation: twin monthly relative soil moisture vs NASA POWER GWETROOT climatology gives R = {r:.2f}, MAE = {mae:.2f} (12 monthly means; GWETROOT is wetness versus saturation, so read it as a shape check).",
        "ev_val_ndvi": "Validation: twin canopy vs MODIS NDVI monthly climatology gives R = {r:.2f}, MAE = {mae:.2f}.",
        "gap_nosat": "No satellite products (SMAP, IMERG, MODIS, GRACE) are used for this site: initial moisture and elevation come from NASA POWER and there is no NDVI validation.",
        "gap_soil_point": "Soil comes from a single point of {source}; field soil tests (texture, depth, stoniness) are still needed.",
        "gap_irr_eff": "Irrigation need is the crop water deficit divided by an assumed 70% application efficiency.",
        "gap_cost": "Input costs are generic estimates; check USDA AMS Market News / local prices",
        "kinds": {"heat": "Heat", "frost": "Frost", "drought": "Drought", "waterlogging": "Waterlogging", "erosion": "Erosion"},
    },
    "es": {
        "ev_power": "NASA POWER 1995-2024: {precip:.0f} mm/año de lluvia, {et0:.0f} mm/año de ET de referencia ({method}), {frost:.1f} días de helada/año, {heat:.1f} días/año con 35 C o más.",
        "ev_smap": "NASA SMAP L4: humedad de zona radicular {smrz:.2f} m3/m3 y superficial {sms:.2f} m3/m3 fijan el agua inicial del suelo en el gemelo.",
        "ev_gpm": "GPM IMERG V07: {gpm:.0f} mm/año de lluvia satelital contrastan la lluvia de POWER.",
        "ev_modis": "MODIS NDVI: mínimo {nmin:.2f} en {mmin}, máximo {nmax:.2f} en {mmax}; se compara con el dosel del gemelo.",
        "ev_srtm": "SRTM: pendiente de {slope:.1f} grados a {elev:.0f} m de elevación define el factor de pendiente de la erosión.",
        "ev_grace": "GRACE-FO: anomalía de almacenamiento de agua terrestre de {grace:.1f} cm LWE (anomalía respecto a la media de la misión, no una tendencia) sugiere el amortiguamiento regional de agua subterránea para riego.",
        "ev_delta": "P50 del gemelo vs actual: uso de agua {dw:+.0f} mm/año, erosión {de:+.2f} t/ha/año, balance de N {dn:+.0f} kg/ha/año, suelo desnudo {db:+.0f} días/año.",
        "ben_water": "Usa unos {v:.0f} mm/año menos de agua que la rotación actual.",
        "ben_irrig": "Requiere unos {v:.0f} mm/año menos de riego complementario.",
        "ben_n": "Mejora el balance de nitrógeno en unos {v:.0f} kg/ha/año.",
        "ben_erosion": "Reduce la pérdida de suelo modelada en {v:.0f}%.",
        "ben_bare": "Reduce el tiempo de suelo desnudo en unos {v:.0f} días/año.",
        "ben_om": "Eleva el índice de materia orgánica en {v:.1f} puntos al final del horizonte.",
        "ben_income": "Eleva el índice relativo de ingreso en {v:.0f}%.",
        "ben_base": "Índice de rendimiento esperado de {y:.0f}% del potencial con {w:.0f} días de estrés hídrico/año (P50).",
        "ben_similar": "Desempeño general comparable con un perfil de riesgo distinto.",
        "gap_soil": "Textura y profundidad del suelo supuestas franca (capacidad de campo 0.27, punto de marchitez 0.12 m3/m3); se requieren análisis locales.",
        "gap_mgmt": "No hay datos de campo sobre fertilización, labranza, manejo de residuos ni acceso a riego.",
        "gap_res": "NASA POWER (malla de unos 50 km) y un solo punto de estudio de suelo son gruesos frente a una parcela.",
        "gap_price": "El ingreso es un índice relativo neto (precio genérico menos costo genérico), no precios locales.",
        "gap_seed": "Disponibilidad de semilla, método de terminación y equipo para {crops} requieren confirmación local.",
        "risk_vuln": "Riesgo de {kind} en {month} (probabilidad cercana a {p:.0f}% en los años simulados).",
        "risk_erosion": "La pérdida de suelo se concentra en {months} ({values} t/ha por mes en promedio); la rotación actual pierde {current} t/ha en los mismos meses.",
        "risk_deficit": "Déficit hídrico estacional equivalente a {v:.0f} mm/año de agua suplementaria en el caso P50; verifique la disponibilidad de agua.",
        "risk_n": "Balance de nitrógeno negativo (P50 {v:.0f} kg/ha/año): se está agotando el nitrógeno del suelo; planifique fertilizante o leguminosas.",
        "risk_irrig": "Los cultivos de invierno o secas pueden necesitar unos {v:.0f} mm/año de riego en el caso P50; verifique la disponibilidad de agua.",
        "risk_cover": "Una cobertura puede competir por el agua almacenada antes del siguiente cultivo principal.",
        "risk_warm": "Con +2.5 C de calentamiento, los días de estrés hídrico en P90 llegan a {v:.0f} días/año.",
        "risk_review": "Los resultados son rangos de un modelo simplificado; revíselos con un agrónomo local.",
        "et0_pm": "FAO-56 Penman-Monteith con RH2M, WS2M y radiación ALLSKY de POWER",
        "et0_hg": "Hargreaves, sin humedad, viento ni radiación disponibles",
        "ev_power_sm": "NASA POWER GWETROOT/GWETTOP (humedad de suelo MERRA-2): zona radicular {smrz:.2f} y superficial {sms:.2f} m3/m3 equivalentes fijan el agua inicial del suelo en el gemelo.",
        "ev_slope_only": "Terreno: pendiente de {slope:.1f} grados a {elev:.0f} m (pendiente del levantamiento de suelos y elevación de POWER) define el factor de pendiente de la erosión.",
        "ev_soil": "Suelo ({source}): {texture}, agua disponible {awc:.0f} mm/m, grupo hidrológico {group} (número de curva en desnudo {cn:.0f}), factor K {k:.2f}, materia orgánica {om:.1f}%.",
        "ev_bands": "Las bandas P10-P90 mezclan 40 miembros climáticos: 60% años históricos remuestreados y 40% con +1.5 C o +2.5 C de calentamiento, por lo que combinan variabilidad climática e incertidumbre de escenario.",
        "ev_val_sm": "Validación: la humedad relativa mensual del gemelo vs la climatología GWETROOT de NASA POWER da R = {r:.2f}, MAE = {mae:.2f} (12 medias mensuales; GWETROOT es humedad respecto a saturación, úsela como verificación de forma).",
        "ev_val_ndvi": "Validación: el dosel del gemelo vs la climatología mensual de NDVI MODIS da R = {r:.2f}, MAE = {mae:.2f}.",
        "gap_nosat": "No se usan productos satelitales (SMAP, IMERG, MODIS, GRACE) en este sitio: la humedad inicial y la elevación vienen de NASA POWER y no hay validación con NDVI.",
        "gap_soil_point": "El suelo proviene de un solo punto de {source}; aún se requieren análisis de suelo en campo (textura, profundidad, pedregosidad).",
        "gap_irr_eff": "La necesidad de riego es el déficit hídrico del cultivo dividido entre una eficiencia de aplicación supuesta de 70%.",
        "gap_cost": "Los costos de insumos son estimaciones genéricas; consulte USDA AMS Market News o precios locales.",
        "kinds": {"heat": "calor", "frost": "helada", "drought": "sequía", "waterlogging": "encharcamiento", "erosion": "erosión"},
    },
}


def _month_name(lang: str, month: int) -> str:
    return MONTHS[lang][month - 1]


def soil_evidence(soil: dict | None, lang: str) -> list[str]:
    if not soil:
        return []
    t = TEXT[lang]
    line = t["ev_soil"].format(
        source=soil["source"], texture=soil["texture"], awc=soil["awc_mm_per_m"], group=soil["hydrologic_group"],
        cn=soil["curve_number"], k=soil["k_factor"], om=soil["om_pct"],
    )
    return [line] + list(soil.get("notes", []))


def climate_evidence(site: dict, ndvi: list[float], lang: str, et0_method: str = "penman_monteith") -> list[str]:
    t = TEXT[lang]
    climate = site["climate"]
    method = t["et0_pm"] if et0_method == "penman_monteith" else t["et0_hg"]
    lines = [
        t["ev_power"].format(precip=climate["precip_annual_mm"], et0=climate["et0_annual_mm"], method=method, frost=climate["frost_days"], heat=climate["heat_days"]),
    ]
    if site.get("satellite_available", True):
        lines.append(t["ev_smap"].format(smrz=site["sm_rootzone"], sms=site["sm_surface"]))
        if site.get("gpm_annual_mm") is not None:
            lines.append(t["ev_gpm"].format(gpm=site["gpm_annual_mm"]))
        if ndvi:
            lo, hi = ndvi.index(min(ndvi)) + 1, ndvi.index(max(ndvi)) + 1
            lines.append(t["ev_modis"].format(nmin=min(ndvi), mmin=_month_name(lang, lo), nmax=max(ndvi), mmax=_month_name(lang, hi)))
        lines.append(t["ev_srtm"].format(slope=site["slope_deg"], elev=site["elevation_m"]))
        if site.get("grace_lwe_cm") is not None:
            lines.append(t["ev_grace"].format(grace=site["grace_lwe_cm"]))
    else:
        lines.append(t["ev_power_sm"].format(smrz=site["sm_rootzone"], sms=site["sm_surface"]))
        lines.append(t["ev_slope_only"].format(slope=site["slope_deg"], elev=site["elevation_m"]))
    lines += soil_evidence(site.get("soil"), lang)
    lines.append(t["ev_bands"])
    return lines


def validation_evidence(fit: dict[str, float] | None, lang: str) -> list[str]:
    if not fit:
        return []
    t = TEXT[lang]
    lines: list[str] = []
    if "soil_moisture_r" in fit:
        lines.append(t["ev_val_sm"].format(r=fit["soil_moisture_r"], mae=fit["soil_moisture_mae"]))
    if "canopy_r" in fit:
        lines.append(t["ev_val_ndvi"].format(r=fit["canopy_r"], mae=fit["canopy_mae"]))
    return lines


def describe_strategy(
    key: str,
    crops: list[str],
    current_crops: list[str],
    metrics: dict,
    current_metrics: dict,
    vulnerability: list[dict],
    site: dict,
    ndvi: list[float],
    lang: str,
    et0_method: str = "penman_monteith",
    extra_evidence: list[str] | None = None,
    extra_gaps: list[str] | None = None,
    current_vulnerability: list[dict] | None = None,
) -> dict:
    t = TEXT[lang]
    p50 = {k: v["p50"] for k, v in metrics.items()}
    base = {k: v["p50"] for k, v in current_metrics.items()}
    swaps = ", ".join(f"{a} -> {b}" for a, b in zip(current_crops, crops) if a != b) or "-"
    why = WHY[lang].get(key, WHY[lang]["extra_a"]).format(bare=base["bare_soil_days"], swaps=swaps)
    evidence = climate_evidence(site, ndvi, lang, et0_method) + list(extra_evidence or [])
    if key != "current":
        evidence.append(
            t["ev_delta"].format(
                dw=p50["water_use_mm"] - base["water_use_mm"],
                de=p50["erosion_t_ha"] - base["erosion_t_ha"],
                dn=p50["n_balance_kg_ha"] - base["n_balance_kg_ha"],
                db=p50["bare_soil_days"] - base["bare_soil_days"],
            )
        )
    benefits: list[str] = []
    if key == "current":
        benefits.append(t["ben_base"].format(y=p50["yield_index"], w=p50["water_stress_days"]))
    else:
        if base["water_use_mm"] - p50["water_use_mm"] >= 10:
            benefits.append(t["ben_water"].format(v=base["water_use_mm"] - p50["water_use_mm"]))
        if base["irrigation_need_mm"] - p50["irrigation_need_mm"] >= 10:
            benefits.append(t["ben_irrig"].format(v=base["irrigation_need_mm"] - p50["irrigation_need_mm"]))
        if p50["n_balance_kg_ha"] - base["n_balance_kg_ha"] >= 5:
            benefits.append(t["ben_n"].format(v=p50["n_balance_kg_ha"] - base["n_balance_kg_ha"]))
        if base["erosion_t_ha"] > 0 and (1 - p50["erosion_t_ha"] / base["erosion_t_ha"]) >= 0.05:
            benefits.append(t["ben_erosion"].format(v=100 * (1 - p50["erosion_t_ha"] / base["erosion_t_ha"])))
        if base["bare_soil_days"] - p50["bare_soil_days"] >= 10:
            benefits.append(t["ben_bare"].format(v=base["bare_soil_days"] - p50["bare_soil_days"]))
        if p50["soil_om_index"] - base["soil_om_index"] >= 0.5:
            benefits.append(t["ben_om"].format(v=p50["soil_om_index"] - base["soil_om_index"]))
        if base["income_index"] > 0 and (p50["income_index"] / base["income_index"] - 1) >= 0.05:
            benefits.append(t["ben_income"].format(v=100 * (p50["income_index"] / base["income_index"] - 1)))
        if not benefits:
            benefits.append(t["ben_similar"])
    soil = site.get("soil")
    soil_gap = t["gap_soil"] if not soil or soil["source"].startswith("Default") else t["gap_soil_point"].format(source=soil["source"])
    gaps = [soil_gap, t["gap_mgmt"], t["gap_res"], t["gap_price"], t["gap_cost"], t["gap_irr_eff"]]
    if not site.get("satellite_available", True):
        gaps.append(t["gap_nosat"])
    gaps += list(extra_gaps or [])
    new_crops = sorted({c for c in crops if c not in current_crops and c in CROPS})
    if new_crops:
        gaps.append(t["gap_seed"].format(crops=", ".join(new_crops)))
    risks: list[str] = []
    erosion_now = {v["month"]: v.get("soil_loss_t_ha") or 0.0 for v in vulnerability if v["type"] == "erosion"}
    erosion_base = {v["month"]: v.get("soil_loss_t_ha") or 0.0 for v in (current_vulnerability or []) if v["type"] == "erosion"}
    top = sorted(erosion_now, key=lambda m: -erosion_now[m])[:3]
    if top and erosion_now[top[0]] >= 0.05:
        risks.append(
            t["risk_erosion"].format(
                months=", ".join(_month_name(lang, m) for m in top),
                values=", ".join(f"{erosion_now[m]:.2f}" for m in top),
                current=", ".join(f"{erosion_base.get(m, 0.0):.2f}" for m in top),
            )
        )
    others = [v for v in vulnerability if v["type"] != "erosion"]
    for item in sorted(others, key=lambda v: -v["severity"])[:3]:
        risks.append(
            t["risk_vuln"].format(kind=t["kinds"][item["type"]], month=_month_name(lang, item["month"]), p=item["severity"] * 100)
        )
    if p50["irrigation_need_mm"] >= 50:
        has_dry_season_crop = any(CROPS[c].winter for c in crops if c in CROPS)
        risks.append(t["risk_irrig" if has_dry_season_crop else "risk_deficit"].format(v=p50["irrigation_need_mm"]))
    if p50["n_balance_kg_ha"] < -20:
        risks.append(t["risk_n"].format(v=p50["n_balance_kg_ha"]))
    if any(CROPS[c].cover for c in crops if c in CROPS):
        risks.append(t["risk_cover"])
    if metrics["water_stress_days"]["p90"] > p50["water_stress_days"] + 5:
        risks.append(t["risk_warm"].format(v=metrics["water_stress_days"]["p90"]))
    risks.append(t["risk_review"])
    return {"why": why, "evidence": evidence, "benefits": benefits, "gaps": gaps, "risks": risks}


LIVE_UNAVAILABLE_GAP = {
    "en": "Live NASA data unavailable for this point; demo farm climate used",
    "es": "Datos NASA en vivo no disponibles para este punto; se usó el clima de la parcela demo",
}

CDL_TEXT = {
    "en": {
        "alt": "USDA CDL {first}–{last}: corn–soybean alternation in {alt} of {total} crop years",
        "noncrop": "USDA CDL {first}–{last}: the farm cell and its 8 neighbouring 300 m cells show {noncrop} cover in most of {total} years (cropland in only {crop}); the regional corn–soybean rotation is assumed.",
        "gap": "Cropping history at this point is not cropland in the USDA CDL; the current rotation is an assumption to confirm with the farmer.",
    },
    "es": {
        "alt": "USDA CDL {first}–{last}: alternancia maíz–soya en {alt} de {total} años de cultivo",
        "noncrop": "USDA CDL {first}–{last}: la celda de la parcela y sus 8 celdas vecinas de 300 m muestran cobertura de {noncrop} en la mayoría de los {total} años (cultivo en solo {crop}); se asume la rotación regional maíz–soya.",
        "gap": "El historial de cultivos en este punto no es tierra de cultivo en el USDA CDL; la rotación actual es un supuesto por confirmar con el agricultor.",
    },
}


def cdl_text(summary, lang: str) -> tuple[list[str], list[str]]:
    t = CDL_TEXT[lang]
    values = dict(
        first=summary.first_year, last=summary.last_year, alt=summary.alternation_years, total=summary.total_years,
        crop=summary.crop_years, noncrop=summary.non_crop_label,
    )
    if summary.is_cropland:
        return [t["alt"].format(**values)], []
    return [t["noncrop"].format(**values)], [t["gap"]]
