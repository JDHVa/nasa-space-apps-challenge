import datetime as dt
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "backend" / "data_raw"
TIMEOUT = 60.0
FARMS = {"iowa": (41.95, -93.71), "bajio": (20.52, -100.81)}
POWER_PARAMS = "T2M_MAX,T2M_MIN,T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M,T2MDEW,GWETROOT,GWETTOP"
POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_CLIM_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
SOIL_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
SOIL_PROPS = ["clay", "sand", "silt", "soc", "bdod", "phh2o", "nitrogen", "cec"]
SOIL_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm"]
SDA_URL = "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
CDL_URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue"
CDL_YEARS = range(2010, 2025)
CDL_STEP = 300.0
NWIS_SITE_URL = "https://waterservices.usgs.gov/nwis/site/"
NWIS_DV_URL = "https://waterservices.usgs.gov/nwis/dv/"
NWIS_BBOX = "-94.50,41.50,-93.00,42.50"
NWIS_RADIUS_KM = 30.0

manifest = []


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def request(client, method, url, **kwargs):
    last_error = None
    for attempt in range(2):
        try:
            response = client.request(method, url, timeout=TIMEOUT, **kwargs)
            response.raise_for_status()
            return response
        except Exception as exc:
            last_error = exc
            time.sleep(3)
    raise last_error


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path.stat().st_size


def rel(farm, name):
    return f"backend/data_raw/{farm}/{name}"


def record(farm, dataset, source, url_template, status, file, n_records, notes, error=None):
    entry = {
        "farm": farm,
        "dataset": dataset,
        "source": source,
        "url_template": url_template,
        "date_fetched": utc_now(),
        "status": status,
        "file": file,
        "n_records": n_records,
        "notes": notes,
    }
    if error:
        entry["error"] = error
    manifest.append(entry)
    print(f"[{status}] {farm}/{dataset}: records={n_records} size={entry.get('size', '')} {notes[:100]}", flush=True)


def attempt(farm, dataset, source, url_template, fn):
    try:
        file, n_records, notes, size = fn()
        record(farm, dataset, source, url_template, "ok", file, n_records, f"{notes} size_bytes={size}")
    except Exception as exc:
        record(farm, dataset, source, url_template, "failed", None, 0, "", error=f"{type(exc).__name__}: {exc}"[:500])


def power_fetch(client, farm, lat, lon, daily):
    if daily:
        url = POWER_DAILY_URL
        extra = {"start": "19950101", "end": "20241231"}
        name = "power_daily.json"
    else:
        url = POWER_CLIM_URL
        extra = {}
        name = "power_climatology.json"
    params = {"parameters": POWER_PARAMS, "community": "AG", "longitude": lon, "latitude": lat, "format": "JSON", **extra}
    data = request(client, "GET", url, params=params).json()
    if "properties" not in data:
        raise RuntimeError(str(data)[:300])
    parameter = data["properties"]["parameter"]
    n = len(next(iter(parameter.values()), {})) if daily else len(parameter)
    size = save_json(RAW / farm / name, data)
    unit = "days" if daily else "parameters"
    return rel(farm, name), n, f"{n} {unit}, POWER AG community", size


def soilgrids_fetch(client, farm, lat, lon):
    params = [("lon", lon), ("lat", lat)]
    params += [("property", p) for p in SOIL_PROPS]
    params += [("depth", d) for d in SOIL_DEPTHS]
    params.append(("value", "mean"))
    data = request(client, "GET", SOIL_URL, params=params).json()
    layers = data.get("properties", {}).get("layers", [])
    if not layers:
        raise RuntimeError(str(data)[:300])
    size = save_json(RAW / farm / "soilgrids.json", data)
    return rel(farm, "soilgrids.json"), len(layers), f"{len(layers)} layers (props x depths)", size


def ssurgo_sql(lat, lon):
    return f"""
SELECT mu.mukey, mu.muname, co.cokey, co.compname, co.comppct_r, co.hydgrp, co.drainagecl, ch.kwfact, co.slope_r, ch.hzdept_r, ch.hzdepb_r, ch.om_r, ch.awc_r, ch.claytotal_r, ch.sandtotal_r
FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('point({lon} {lat})') AS m
INNER JOIN mapunit AS mu ON mu.mukey = m.mukey
INNER JOIN component AS co ON co.mukey = mu.mukey
LEFT JOIN chorizon AS ch ON ch.cokey = co.cokey AND ch.hzdept_r = 0
ORDER BY co.comppct_r DESC
"""


