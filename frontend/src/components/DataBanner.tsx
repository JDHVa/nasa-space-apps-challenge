import { useState } from "react";
import { AlertTriangle, Database, X } from "lucide-react";
import { useStore } from "../store";
import { useT } from "../i18n";

export function DataBanner({ className }: { className?: string }) {
  const t = useT();
  const analysis = useStore((s) => s.analysis);
  const clicked = useStore((s) => s.clicked);
  const demoMode = useStore((s) => s.demoMode);
  const [dismissed, setDismissed] = useState<string | null>(null);
  if (!analysis) return null;
  const { site } = analysis;
  const key = `${site.lat},${site.lon},${site.data_mode}`;
  const moved = clicked !== null && (Math.abs(site.lat - clicked.lat) > 0.05 || Math.abs(site.lon - clicked.lon) > 0.05);
  if (demoMode) {
    return (
      <span className={`pointer-events-auto inline-flex items-center gap-1.5 rounded-full bg-white/5 px-2.5 py-1 text-[11px] text-slate-300 ring-1 ring-white/10 ${className ?? ""}`}>
        <Database className="h-3 w-3" />
        {t("banner.demoFarm")}
      </span>
    );
  }
  if (site.data_mode === "demo" || moved) {
    if (dismissed === key) return null;
    return (
      <div className={`pointer-events-auto flex items-start gap-2 rounded-xl border border-amber-400/40 bg-amber-400/10 px-3 py-2 text-xs text-amber-200 backdrop-blur ${className ?? ""}`}>
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <span className="flex-1">{t("banner.demo")}</span>
        <button onClick={() => setDismissed(key)} aria-label={t("banner.dismiss")} className="shrink-0 text-amber-300 hover:text-amber-100">
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }
  if (site.data_mode === "cache") {
    return (
      <span className={`pointer-events-auto inline-flex items-center gap-1.5 rounded-full bg-white/5 px-2.5 py-1 text-[11px] text-slate-300 ring-1 ring-white/10 ${className ?? ""}`}>
        <Database className="h-3 w-3" />
        {t("banner.cache")}
      </span>
    );
  }
  return null;
}
