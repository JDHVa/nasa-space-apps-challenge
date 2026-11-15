import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Box, ChevronDown, Database } from "lucide-react";
import clsx from "clsx";
import { Link } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { Narrator } from "../components/Narrator";
import { DataBanner } from "../components/DataBanner";
import { RiskBadge } from "../components/RiskBadge";
import { WhatIfLab } from "../components/WhatIfLab";
import type { MetricKey, Strategy, Vulnerability } from "../api/types";
import { useMonths, useT, type Key } from "../i18n";
import { useStore } from "../store";

const COLORS = ["#fbbf24", "#4ade80", "#38bdf8", "#c084fc", "#f472b6"];
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
const LOWER_BETTER: MetricKey[] = ["water_use_mm", "irrigation_need_mm", "erosion_t_ha", "water_stress_days", "bare_soil_days"];
const VULN_TYPES: Vulnerability["type"][] = ["heat", "frost", "drought", "waterlogging", "erosion"];
const VULN_COLORS: Record<Vulnerability["type"], string> = {
  heat: "#f97316",
  frost: "#60a5fa",
  drought: "#fbbf24",
  waterlogging: "#22d3ee",
  erosion: "#c084fc"
};

const fmt = (v: number) => (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(2));

const tooltipStyle = {
  background: "rgba(11,18,32,0.95)",
  border: "1px solid rgba(148,163,184,0.2)",
  borderRadius: 12,
  color: "#e2e8f0",
  fontSize: 12
};

function Panel({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={clsx("glass rounded-2xl p-5", className)}>
      <h3 className="mb-4 text-xs font-bold uppercase tracking-widest text-slate-400">{title}</h3>
      {children}
    </section>
  );
}