def ssurgo_fetch(client, farm, lat, lon):
    sql = ssurgo_sql(lat, lon)
    data = request(client, "POST", SDA_URL, data={"query": sql, "format": "JSON+COLUMNNAME"}).json()
    if "Table" not in data:
        raise RuntimeError(str(data)[:300])
    n = max(len(data["Table"]) - 1, 0)
    size = save_json(RAW / farm / "ssurgo.json", {"query": sql, "result": data})
    return rel(farm, "ssurgo.json"), n, f"{n} component-horizon rows (point intersection)", size


def lonlat_to_albers(lat, lon):
    a = 6378137.0
    f = 1 / 298.257222101
    e2 = 2 * f - f * f
    e = math.sqrt(e2)

    def m_of(p):
        return math.cos(p) / math.sqrt(1 - e2 * math.sin(p) ** 2)

    def q_of(p):
        s = math.sin(p)
        return (1 - e2) * (s / (1 - e2 * s * s) - (1 / (2 * e)) * math.log((1 - e * s) / (1 + e * s)))

    p1, p2, p0 = math.radians(29.5), math.radians(45.5), math.radians(23.0)
    l0 = math.radians(-96.0)
    m1, m2 = m_of(p1), m_of(p2)
    q0, q1, q2 = q_of(p0), q_of(p1), q_of(p2)
    n = (m1 * m1 - m2 * m2) / (q2 - q1)
    c = m1 * m1 + n * q1
    rho0 = a * math.sqrt(c - n * q0) / n
    p = math.radians(lat)
    lam = math.radians(lon)
    rho = a * math.sqrt(c - n * q_of(p)) / n
    theta = n * (lam - l0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def cdl_category(text):
    match = re.search(r'category:\s*"([^"]*)"', text) or re.search(r"<Category>(.*?)</Category>", text, re.S)
    if match:
        return match.group(1).strip() or None
    return None


def cdl_fetch(client, farm, lat, lon):
    x0, y0 = lonlat_to_albers(lat, lon)
    offsets = [(dx, dy) for dy in (CDL_STEP, 0.0, -CDL_STEP) for dx in (-CDL_STEP, 0.0, CDL_STEP)]
    center_crop, dominant, grids, errors = {}, {}, {}, []
    raw_sample = None
    for year in CDL_YEARS:
        values = []
        for dx, dy in offsets:
            try:
                r = request(client, "GET", CDL_URL, params={"year": year, "x": round(x0 + dx, 3), "y": round(y0 + dy, 3)})
                if raw_sample is None:
                    raw_sample = {"year": year, "text": r.text[:600]}
                values.append(cdl_category(r.text))
            except Exception as exc:
                values.append(None)
                errors.append(f"{year} dx={dx} dy={dy}: {type(exc).__name__}: {exc}"[:200])
        names = [v for v in values if v]
        center_crop[str(year)] = values[4]
        dominant[str(year)] = Counter(names).most_common(1)[0][0] if names else None
        grids[str(year)] = values
    payload = {
        "point_albers_5070": [round(x0, 3), round(y0, 3)],
        "grid_spacing_m": CDL_STEP,
        "center_crop": center_crop,
        "dominant_3x3": dominant,
        "grid_order": "row-major, north to south, west to east; index 4 = center",
        "grid": grids,
        "errors": errors[:50],
        "raw_sample": raw_sample,
    }
    n = sum(1 for v in center_crop.values() if v)
    size = save_json(RAW / farm / "cdl_history.json", payload)
    return rel(farm, "cdl_history.json"), n, f"{n}/{len(CDL_YEARS)} years with center crop; {len(errors)} sample errors", size


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def parse_rdb(text):
    lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[2:]]


