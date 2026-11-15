import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Cpu, FlaskConical, Loader2 } from "lucide-react";
import { whatIf } from "../api/client";
import type { AnalyzeResponse, Band, MetricKey, Strategy, WhatIfResponse } from "../api/types";
import { cropLabel, useT, type Key } from "../i18n";

const METRICS: MetricKey[] = [
  "water_use_mm",
  "irrigation_need_mm",
  "yield_index",
  "n_balance_kg_ha",
  "erosion_t_ha",
  "soil_om_index",
  "income_index",
  "water_stress_days",
  "bare_soil_days"
];
const CROPS = ["maize", "sorghum", "wheat", "beans", "soybean", "oats", "alfalfa", "vetch", "rye"];

const fmt = (v: number) => (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(2));

function DualBar({ label, base, next, lo, hi }: { label: string; base: Band; next: Band | null; lo: number; hi: number }) {
  const span = hi - lo || 1;
  const pos = (v: number) => Math.max(0, Math.min(100, ((v - lo) / span) * 100));
  const row = (b: Band, color: string) => (
    <div className="relative h-2 rounded-full bg-white/5">
      {b.p10 !== b.p90 && (
        <motion.div
          className="absolute top-0 h-2 rounded-full"
          style={{ background: `${color}55`, boxShadow: `0 0 8px ${color}44` }}
          animate={{ left: `${pos(b.p10)}%`, width: `${Math.max(1.5, pos(b.p90) - pos(b.p10))}%` }}
          transition={{ type: "spring", stiffness: 120, damping: 20 }}
        />
      )}
      <motion.div
        className="absolute -top-0.5 h-3 w-1 rounded-full"
        style={{ background: color }}
        animate={{ left: `${pos(b.p50)}%` }}
        transition={{ type: "spring", stiffness: 120, damping: 20 }}
      />
    </div>
  );
  const delta = next ? next.p50 - base.p50 : 0;
  return (
    <div className="mb-3">
      <div className="mb-1 flex items-baseline justify-between text-[11px]">
        <span className="text-slate-400">{label}</span>
        <span className="tabular-nums text-slate-200">
          {fmt(base.p50)}
          {next && (
            <>
              <span className="mx-1 text-slate-500">to</span>
              <span className="font-semibold text-agri-400">{fmt(next.p50)}</span>
              <span className={delta === 0 ? "ml-1 text-slate-500" : "ml-1 text-sky-300"}>
                ({delta >= 0 ? "+" : ""}
                {fmt(delta)})
              </span>
            </>
          )}
          <span className="ml-1 text-slate-500">{base.unit}</span>
        </span>
      </div>
      <div className="space-y-1">
        {row(base, "#94a3b8")}
        {next && row(next, "#4ade80")}
      </div>
    </div>
  );
}

export function WhatIfLab({ analysis, strategy }: { analysis: AnalyzeResponse; strategy: Strategy }) {
  const t = useT();
  const [shift, setShift] = useState(0);
  const [irrigation, setIrrigation] = useState(0);
  const [swap, setSwap] = useState("");
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const seq = useRef(0);

  useEffect(() => {
    setShift(0);
    setIrrigation(0);
    setSwap("");
    setResult(null);
    setError(false);
  }, [strategy.id]);

  useEffect(() => {
    if (shift === 0 && irrigation === 0 && swap === "") {
      seq.current++;
      setResult(null);
      setError(false);
      setLoading(false);
      return;
    }
    const token = ++seq.current;
    setLoading(true);
    const timer = setTimeout(async () => {
      const res = await whatIf({
        strategy_id: strategy.id,
        rotation: strategy.rotation,
        sowing_shift_days: shift,
        irrigation_mm: irrigation,
        crop_swap: swap === "" ? null : swap,
        site: analysis.site
      });
      if (seq.current !== token) return;
      setLoading(false);
      if (res) {
        setResult(res);
        setError(false);
      } else {
        setError(true);
      }
    }, 450);
    return () => clearTimeout(timer);
  }, [shift, irrigation, swap, strategy.id, analysis.site]);

  const ranges = METRICS.map((m) => {
    const b = strategy.metrics[m];
    const n = result?.metrics[m];
    return { lo: Math.min(b.p10, n?.p10 ?? b.p10), hi: Math.max(b.p90, n?.p90 ?? b.p90) };
  });
  const isEmulator = result?.method === "emulator";

  return (
    <section className="glass rounded-2xl p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-400">
          <FlaskConical className="h-4 w-4 text-agri-400" />
          {t("lab.title")} - {strategy.name}
        </h3>
        <div className="flex items-center gap-2">
          {loading && <Loader2 className="h-4 w-4 animate-spin text-agri-400" />}
          {result && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-400/10 px-3 py-1 text-[11px] font-semibold text-sky-300 ring-1 ring-sky-400/30">
              <Cpu className="h-3.5 w-3.5" />
              {isEmulator ? t("lab.emulator") : t("lab.twin")} - {t("lab.coverage")} {Math.round(result.coverage * 100)}%
            </span>
          )}
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <div className="space-y-5">
          <label className="block text-xs text-slate-300">
            <div className="mb-1.5 flex justify-between">
              <span>{t("lab.shift")}</span>
              <span className="font-bold tabular-nums text-agri-400">
                {shift > 0 ? "+" : ""}
                {shift} d
              </span>
            </div>
            <input className="fx" type="range" min={-30} max={30} step={1} value={shift} onChange={(e) => setShift(Number(e.target.value))} />
          </label>
          <label className="block text-xs text-slate-300">
            <div className="mb-1.5 flex justify-between">
              <span>{t("lab.irrigation")}</span>
              <span className="font-bold tabular-nums text-agri-400">{irrigation} mm</span>
            </div>
            <input className="fx" type="range" min={0} max={300} step={10} value={irrigation} onChange={(e) => setIrrigation(Number(e.target.value))} />
          </label>
          <label className="block text-xs text-slate-300">
            <div className="mb-1.5">{t("lab.swap")}</div>
            <select
              value={swap}
              onChange={(e) => setSwap(e.target.value)}
              className="w-full rounded-lg bg-space-950 px-3 py-2 text-sm text-slate-100 ring-1 ring-white/15"
            >
              <option value="">{t("lab.noSwap")}</option>
              {CROPS.map((c) => (
                <option key={c} value={c}>
                  {cropLabel(t, c)}
                </option>
              ))}
            </select>
          </label>
          <div className="flex gap-4 text-[10px] text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-4 rounded-full bg-slate-400/60" />
              {t("lab.baseline")}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-4 rounded-full bg-agri-400/60" />
              {t("lab.whatif")}
            </span>
          </div>
          {error && (
            <div className="flex gap-2 rounded-lg border border-amber-400/40 bg-amber-400/10 p-2.5 text-xs text-amber-200">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {t("lab.error")}
            </div>
          )}
        </div>
        <div className="grid gap-x-6 sm:grid-cols-2">
          {METRICS.map((m, i) => (
            <DualBar key={m} label={t(`metric.${m}` as Key)} base={strategy.metrics[m]} next={result?.metrics[m] ?? null} lo={ranges[i].lo} hi={ranges[i].hi} />
          ))}
        </div>
      </div>
    </section>
  );
}