function BandBar({ label, strategy, metric, lo, hi, color }: { label: string; strategy: Strategy; metric: MetricKey; lo: number; hi: number; color: string }) {
  const b = strategy.metrics[metric];
  const span = hi - lo || 1;
  const left = ((b.p10 - lo) / span) * 100;
  const point = b.p10 === b.p90;
  const width = Math.max(1.5, ((b.p90 - b.p10) / span) * 100);
  const mid = ((b.p50 - lo) / span) * 100;
  return (
    <div className="mb-2.5">
      <div className="mb-1 flex items-baseline justify-between text-[11px]">
        <span className="text-slate-400">{label}</span>
        <span className="font-semibold tabular-nums text-slate-200">
          {fmt(b.p50)}
          <span className="ml-1 font-normal text-slate-500">{b.unit}</span>
        </span>
      </div>
      <div className="relative h-2 rounded-full bg-white/5">
        {!point && (
          <motion.div
            className="absolute top-0 h-2 rounded-full"
            style={{ background: `${color}55`, boxShadow: `0 0 8px ${color}44` }}
            initial={{ left: `${mid}%`, width: 0 }}
            animate={{ left: `${left}%`, width: `${width}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        )}
        <motion.div
          className="absolute -top-0.5 h-3 w-1 rounded-full"
          style={{ background: color }}
          initial={{ left: `${mid}%` }}
          animate={{ left: `${mid}%` }}
        />
      </div>
      {!point && (
        <div className="mt-0.5 flex justify-between text-[9px] tabular-nums text-slate-600">
          <span>P10 {fmt(b.p10)}</span>
          <span>P90 {fmt(b.p90)}</span>
        </div>
      )}
    </div>
  );
}

function Accordion({ title, items, defaultOpen }: { title: string; items: string[]; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(Boolean(defaultOpen));
  return (
    <div className="border-b border-white/5 last:border-0">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center justify-between py-3 text-left text-sm font-semibold text-slate-100">
        {title}
        <motion.span animate={{ rotate: open ? 180 : 0 }}>
          <ChevronDown className="h-4 w-4 text-slate-400" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.ul
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden pb-3 pl-1 text-sm text-slate-300"
          >
            {items.map((item) => (
              <li key={item} className="flex gap-2 py-0.5">
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-agri-400" />
                {item}
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Compare() {
  const t = useT();
  const months = useMonths();
  const { analysis, strategyId, setStrategy, priorities } = useStore();

  const strategies = analysis?.strategies ?? [];
  const selected = strategies.find((s) => s.id === strategyId) ?? strategies[0];

  const ranges = useMemo(() => {
    const out = {} as Record<MetricKey, { lo: number; hi: number }>;
    METRICS.forEach((m) => {
      out[m] = {
        lo: Math.min(...strategies.map((s) => s.metrics[m].p10)),
        hi: Math.max(...strategies.map((s) => s.metrics[m].p90))
      };
    });
    return out;
  }, [strategies]);

  const radarData = useMemo(() => {
    const axes: { key: keyof typeof priorities; metric: MetricKey }[] = [
      { key: "water", metric: "irrigation_need_mm" },
      { key: "nitrogen", metric: "n_balance_kg_ha" },
      { key: "erosion", metric: "erosion_t_ha" },
      { key: "organic_matter", metric: "soil_om_index" },
      { key: "income", metric: "income_index" }
    ];
    return axes.map(({ key, metric }) => {
      const vals = strategies.map((s) => s.metrics[metric].p50);
      const lo = Math.min(...vals);
      const hi = Math.max(...vals);
      const row: Record<string, number | string> = { axis: t(`prio.${key}` as Key), priority: priorities[key] };
      strategies.forEach((s, i) => {
        let n = hi === lo ? 0.5 : (s.metrics[metric].p50 - lo) / (hi - lo);
        if (LOWER_BETTER.includes(metric)) n = 1 - n;
        row[`s${i}`] = 0.1 + 0.9 * n;
      });
      return row;
    });
  }, [strategies, priorities, t]);

  const validationData = useMemo(() => {
    if (!analysis) return [];
    const ndvi_observed = analysis.validation.ndvi_observed ?? [];
    const canopy_twin = analysis.validation.canopy_twin ?? [];
    const n = Math.max(ndvi_observed.length, canopy_twin.length);
    return Array.from({ length: n }, (_, i) => ({ i, ndvi: ndvi_observed[i], canopy: canopy_twin[i] }));
  }, [analysis]);

  const smData = useMemo(() => {
    const obs = analysis?.validation.soil_moisture_observed ?? [];
    const twin = analysis?.validation.soil_moisture_twin ?? [];
    const n = Math.max(obs.length, twin.length);
    return Array.from({ length: n }, (_, i) => ({ i: months[i] ?? String(i + 1), obs: obs[i], twin: twin[i] }));
  }, [analysis, months]);

  const fit = analysis?.validation.fit;
  const soil = analysis?.site.soil;
  const fitBadges: { label: string; value: string }[] = [];
  if (fit?.soil_moisture_r !== undefined) fitBadges.push({ label: "SM R", value: fit.soil_moisture_r.toFixed(2) });
  if (fit?.soil_moisture_mae !== undefined) fitBadges.push({ label: "SM MAE", value: fit.soil_moisture_mae.toFixed(3) });
  if (fit?.canopy_r !== undefined) fitBadges.push({ label: "NDVI R", value: fit.canopy_r.toFixed(2) });
  if (fit?.canopy_mae !== undefined) fitBadges.push({ label: "NDVI MAE", value: fit.canopy_mae.toFixed(3) });

  if (!analysis || !selected) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-slate-400">
        <p>{t("twin.noData")}</p>
        <Link to="/" className="rounded-xl bg-agri-400 px-4 py-2 text-sm font-bold text-space-950">
          {t("twin.back")}
        </Link>
      </div>
    );
  }

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.1 } } };
  const rise = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">{t("cmp.title")}</h2>
          <p className="mt-1 text-sm text-slate-400">{t("cmp.subtitle")}</p>
        </div>
        <Link to="/twin" className="flex items-center gap-2 rounded-xl bg-white/5 px-4 py-2 text-sm font-semibold text-agri-400 ring-1 ring-agri-400/30 hover:bg-white/10">
          <Box className="h-4 w-4" />
          {t("cmp.viewTwin")}
        </Link>
      </div>

      <DataBanner className="mb-4" />

      <motion.div variants={stagger} initial="hidden" animate="show" className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        {strategies.map((s, i) => {
          const active = s.id === selected.id;
          const color = COLORS[i % COLORS.length];
          return (
            <motion.article
              key={s.id}
              variants={rise}
              onClick={() => {
                setStrategy(s.id);
              }}
              whileHover={{ y: -4 }}
              className={clsx(
                "glass cursor-pointer rounded-2xl p-5 transition-shadow",
                active && "ring-2",
                s.is_current && "bg-amber-400/5"
              )}
              style={active ? { boxShadow: `0 0 36px ${color}33`, ["--tw-ring-color" as string]: color } : undefined}
            >
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md text-xs font-extrabold text-space-950" style={{ background: color }}>
                      {String.fromCharCode(65 + i)}
                    </span>
                    {s.is_current && (
                      <span className="rounded-full bg-amber-400/15 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-300">{t("cmp.current")}</span>
                    )}
                  </div>
                  <h4 className="mt-2 text-base font-bold leading-snug">{s.name}</h4>
                  <RiskBadge strategy={s} />
                </div>
                <div className="text-right">
                  <div className="text-[10px] uppercase tracking-wider text-slate-500">{t("cmp.score")}</div>
                  <div className="text-2xl font-extrabold tabular-nums" style={{ color }}>
                    {Math.round(s.score)}
                  </div>
                </div>
              </div>
              {s.gaps.filter((g) => g.startsWith("Unrecognized crop")).map((g) => (
                <div key={g} className="mb-3 flex gap-2 rounded-lg border border-amber-400/40 bg-amber-400/10 p-2 text-xs font-semibold text-amber-200">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  {g}
                </div>
              ))}
              {METRICS.map((m) => (
                <BandBar key={m} label={t(`metric.${m}` as Key)} strategy={s} metric={m} lo={ranges[m].lo} hi={ranges[m].hi} color={color} />
              ))}
            </motion.article>
          );
        })}
      </motion.div>

      <motion.div variants={stagger} initial="hidden" animate="show" className="mt-4 grid gap-4 lg:grid-cols-2">
        <motion.div variants={rise}>
          <Panel title={t("cmp.radar")} className="h-full">
            <div className="h-80">
              <ResponsiveContainer>
                <RadarChart data={radarData} outerRadius="72%">
                  <PolarGrid stroke="rgba(148,163,184,0.2)" />
                  <PolarAngleAxis dataKey="axis" tick={{ fill: "#cbd5e1", fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
                  <Radar name="Priorities" dataKey="priority" stroke="#e2e8f0" strokeDasharray="4 4" fill="transparent" />
                  {strategies.map((s, i) => (
                    <Radar key={s.id} name={String.fromCharCode(65 + i)} dataKey={`s${i}`} stroke={COLORS[i % COLORS.length]} fill={COLORS[i % COLORS.length]} fillOpacity={0.15} />
                  ))}
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => v.toFixed(2)} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </motion.div>

        <motion.div variants={rise}>
          <Panel title={t("cmp.heatmap")} className="h-full">
            <div className="overflow-x-auto">
              <div className="min-w-[420px]">
                <div className="mb-1 ml-8 grid grid-cols-12 gap-1 text-center text-[10px] text-slate-500">
                  {months.map((m) => (
                    <span key={m}>{m}</span>
                  ))}
                </div>
                {strategies.map((s, i) => (
                  <div key={s.id} className="mb-1 flex items-center gap-2">
                    <span className="w-6 text-xs font-bold" style={{ color: COLORS[i % COLORS.length] }}>
                      {String.fromCharCode(65 + i)}
                    </span>
                    <div className="grid flex-1 grid-cols-12 gap-1">
                      {s.bare_soil_calendar.map((v, mi) => (
                        <motion.div
                          key={mi}
                          initial={{ opacity: 0, scale: 0.6 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: mi * 0.03 + i * 0.1 }}
                          title={`${months[mi]}: ${Math.round(v * 100)}%`}
                          className="flex h-9 items-center justify-center rounded-md text-[10px] font-semibold text-white/90"
                          style={{ background: `rgba(217,119,6,${0.08 + v * 0.85})` }}
                        >
                          {Math.round(v * 100)}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                ))}
                <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-500">
                  <span>{t("cmp.covered")}</span>
                  <div className="h-1.5 flex-1 rounded-full" style={{ background: "linear-gradient(90deg, rgba(217,119,6,0.08), rgba(217,119,6,0.93))" }} />
                  <span>{t("cmp.bare")}</span>
                </div>
              </div>
            </div>
          </Panel>
        </motion.div>

        <motion.div variants={rise}>
          <Panel title={`${t("cmp.vuln")} - ${selected.name}`} className="h-full">
            <div className="overflow-x-auto">
              <div className="min-w-[420px]">
                <div className="mb-1 ml-28 grid grid-cols-12 gap-1 text-center text-[10px] text-slate-500">
                  {months.map((m) => (
                    <span key={m}>{m}</span>
                  ))}
                </div>
                {VULN_TYPES.map((type) => (
                  <div key={type} className="mb-1 flex items-center gap-2">
                    <span className="w-[104px] text-xs text-slate-300">{t(`vuln.${type}` as Key)}</span>
                    <div className="grid flex-1 grid-cols-12 gap-1">
                      {months.map((_, mi) => {
                        const sev = Math.max(0, ...selected.vulnerability.filter((v) => v.type === type && v.month === mi + 1).map((v) => v.severity));
                        return (
                          <div
                            key={mi}
                            title={`${t(`vuln.${type}` as Key)} ${months[mi]}: ${Math.round(sev * 100)}%`}
                            className="h-7 rounded-md"
                            style={{ background: sev > 0 ? VULN_COLORS[type] : "rgba(148,163,184,0.06)", opacity: sev > 0 ? 0.2 + sev * 0.8 : 1 }}
                          />
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Panel>
        </motion.div>

        <motion.div variants={rise}>
          <Panel title={t(analysis.validation?.ndvi_observed?.length ? "cmp.validationNdvi" : "cmp.validation")} className="h-full">
            <div className="mb-3 flex flex-wrap gap-2">
              {fitBadges.map((b) => (
                <span key={b.label} className="rounded-full bg-white/5 px-2.5 py-1 text-xs font-semibold text-agri-400 ring-1 ring-white/10">
                  {b.label} {b.value}
                </span>
              ))}
            </div>
            {analysis.site.satellite_available === false && (
              <p className="mb-3 rounded-lg bg-amber-300/10 px-3 py-2 text-xs text-amber-300 ring-1 ring-amber-300/20">{t("cmp.nosat")}</p>
            )}
            {smData.length > 0 && (
              <>
                <p className="mb-1 text-xs text-slate-400">{t("cmp.sm")}</p>
                <div className="h-52">
                  <ResponsiveContainer>
                    <LineChart data={smData} margin={{ left: -18, right: 8, top: 4 }}>
                      <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
                      <XAxis dataKey="i" tick={{ fill: "#64748b", fontSize: 10 }} />
                      <YAxis domain={[0, 1]} tick={{ fill: "#64748b", fontSize: 10 }} />
                      <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => v.toFixed(2)} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Line type="monotone" dataKey="obs" name={t("cmp.smObs")} stroke="#38bdf8" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="twin" name={t("cmp.smTwin")} stroke="#4ade80" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
            {(analysis.validation.ndvi_observed?.length ?? 0) > 0 && (
              <div className="mt-3 h-52">
                <ResponsiveContainer>
                  <LineChart data={validationData} margin={{ left: -18, right: 8, top: 4 }}>
                    <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
                    <XAxis dataKey="i" tick={{ fill: "#64748b", fontSize: 10 }} />
                    <YAxis domain={[0, 1]} tick={{ fill: "#64748b", fontSize: 10 }} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => v.toFixed(2)} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Line type="monotone" dataKey="ndvi" name={t("cmp.ndvi")} stroke="#fbbf24" dot={false} strokeWidth={2} />
                    <Line type="monotone" dataKey="canopy" name={t("cmp.canopy")} stroke="#4ade80" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            {soil && (
              <div className="mt-4 rounded-xl bg-white/5 p-3 ring-1 ring-white/10">
                <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-300">{t("soil.title")}</p>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-300">
                  {soil.texture && (<><dt className="text-slate-500">{t("soil.texture")}</dt><dd>{soil.texture}</dd></>)}
                  {soil.awc_mm_per_m !== undefined && (<><dt className="text-slate-500">{t("soil.awc")}</dt><dd>{soil.awc_mm_per_m}</dd></>)}
                  {soil.hydrologic_group && (<><dt className="text-slate-500">{t("soil.hsg")}</dt><dd>{soil.hydrologic_group}</dd></>)}
                  {soil.om_pct !== undefined && (<><dt className="text-slate-500">{t("soil.om")}</dt><dd>{soil.om_pct}%</dd></>)}
                  {soil.source && (<><dt className="text-slate-500">{t("soil.source")}</dt><dd>{soil.source}</dd></>)}
                </dl>
              </div>
            )}
          </Panel>
        </motion.div>

        <motion.div variants={rise}>
          <Panel title={selected.name} className="h-full">
            <Accordion title={t("cmp.why")} items={[selected.why]} defaultOpen />
            <Accordion title={t("cmp.evidence")} items={selected.evidence} />
            <Accordion title={t("cmp.benefits")} items={selected.benefits} />
            <Accordion title={t("cmp.gaps")} items={selected.gaps} />
            <Accordion title={t("cmp.risks")} items={selected.risks} />
          </Panel>
        </motion.div>

        <motion.div variants={rise}>
          <Panel title={t("cmp.narrator")} className="h-full">
            <Narrator analysis={analysis} strategy={selected} />
          </Panel>
        </motion.div>
      </motion.div>

      <div className="mt-4">
        <WhatIfLab analysis={analysis} strategy={selected} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="mt-4 flex gap-4 rounded-2xl border border-amber-400/40 bg-amber-400/10 p-5"
      >
        <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-300" />
        <div>
          <h3 className="font-bold text-amber-200">{t("cmp.gapsBox")}</h3>
          <p className="mt-1 text-sm text-amber-100/80">{t("cmp.gapsBoxText")}</p>
          {selected.gaps.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-sm text-amber-100/70">
              {selected.gaps.map((g) => (
                <li key={g}>{g}</li>
              ))}
            </ul>
          )}
        </div>
      </motion.div>

      <div className="mt-4 pb-4">
        <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-500">
          <Database className="h-3.5 w-3.5" />
          {t("cmp.sources")} - {t("cmp.mode")}: {analysis.site.data_mode}
        </div>
        <div className="flex flex-wrap gap-2">
          {analysis.sources.map((src) => (
            <span key={src.name} title={`${src.dataset} - ${src.use}`} className="rounded-full bg-white/5 px-3 py-1 text-xs text-slate-300 ring-1 ring-white/10">
              {src.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