def nwis_fetch(client, farm, lat, lon):
    r = request(client, "GET", NWIS_SITE_URL, params={
        "format": "rdb", "bBox": NWIS_BBOX, "siteType": "GW",
    })
    sites = []
    for row in parse_rdb(r.text):
        try:
            slat, slon = float(row["dec_lat_va"]), float(row["dec_long_va"])
        except (KeyError, ValueError):
            continue
        d = haversine_km(lat, lon, slat, slon)
        if d <= NWIS_RADIUS_KM:
            sites.append({"site_no": row["site_no"], "station_nm": row.get("station_nm"), "lat": slat, "lon": slon, "distance_km": round(d, 2)})
    sites.sort(key=lambda s: s["distance_km"])
    selected, dv_payload, n = None, None, 0
    for s in sites[:8]:
        try:
            rr = request(client, "GET", NWIS_DV_URL, params={
                "format": "json", "sites": s["site_no"], "parameterCd": "72019", "startDT": "1995-01-01", "endDT": "2024-12-31",
            })
            body = rr.json()
            series = body.get("value", {}).get("timeSeries", [])
            count = sum(len(ts["values"][0]["value"]) for ts in series if ts.get("values"))
            if count > 0:
                selected, dv_payload, n = s, body, count
                break
        except Exception:
            continue
    payload = {
        "search_bbox": NWIS_BBOX,
        "radius_km": NWIS_RADIUS_KM,
        "parameter": "72019 depth to water level, feet below land surface (daily mean)",
        "candidates": sites,
        "selected": selected,
        "daily_values": dv_payload,
    }
    size = save_json(RAW / farm / "nwis_groundwater.json", payload)
    if selected is None:
        raise RuntimeError(f"no site within {NWIS_RADIUS_KM} km with 72019 daily data ({len(sites)} candidates)")
    return rel(farm, "nwis_groundwater.json"), n, f"site {selected['site_no']} at {selected['distance_km']} km, {n} daily values", size


def main():
    with httpx.Client(follow_redirects=True, headers={"User-Agent": "fieldtwin-public-data-fetch"}) as client:
        for farm, (lat, lon) in FARMS.items():
            if farm == "bajio":
                record(farm, "power_daily", "NASA POWER", POWER_DAILY_URL, "skipped_existing", "backend/demo/bajio_power.json", 0,
                       "already present in backend/demo (bajio_power.json), not re-downloaded")
            else:
                attempt(farm, "power_daily", "NASA POWER daily point", POWER_DAILY_URL,
                        lambda: power_fetch(client, farm, lat, lon, True))
            attempt(farm, "power_climatology", "NASA POWER climatology point", POWER_CLIM_URL,
                    lambda: power_fetch(client, farm, lat, lon, False))
            attempt(farm, "soilgrids", "ISRIC SoilGrids v2.0 point query", SOIL_URL,
                    lambda: soilgrids_fetch(client, farm, lat, lon))
            if farm == "iowa":
                attempt(farm, "ssurgo", "USDA NRCS SSURGO via Soil Data Access", SDA_URL,
                        lambda: ssurgo_fetch(client, farm, lat, lon))
                attempt(farm, "cdl_history", "USDA NASS CDL via CropScape GetCDLValue", CDL_URL,
                        lambda: cdl_fetch(client, farm, lat, lon))
                attempt(farm, "nwis_groundwater", "USGS NWIS site + dv (72019)", NWIS_DV_URL,
                        lambda: nwis_fetch(client, farm, lat, lon))
            else:
                for dataset, source in (("ssurgo", "USDA NRCS SSURGO"), ("cdl_history", "USDA NASS CDL"), ("nwis_groundwater", "USGS NWIS")):
                    record(farm, dataset, source, "", "not_requested", None, 0, "task scope limited to iowa")
            record(farm, "gaez_v4", "FAO GAEZ v4", "", "skipped", None, 0,
                   "no simple no-auth point REST endpoint found; GAEZ v4 is distributed as rasters via the portal (skipped)")

    not_fetched = [
        {"source": "NASA SMAP L3/L4", "reason": "Earthdata login required"},
        {"source": "NASA GPM IMERG", "reason": "Earthdata login required"},
        {"source": "ECOSTRESS", "reason": "Earthdata login required"},
        {"source": "GLDAS / NLDAS", "reason": "Earthdata login required"},
        {"source": "MODIS / Landsat / Sentinel-2", "reason": "Earthdata / Earth Engine credentials required"},
        {"source": "SRTM", "reason": "Earthdata / Earth Engine credentials required"},
        {"source": "GEDI", "reason": "Earthdata / Earth Engine credentials required"},
        {"source": "USDA NASS QuickStats", "reason": "API key required"},
        {"source": "ERA5", "reason": "Copernicus CDS API key required"},
        {"source": "PRISM", "reason": "bulk grids, not a point API; not fetched"},
    ]
    out = {
        "generated_utc": utc_now(),
        "farms": {k: {"lat": v[0], "lon": v[1]} for k, v in FARMS.items()},
        "entries": manifest,
        "not_fetched_requires_credentials_or_bulk": not_fetched,
    }
    save_json(RAW / "manifest.json", out)
    print(f"manifest written: {RAW / 'manifest.json'}", flush=True)


if __name__ == "__main__":
    main()
