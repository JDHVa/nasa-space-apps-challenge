import { Suspense, lazy, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Satellite } from "lucide-react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import clsx from "clsx";
import { useT } from "./i18n";
import { useStore } from "./store";

const Compare = lazy(() => import("./screens/Compare").then((m) => ({ default: m.Compare })));
const MapSelect = lazy(() => import("./screens/MapSelect").then((m) => ({ default: m.MapSelect })));
const TwinView = lazy(() => import("./screens/TwinView").then((m) => ({ default: m.TwinView })));

const defaultSources = [
  { name: "NASA POWER", dataset: "POWER", use: "Daily agroclimatology & GWETROOT soil wetness" },
  { name: "USDA SSURGO", dataset: "SSURGO", use: "Soil survey" },
  { name: "ISRIC SoilGrids", dataset: "SoilGrids 2.0", use: "Global soil properties" },
  { name: "USDA CDL", dataset: "Cropland Data Layer", use: "Crop history" }
];

function Page({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      className="absolute inset-0 overflow-y-auto"
      initial={{ opacity: 0, y: 14, filter: "blur(6px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      exit={{ opacity: 0, y: -10, filter: "blur(6px)" }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <Suspense
        fallback={
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-agri-400 border-t-transparent" />
          </div>
        }
      >
        {children}
      </Suspense>
    </motion.div>
  );
}

export function App() {
  const t = useT();
  const lang = useStore((s) => s.lang);
  const setLang = useStore((s) => s.setLang);
  const location = useLocation();
  const analysis = useStore((s) => s.analysis);
  const [open, setOpen] = useState(false);
  const sources = analysis?.sources?.length ? analysis.sources : defaultSources;
  const nav = [
    { to: "/", label: t("nav.map") },
    { to: "/twin", label: t("nav.twin") },
    { to: "/compare", label: t("nav.compare") }
  ];

  return (
    <div className="flex h-full flex-col text-slate-100">
      <header className="z-30 flex shrink-0 items-center justify-between gap-3 border-b border-white/5 bg-space-950/80 px-4 py-2.5 backdrop-blur-xl sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-agri-500/15 text-agri-400 ring-1 ring-agri-500/30">
            <Satellite className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <h1 className="text-base font-extrabold tracking-tight">
              Field<span className="text-agri-400">Twin</span>
            </h1>
            <p className="hidden text-[11px] text-slate-400 sm:block">{t("app.tagline")}</p>
          </div>
        </div>
        <nav className="flex items-center gap-1">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                  isActive
                    ? "bg-agri-500/20 text-agri-400 ring-1 ring-agri-500/40"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex rounded-lg bg-white/5 p-0.5 text-xs font-bold ring-1 ring-white/10">
          {(["en", "es"] as const).map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={clsx(
                "rounded-md px-2.5 py-1 uppercase transition",
                lang === l ? "bg-agri-500 text-space-950" : "text-slate-400 hover:text-slate-200"
              )}
            >
              {l}
            </button>
          ))}
        </div>
      </header>
      <main className="relative min-h-0 flex-1">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Page><MapSelect /></Page>} />
            <Route path="/twin" element={<Page><TwinView /></Page>} />
            <Route path="/compare" element={<Page><Compare /></Page>} />
          </Routes>
        </AnimatePresence>
      </main>
      <footer className="relative z-30 shrink-0 border-t border-amber-400/20 bg-space-950/90 px-4 py-1.5 text-center text-[11px] text-amber-200/80 backdrop-blur">
        {t("disclaimer")}
        <span className="mx-2 text-slate-600">|</span>
        <button type="button" onClick={() => setOpen((o) => !o)} className="text-slate-400 underline decoration-dotted hover:text-slate-200">
          {t("cmp.sources")}
        </button>
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="absolute bottom-10 left-1/2 z-40 max-h-[60vh] w-[min(92vw,640px)] -translate-x-1/2 overflow-y-auto rounded-2xl bg-space-900/95 p-4 text-left ring-1 ring-white/10 backdrop-blur-xl"
            >
              <div className="mb-2 flex items-center justify-between text-xs font-bold uppercase tracking-widest text-slate-400">
                {t("cmp.sources")}
                <button type="button" onClick={() => setOpen(false)} className="text-slate-500 hover:text-slate-200">
                  {t("banner.dismiss")}
                </button>
              </div>
              <ul className="grid gap-1.5 sm:grid-cols-2">
                {sources.map((src) => (
                  <li key={src.name} className="rounded-lg bg-white/5 px-3 py-1.5 text-xs text-slate-300">
                    <span className="font-semibold text-slate-100">{src.name}</span>
                    <span className="block text-slate-400">{src.dataset} - {src.use}</span>
                  </li>
                ))}
              </ul>
              {!analysis?.sources?.length && <p className="mt-3 text-[11px] text-slate-500">{t("src.ee")}</p>}
            </motion.div>
          )}
        </AnimatePresence>
      </footer>
    </div>
  );
}
export default App;
