import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, MapPin, Sparkles, Wand2 } from "lucide-react";
import clsx from "clsx";
import maplibregl from "maplibre-gl";
import { useNavigate } from "react-router-dom";
import { analyze, fetchDemo, type DemoFarm } from "../api/client";
import type { AnalyzeResponse, Priorities } from "../api/types";
import { cropLabel, useT, type Key } from "../i18n";
import { useStore } from "../store";

const CROPS = ["maize", "sorghum", "wheat", "beans", "soybean", "oats", "alfalfa", "vetch", "rye", "fallow"];
const PRIORITY_KEYS: (keyof Priorities)[] = ["water", "nitrogen", "erosion", "organic_matter", "income"];
const STEPS: Key[] = ["step.power", "step.smap", "step.gpm", "step.modis", "step.twin"];

const DEMOS: { farm: DemoFarm; key: Key; lat: number; lon: number }[] = [
  { farm: "iowa", key: "demo.iowa", lat: 41.95, lon: -93.71 },
  { farm: "bajio", key: "demo.bajio", lat: 20.52, lon: -100.81 }
];

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export function MapSelect() {
  const t = useT();
  const navigate = useNavigate();
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const { rotation, setRotation, priorities, setPriority, location, setLocation, lang, setAnalysis, setDemoMode } = useStore();
  const [step, setStep] = useState(-1);
  const busy = step >= 0;
  const [warn, setWarn] = useState(false);

  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      center: location ? [location.lon, location.lat] : [-101.3, 20.9],
      zoom: location ? 11 : 3.2,
      pitch: 30,
      attributionControl: { compact: true },
      style: {
        version: 8,
        sources: {
          esri: {
            type: "raster",
            tiles: [
              "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ],
            tileSize: 256,
            maxzoom: 18,
            attribution: "Tiles &copy; Esri, Maxar, Earthstar Geographics"
          },
          labels: {
            type: "raster",
            tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"],
            tileSize: 256,
            attribution: "Labels &copy; Esri"
          }
        },
        layers: [
          { id: "esri", type: "raster", source: "esri", paint: { "raster-brightness-max": 0.7, "raster-saturation": -0.15 } },
          { id: "labels", type: "raster", source: "labels" }
        ]
      }
    });
    mapRef.current = map;
    const place = (lng: number, lat: number) => {
      markerRef.current?.remove();
      const el = document.createElement("div");
      el.className = "pulse-marker";
      markerRef.current = new maplibregl.Marker({ element: el }).setLngLat([lng, lat]).addTo(map);
    };
    if (location) place(location.lon, location.lat);
    map.on("click", (e) => {
      place(e.lngLat.lng, e.lngLat.lat);
      setLocation({ lat: e.lngLat.lat, lon: e.lngLat.lng });
      setWarn(false);
      map.flyTo({ center: e.lngLat, zoom: Math.max(map.getZoom(), 10.5), pitch: 45, duration: 1800, essential: true });
    });
    map.getCanvas().style.cursor = "crosshair";
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  const toggleCrop = (crop: string) =>
    setRotation(rotation.includes(crop) ? rotation.filter((c) => c !== crop) : [...rotation, crop]);

  const run = async (work: Promise<AnalyzeResponse>) => {
    setStep(0);
    const box: { value: AnalyzeResponse | null } = { value: null };
    work.then((r) => {
      box.value = r;
    });
    let i = 0;
    while (i < STEPS.length) {
      setStep(i);
      await sleep(box.value ? 160 : i === STEPS.length - 1 ? 400 : 650);
      if (i === STEPS.length - 1 && !box.value) continue;
      i++;
    }
    const data = box.value ?? (await work);
    setStep(STEPS.length);
    await sleep(350);
    setAnalysis(data);
    navigate("/twin");
  };

  const build = () => {
    if (!location) {
      setWarn(true);
      return;
    }
    const seq = rotation.length ? rotation : ["maize"];
    void run(
      analyze({
        lat: location.lat,
        lon: location.lon,
        current_rotation: seq,
        priorities,
        years: 5,
        lang
      })
    );
  };

  return (
    <div className="relative h-full w-full">
      <div ref={container} className="absolute inset-0" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-space-950/70 via-transparent to-transparent" />
      <motion.aside
        initial={{ x: -40, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="glass absolute bottom-3 left-3 right-3 top-auto max-h-[78%] overflow-y-auto rounded-2xl p-5 sm:bottom-4 sm:left-4 sm:right-auto sm:top-4 sm:max-h-none sm:w-[380px]"
      >
        <h2 className="text-xl font-extrabold leading-tight tracking-tight">{t("map.title")}</h2>
        <div
          className={clsx(
            "mt-2 flex items-center gap-2 rounded-lg px-3 py-2 text-xs",
            location ? "bg-agri-500/10 text-agri-400" : "bg-white/5 text-slate-400",
            warn && "ring-1 ring-amber-400/60"
          )}
        >
          <MapPin className="h-4 w-4" />
          {location ? `${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}` : warn ? t("map.needPoint") : t("map.hint")}
        </div>

        <h3 className="mt-5 text-xs font-bold uppercase tracking-wider text-slate-400">{t("map.rotation")}</h3>
        <p className="text-[11px] text-slate-500">{t("map.rotationHint")}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {CROPS.map((crop) => {
            const idx = rotation.indexOf(crop);
            return (
              <motion.button
                key={crop}
                whileTap={{ scale: 0.92 }}
                onClick={() => toggleCrop(crop)}
                disabled={busy}
                className={clsx(
                  "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 transition",
                  idx >= 0
                    ? "bg-agri-500/20 text-agri-400 ring-agri-500/50"
                    : "bg-white/5 text-slate-300 ring-white/10 hover:bg-white/10"
                )}
              >
                {idx >= 0 && (
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-agri-400 text-[10px] font-bold text-space-950">
                    {idx + 1}
                  </span>
                )}
                {cropLabel(t, crop)}
              </motion.button>
            );
          })}
        </div>

        <h3 className="mt-5 text-xs font-bold uppercase tracking-wider text-slate-400">{t("map.priorities")}</h3>
        <div className="mt-2 space-y-3">
          {PRIORITY_KEYS.map((key) => (
            <label key={key} className="block">
              <div className="mb-1 flex justify-between text-xs">
                <span className="text-slate-300">{t(`prio.${key}` as Key)}</span>
                <span className="font-semibold tabular-nums text-amber-300">{Math.round(priorities[key] * 100)}</span>
              </div>
              <input
                className="fx"
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={priorities[key]}
                disabled={busy}
                onChange={(e) => setPriority(key, Number(e.target.value))}
              />
            </label>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {busy ? (
            <motion.ul
              key="steps"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 space-y-2 overflow-hidden"
            >
              <li className="text-xs font-bold uppercase tracking-wider text-agri-400">{t("map.building")}</li>
              {STEPS.map((s, i) => (
                <motion.li
                  key={s}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: i <= step ? 1 : 0.35, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="flex items-center gap-2 text-sm"
                >
                  {i < step ? (
                    <Check className="h-4 w-4 text-agri-400" />
                  ) : i === step ? (
                    <Loader2 className="h-4 w-4 animate-spin text-amber-300" />
                  ) : (
                    <span className="h-4 w-4 rounded-full border border-slate-600" />
                  )}
                  <span className={i < step ? "text-slate-300" : "text-slate-100"}>{t(s)}</span>
                </motion.li>
              ))}
            </motion.ul>
          ) : (
            <motion.div key="btns" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mt-6 space-y-2">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                onClick={build}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-agri-400 px-4 py-3 text-sm font-bold text-space-950 shadow-[0_0_30px_rgba(74,222,128,0.35)]"
              >
                <Wand2 className="h-4 w-4" />
                {t("map.build")}
              </motion.button>
              {DEMOS.map((d) => (
                <motion.button
                  key={d.farm}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => {
                    mapRef.current?.flyTo({ center: [d.lon, d.lat], zoom: 10, duration: 1400 });
                    setDemoMode(true);
                    void run(fetchDemo(d.farm));
                  }}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-white/5 px-4 py-2.5 text-sm font-semibold text-amber-300 ring-1 ring-amber-300/30 hover:bg-white/10"
                >
                  <Sparkles className="h-4 w-4" />
                  {t(d.key)}
                </motion.button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.aside>
    </div>
  );
}
