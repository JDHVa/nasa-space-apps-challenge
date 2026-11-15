import { useEffect, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BarChart3, CloudRain, Droplets, Leaf, Pause, Play, Sprout, Sun } from "lucide-react";
import clsx from "clsx";
import { Link } from "react-router-dom";
import { cropLabel, useMonths, useT } from "../i18n";
import { useStore } from "../store";
import { DataBanner } from "../components/DataBanner";
import { RiskBadge } from "../components/RiskBadge";
import { FieldScene } from "../twin/FieldScene";
import { sampleAt, weekToMonthYear } from "../twin/sample";

function Gauge({
  label,
  value,
  display,
  unit,
  color,
  icon
}: {
  label: string;
  value: number;
  display: string;
  unit: string;
  color: string;
  icon: React.ReactNode;
}) {
  const radius = 22;
  const circ = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(1, value));
  return (
    <div className="glass flex items-center gap-3 rounded-2xl px-3 py-2.5">
      <div className="relative h-14 w-14 shrink-0">
        <svg viewBox="0 0 56 56" className="h-full w-full -rotate-90">
          <circle cx="28" cy="28" r={radius} fill="none" stroke="rgba(148,163,184,0.18)" strokeWidth="5" />
          <circle
            cx="28"
            cy="28"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={circ * (1 - pct)}
            style={{ transition: "stroke-dashoffset 0.3s ease", filter: `drop-shadow(0 0 5px ${color})` }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center" style={{ color }}>
          {icon}
        </div>
      </div>
      <div className="min-w-0">
        <div className="truncate text-[11px] font-medium uppercase tracking-wider text-slate-400">{label}</div>
        <div className="text-lg font-bold tabular-nums leading-tight text-slate-50">
          {display}
          <span className="ml-1 text-xs font-medium text-slate-400">{unit}</span>
        </div>
      </div>
    </div>
  );
}

