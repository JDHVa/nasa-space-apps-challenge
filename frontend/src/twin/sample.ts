import type { DailyPoint } from "../api/types";

export type Sample = { crop: string | null; canopy: number; moisture: number; rain: number; et: number };

const EMPTY: Sample = { crop: null, canopy: 0, moisture: 0.4, rain: 0, et: 0 };

export function sampleAt(points: DailyPoint[], week: number): Sample {
  if (points.length === 0) return EMPTY;
  const clamped = Math.max(0, Math.min(points.length - 1, week));
  const i = Math.floor(clamped);
  const j = Math.min(points.length - 1, i + 1);
  const f = clamped - i;
  const a = points[i];
  const b = points[j];
  return {
    crop: f < 0.5 ? a.crop : b.crop,
    canopy: a.canopy + (b.canopy - a.canopy) * f,
    moisture: a.soil_moisture + (b.soil_moisture - a.soil_moisture) * f,
    rain: a.rain_mm + (b.rain_mm - a.rain_mm) * f,
    et: a.et_mm + (b.et_mm - a.et_mm) * f
  };
}

export function weekToMonthYear(week: number): { month: number; year: number } {
  const w = Math.max(0, week);
  const year = Math.floor(w / 52);
  const month = Math.min(11, Math.floor(((w % 52) / 52) * 12));
  return { month, year };
}
