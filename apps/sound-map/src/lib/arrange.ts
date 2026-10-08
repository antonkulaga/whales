// Client-side preview of experiments/follow_combine.plan: same offsets and duration, so the
// timeline the composer draws matches what Python will render. Python stays authoritative.

import type { AceRequest, Arrangement, CombinationLimits, PartDraft, Source, Spec } from "./types.ts";

export interface PlacedPart extends PartDraft {
  index: number;
  start_s: number; // where the part begins on the combined timeline
  length_s: number;
}

export function clamp(value: number, low: number, high: number): number {
  return Math.min(high, Math.max(low, value));
}

export function draftFor(source: Source, offset_s = 0): PartDraft {
  return { source: source.id, offset_s, trim_s: [0, source.duration_s], gain_db: 0, shift_octaves: null };
}

/** Resolve offsets the way Python does: layered parts keep their offsets; sequenced parts follow with a gap. */
export function place(parts: PartDraft[], arrangement: Arrangement, gap_s: number, sources: Map<string, Source>): PlacedPart[] {
  let clock = 0;
  return parts.map((part, index) => {
    const source = sources.get(part.source);
    const duration = source?.duration_s ?? part.trim_s[1];
    const start = clamp(part.trim_s[0], 0, duration);
    const end = clamp(part.trim_s[1], 0, duration);
    const length_s = Math.max(0, end - start);
    const start_s = arrangement === "sequence" ? clock : Math.max(0, part.offset_s);
    clock = start_s + length_s + gap_s;
    return { ...part, index, trim_s: [start, end] as [number, number], start_s, length_s };
  });
}

export function totalDuration(placed: PlacedPart[]): number {
  return placed.length ? Math.max(...placed.map((p) => p.start_s + p.length_s)) + 0.5 : 0;
}

/** Problems the server would reject, in the user's terms; empty when the spec can be sent. */
export function problems(placed: PlacedPart[], limits: CombinationLimits): string[] {
  const out: string[] = [];
  if (!placed.length) out.push("Add at least one recording from the map.");
  if (placed.length > limits.max_parts) out.push(`Use at most ${limits.max_parts} recordings.`);
  placed.forEach((p) => {
    if (p.length_s < limits.min_part_s) out.push(`Part ${p.index + 1} keeps less than ${limits.min_part_s} s after trimming.`);
    if (p.gain_db < limits.gain_db[0] || p.gain_db > limits.gain_db[1])
      out.push(`Part ${p.index + 1} gain must stay between ${limits.gain_db[0]} and ${limits.gain_db[1]} dB.`);
  });
  const duration = totalDuration(placed);
  if (duration > limits.max_duration_s) out.push(`The piece lasts ${duration.toFixed(0)} s; the limit is ${limits.max_duration_s} s.`);
  return out;
}

export function buildSpec(title: string, arrangement: Arrangement, gap_s: number, parts: PartDraft[], ace: AceRequest | null): Spec {
  const resolved = parts.map((p) => ({
    source: p.source,
    offset_s: round(p.offset_s),
    trim_s: [round(p.trim_s[0]), round(p.trim_s[1])] as [number, number],
    gain_db: round(p.gain_db),
    shift_octaves: p.shift_octaves,
  }));
  // Layer order does not change the music. Normalize requests so click order shares a saved piece.
  if (arrangement === "layer") resolved.sort(compareParts);
  return {
    title: title.trim() || undefined,
    arrangement,
    gap_s,
    parts: resolved,
    ace,
  };
}

function compareParts(a: PartDraft, b: PartDraft): number {
  return (a.source < b.source ? -1 : a.source > b.source ? 1 : 0)
    || a.offset_s - b.offset_s || a.trim_s[0] - b.trim_s[0] || a.trim_s[1] - b.trim_s[1]
    || a.gain_db - b.gain_db || (a.shift_octaves ?? -7) - (b.shift_octaves ?? -7);
}

function round(value: number): number {
  return Math.round(value * 1000) / 1000;
}
