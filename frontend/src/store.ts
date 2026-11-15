import { create } from "zustand";
import type { AnalyzeResponse, Lang, Priorities } from "./api/types";

type State = {
  analysis: AnalyzeResponse | null;
  strategyId: string | null;
  week: number;
  playing: boolean;
  lang: Lang;
  priorities: Priorities;
  rotation: string[];
  location: { lat: number; lon: number } | null;
  clicked: { lat: number; lon: number } | null;
  demoMode: boolean;
  setDemoMode: (d: boolean) => void;
  setAnalysis: (a: AnalyzeResponse) => void;
  setStrategy: (id: string) => void;
  setWeek: (w: number) => void;
  setPlaying: (p: boolean) => void;
  setLang: (l: Lang) => void;
  setPriority: (k: keyof Priorities, v: number) => void;
  setRotation: (r: string[]) => void;
  setLocation: (l: { lat: number; lon: number }) => void;
};

export const useStore = create<State>((set, get) => ({
  analysis: null,
  strategyId: null,
  week: 0,
  playing: true,
  lang: "en",
  priorities: { water: 0.7, nitrogen: 0.5, erosion: 0.6, organic_matter: 0.5, income: 0.6 },
  rotation: ["maize", "wheat"],
  location: null,
  clicked: null,
  demoMode: false,
  setDemoMode: (demoMode) => set({ demoMode }),
  setAnalysis: (analysis) =>
    set({ analysis, clicked: get().location, strategyId: analysis.strategies[0]?.id ?? null, week: 0, playing: true }),
  setStrategy: (strategyId) => set({ strategyId }),
  setWeek: (week) => set({ week }),
  setPlaying: (playing) => set({ playing }),
  setLang: (lang) => set({ lang }),
  setPriority: (k, v) => set((s) => ({ priorities: { ...s.priorities, [k]: v } })),
  setRotation: (rotation) => set({ rotation }),
  setLocation: (location) => set({ location, demoMode: false })
}));
