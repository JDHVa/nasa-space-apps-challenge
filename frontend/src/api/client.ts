import demoIowa from "../data/demo_iowa.json";
import demoBajio from "../data/demo_bajio.json";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ExplainRequest,
  WhatIfRequest,
  WhatIfResponse
} from "./types";

const API_BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init: RequestInit | undefined, timeoutMs: number): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...init
    });
    if (!response.ok) throw new Error(`API ${response.status}`);
    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export type DemoFarm = "iowa" | "bajio";

export async function fetchDemo(farm?: DemoFarm): Promise<AnalyzeResponse> {
  try {
    return await request<AnalyzeResponse>(farm ? `/demo?farm=${farm}` : "/demo", undefined, 8000);
  } catch {
    if (farm === "iowa") return demoIowa as unknown as AnalyzeResponse;
    if (farm === "bajio") return demoBajio as unknown as AnalyzeResponse;
    return demoIowa as unknown as AnalyzeResponse;
  }
}

export async function analyze(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  try {
    return await request<AnalyzeResponse>(
      "/analyze",
      { method: "POST", body: JSON.stringify(payload) },
      120000
    );
  } catch {
    return fetchDemo();
  }
}

export async function whatIf(payload: WhatIfRequest): Promise<WhatIfResponse | null> {
  try {
    return await request<WhatIfResponse>("/whatif", { method: "POST", body: JSON.stringify(payload) }, 20000);
  } catch {
    return null;
  }
}

export async function explainStream(
  payload: ExplainRequest,
  onChunk: (text: string) => void
): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok || !response.body) return false;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      onChunk(decoder.decode(value, { stream: true }));
    }
    return true;
  } catch {
    return false;
  }
}
