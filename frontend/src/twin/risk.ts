import type { Strategy } from "../api/types";

export function rainfedWinterRisk(s: Strategy): boolean {
  const winter = s.rotation.some((r) => r.start_month > r.end_month || r.start_month >= 11);
  if (!winter) return false;
  return s.metrics.irrigation_need_mm.p50 > 20 || s.metrics.water_stress_days.p50 > 8;
}
