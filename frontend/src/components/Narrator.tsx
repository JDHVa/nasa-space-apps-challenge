import { useEffect, useRef, useState } from "react";
import { Brain, Loader2 } from "lucide-react";
import { explainStream } from "../api/client";
import type { AnalyzeResponse, Strategy } from "../api/types";
import { useT } from "../i18n";
import { useStore } from "../store";

export function Narrator({ analysis, strategy }: { analysis: AnalyzeResponse; strategy: Strategy }) {
  const t = useT();
  const lang = useStore((s) => s.lang);
  const [shown, setShown] = useState("");
  const [loading, setLoading] = useState(false);
  const [fail, setFail] = useState(false);
  const [typing, setTyping] = useState(false);
  const bufferRef = useRef("");
  const doneRef = useRef(true);
  const tokenRef = useRef(0);

  const run = async () => {
    const token = ++tokenRef.current;
    bufferRef.current = "";
    doneRef.current = false;
    setShown("");
    setFail(false);
    setLoading(true);
    setTyping(true);
    const ok = await explainStream({ strategy_id: strategy.id, analysis, lang }, (chunk) => {
      if (tokenRef.current === token) bufferRef.current += chunk;
    });
    if (tokenRef.current !== token) return;
    doneRef.current = true;
    setLoading(false);
    if (!ok && bufferRef.current.length === 0) {
      setFail(true);
      setTyping(false);
    }
  };

  useEffect(() => {
    void run();
    return () => {
      tokenRef.current++;
    };
  }, [strategy.id, lang]);

  useEffect(() => {
    if (!typing) return;
    const id = setInterval(() => {
      setShown((prev) => {
        const buf = bufferRef.current;
        if (prev.length < buf.length) {
          const step = Math.max(1, Math.ceil((buf.length - prev.length) / 40));
          return buf.slice(0, prev.length + step);
        }
        if (doneRef.current) setTyping(false);
        return prev;
      });
    }, 22);
    return () => clearInterval(id);
  }, [typing]);

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-2 rounded-full bg-agri-400/10 px-3 py-1 text-[11px] font-semibold text-agri-400 ring-1 ring-agri-400/30">
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Brain className="h-3.5 w-3.5" />}
          {t("cmp.narratorLabel")}
        </span>
        <button
          onClick={() => void run()}
          disabled={loading || typing}
          className="rounded-lg bg-white/5 px-3 py-1 text-xs font-semibold text-slate-200 ring-1 ring-white/10 hover:bg-white/10 disabled:opacity-50"
        >
          {t("cmp.narrate")}
        </button>
      </div>
      <div className="min-h-[120px] whitespace-pre-wrap rounded-xl bg-black/25 p-4 text-sm leading-relaxed text-slate-200">
        {fail ? `${t("cmp.narratorFail")}\n\n${strategy.why}` : shown || (loading ? t("cmp.narrating") : "")}
        {(typing || loading) && !fail && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-agri-400 align-middle" />}
      </div>
    </div>
  );
}