export function TwinView() {
  const t = useT();
  const months = useMonths();
  const { analysis, strategyId, setStrategy, week, setWeek, playing, setPlaying } = useStore();
  const strategy = useMemo(
    () => analysis?.strategies.find((s) => s.id === strategyId) ?? analysis?.strategies[0] ?? null,
    [analysis, strategyId]
  );
  const maxWeek = Math.max(0, (strategy?.daily_sample.length ?? 1) - 1);

  useEffect(() => {
    if (!playing || !strategy) return;
    let raf = 0;
    let last = performance.now();
    let lastPush = 0;
    let local = useStore.getState().week;
    const tick = (now: number) => {
      const dt = Math.min(0.1, (now - last) / 1000);
      last = now;
      local += dt * 3.2;
      if (local > maxWeek) local = 0;
      if (now - lastPush > 50) {
        lastPush = now;
        setWeek(local);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, strategy, maxWeek, setWeek]);

  if (!analysis || !strategy) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-slate-400">
        <Sprout className="h-10 w-10 text-agri-400" />
        <p>{t("twin.noData")}</p>
        <Link to="/" className="rounded-xl bg-agri-400 px-4 py-2 text-sm font-bold text-space-950">
          {t("twin.back")}
        </Link>
      </div>
    );
  }

  const s = sampleAt(strategy.daily_sample, week);
  const { month, year } = weekToMonthYear(week);
  const bare = !s.crop || s.canopy < 0.04;

  return (
    <div className="relative h-full w-full">
      <div className="absolute inset-0">
        <FieldScene strategy={strategy} />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-space-950/80 via-transparent to-space-950/40" />

      <div className="pointer-events-none absolute inset-x-3 top-3 flex flex-wrap items-start justify-between gap-3 sm:inset-x-5">
        <motion.div
          initial={{ opacity: 0, y: -14 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass pointer-events-auto rounded-2xl p-2"
        >
          <div className="mb-1.5 px-2 pt-1 text-[10px] font-bold uppercase tracking-widest text-slate-400">
            {t("twin.strategy")}
          </div>
          <div className="flex gap-1">
            {analysis.strategies.map((st, i) => {
              const active = st.id === strategy.id;
              return (
                <button
                  key={st.id}
                  onClick={() => setStrategy(st.id)}
                  className={clsx(
                    "relative rounded-xl px-3.5 py-2 text-sm font-bold transition",
                    active ? "text-space-950" : "text-slate-300 hover:bg-white/5"
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="stratPill"
                      className="absolute inset-0 rounded-xl bg-agri-400 shadow-[0_0_22px_rgba(74,222,128,0.45)]"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                  <span className="relative">{String.fromCharCode(65 + i)}</span>
                </button>
              );
            })}
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={strategy.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
              className="max-w-[260px] px-2 pb-1 pt-2"
            >
              <div className="text-sm font-semibold leading-snug text-slate-100">{strategy.name}</div>
              {strategy.is_current && (
                <span className="mt-1 inline-block rounded-full bg-amber-400/15 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-300">
                  {t("twin.current")}
                </span>
              )}
              <div>
                <RiskBadge strategy={strategy} />
              </div>
            </motion.div>
          </AnimatePresence>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: -14 }}
          animate={{ opacity: 1, y: 0 }}
          className="pointer-events-auto flex gap-2"
        >
          <Link
            to="/compare"
            className="flex items-center gap-2 rounded-xl bg-agri-400 px-4 py-2.5 text-sm font-bold text-space-950 shadow-[0_0_28px_rgba(74,222,128,0.35)] transition hover:scale-105"
          >
            <BarChart3 className="h-4 w-4" />
            {t("twin.compare")}
          </Link>
        </motion.div>
      </div>

      <div className="pointer-events-none absolute inset-x-3 top-32 flex justify-center sm:top-28">
        <DataBanner className="max-w-md" />
      </div>

      <div className="pointer-events-none absolute right-3 top-28 hidden w-56 flex-col gap-2 sm:right-5 md:flex">
        {[
          { label: t("twin.moisture"), value: s.moisture, display: `${Math.round(s.moisture * 100)}`, unit: "%", color: "#38bdf8", icon: <Droplets className="h-5 w-5" /> },
          { label: t("twin.canopy"), value: s.canopy, display: s.canopy.toFixed(2), unit: "", color: "#4ade80", icon: <Leaf className="h-5 w-5" /> },
          { label: t("twin.rain"), value: s.rain / 40, display: s.rain.toFixed(0), unit: "mm", color: "#93c5fd", icon: <CloudRain className="h-5 w-5" /> },
          { label: t("twin.et"), value: s.et / 8, display: s.et.toFixed(1), unit: "mm/d", color: "#fbbf24", icon: <Sun className="h-5 w-5" /> }
        ].map((g, i) => (
          <motion.div key={g.label} initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.08 }}>
            <Gauge {...g} />
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass absolute inset-x-3 bottom-3 rounded-2xl px-4 py-3 sm:inset-x-5 sm:bottom-4"
      >
        <div className="flex items-center gap-4">
          <button
            onClick={() => setPlaying(!playing)}
            aria-label={playing ? t("twin.pause") : t("twin.play")}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-agri-400 text-space-950 shadow-[0_0_22px_rgba(74,222,128,0.4)] transition hover:scale-110"
          >
            {playing ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 translate-x-0.5" />}
          </button>
          <div className="min-w-0 flex-1">
            <div className="mb-1.5 flex flex-wrap items-baseline justify-between gap-2">
              <div className="text-sm font-bold text-slate-100">
                {months[month]} <span className="text-slate-400">- {t("twin.year")} {year + 1}</span>
              </div>
              <div
                className={clsx(
                  "rounded-full px-2.5 py-0.5 text-xs font-bold",
                  bare ? "bg-amber-400/15 text-amber-300" : "bg-agri-400/15 text-agri-400"
                )}
              >
                {cropLabel(t, bare ? null : s.crop)}
              </div>
            </div>
            <input
              className="fx"
              type="range"
              min={0}
              max={maxWeek}
              step={0.1}
              value={Math.min(week, maxWeek)}
              onChange={(e) => {
                setPlaying(false);
                setWeek(Number(e.target.value));
              }}
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
