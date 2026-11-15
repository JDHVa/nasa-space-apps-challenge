import { AlertTriangle } from "lucide-react";
import type { Strategy } from "../api/types";
import { useT } from "../i18n";
import { rainfedWinterRisk } from "../twin/risk";

export function RiskBadge({ strategy }: { strategy: Strategy }) {
  const t = useT();
  if (!rainfedWinterRisk(strategy)) return null;
  const text = t("risk.winter");
  return (
    <span
      title={text}
      aria-label={text}
      className="group relative mt-1 inline-flex cursor-help items-center gap-1 rounded-full bg-amber-400/15 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-300 ring-1 ring-amber-400/40"
    >
      <AlertTriangle className="h-3 w-3" />
      {t("risk.label")}
      <span className="pointer-events-none absolute left-0 top-full z-50 mt-1 hidden w-56 rounded-lg border border-amber-400/40 bg-space-950/95 p-2 text-[11px] font-medium normal-case text-amber-100 group-hover:block">
        {text}
      </span>
    </span>
  );
}
