// Result lanes for one combination: spectrograms with each part's onsets (and contours on the guide),
// onset-strength envelopes, a shared playhead, and per-part timing scores.

import { fileUrl } from "./lib/api.ts";
import type { Manifest, ManifestPart, OutputScores, PhraseEvent, StemName, Timing } from "./lib/types.ts";
import { SPECIES_COLOR } from "./map.ts";

const esc = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
const signed = (z: number | undefined | null) => (z == null ? "—" : `${z > 0 ? "+" : ""}${z.toFixed(1)}`);

const LANES: { key: StemName; title: string; caption: (m: Manifest) => string }[] = [
  { key: "animal", title: "Recordings", caption: () => "Each recording at its place on the timeline." },
  { key: "guide", title: "Combined guide", caption: () => "Each part's measured events in its own instrument and register." },
  { key: "response", title: "Deterministic response", caption: () => "No model: pads, bass and drums on every part's events." },
  { key: "ace", title: "ACE-Step", caption: (m) => m.ace ? `${m.ace.task} of the combined guide · strength ${m.ace.audio_cover_strength} · seed ${m.ace.seed}` : "" },
];

export function partColor(part: ManifestPart): string {
  return SPECIES_COLOR[part.species];
}

function ticks(parts: ManifestPart[], duration: number): string {
  const rows = Math.max(1, parts.length);
  const height = Math.min(9, 36 / rows);
  return parts.map((part, i) => part.onsets_s.map((t) => {
    const x = (t / duration) * 1000;
    return `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${i * height}" y2="${(i + 1) * height - 1}" stroke="${partColor(part)}" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`;
  }).join("")).join("");
}

function contours(parts: ManifestPart[], duration: number, band: [number, number]): string {
  const y = (hz: number) => Math.max(0, Math.min(100, 100 * (1 - Math.log(hz / band[0]) / Math.log(band[1] / band[0]))));
  return parts.map((part) => part.events.filter((e): e is Extract<PhraseEvent, { k: "t" }> => e.k === "t").map((e) => {
    const factor = 2 ** part.shift_octaves;
    const points = e.c.map(([t, hz]) => `${((t / duration) * 1000).toFixed(1)},${y(hz * factor).toFixed(1)}`).join(" ");
    return `<polyline points="${points}" fill="none" stroke="${partColor(part)}" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`;
  }).join("")).join("");
}

function envelope(scores: OutputScores | undefined, duration: number): string {
  if (!scores) return "";
  const points = scores.envelope.map((v, i) => `${((i / scores.envelope_rate_hz / duration) * 1000).toFixed(1)},${(24 - (Math.max(0, Math.min(6, v + 1)) / 7) * 22).toFixed(1)}`).join(" ");
  return `<svg class="env" viewBox="0 0 1000 24" preserveAspectRatio="none" aria-hidden="true"><polyline points="${points}" vector-effect="non-scaling-stroke"/></svg>`;
}

export function renderLanes(container: HTMLElement, manifest: Manifest, onSeek: (t: number) => void): (t: number | null) => void {
  const parts = manifest.parts;
  container.innerHTML = LANES.filter((lane) => manifest.stems[lane.key]).map((lane) => {
    const stem = manifest.stems[lane.key]!;
    const overlay = ticks(parts, manifest.duration_s) + (lane.key === "guide" || lane.key === "ace" ? contours(parts, manifest.duration_s, stem.band) : "");
    const scores = lane.key === "response" || lane.key === "ace" ? manifest.scores[lane.key] : undefined;
    return `<div class="lane"><div><h3>${esc(lane.title)}</h3><div class="small">${esc(lane.caption(manifest))}</div></div>
      <div><div class="spec" data-lane="${lane.key}"><img src="${esc(fileUrl(stem.image))}" alt="Spectrogram of ${esc(lane.title)}" loading="lazy">
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">${overlay}</svg><div class="playhead"></div></div>${envelope(scores, manifest.duration_s)}</div></div>`;
  }).join("");
  container.querySelectorAll<HTMLElement>(".spec").forEach((spec) => spec.addEventListener("click", (event) => {
    const box = spec.getBoundingClientRect();
    onSeek(((event.clientX - box.left) / box.width) * manifest.duration_s);
  }));
  const heads = [...container.querySelectorAll<HTMLElement>(".playhead")];
  return (t) => {
    for (const head of heads) {
      head.style.display = t == null ? "none" : "block";
      if (t != null) head.style.left = `${((t / manifest.duration_s) * 100).toFixed(3)}%`;
    }
  };
}

function chip(label: string, timing: Timing | null, color?: string): string {
  const z = timing?.z;
  return `<span class="chip ${z != null && z >= 3 ? "good" : ""}" ${color ? `style="--c:${color}"` : ""}>${esc(label)} z ${signed(z)}</span>`;
}

export function renderScores(container: HTMLElement, manifest: Manifest) {
  const rows = (["response", "ace"] as const).flatMap((key) => {
    const scores = manifest.scores[key];
    if (!scores) return [];
    const title = key === "response" ? "Deterministic response" : "ACE-Step";
    const parts = manifest.parts.map((p, i) => chip(`${i + 1} ${p.source}`, scores.parts[i] ?? null, partColor(p))).join("");
    const leak = scores.leakage != null ? `<span class="chip">source leak ${scores.leakage.toFixed(2)}</span>` : "";
    return [`<div class="score-row"><b>${title}</b>${parts}${chip("all onsets", scores.all)}${leak}</div>`];
  });
  container.innerHTML = rows.join("") +
    `<p class="small">Timing z compares each output's onset envelope with one part's onsets against the same output shifted in time. From z ≈ 3 the music follows that part; near 0 it ignores it. Source leak ≥ 0.15 means the output partly copies the guide.</p>`;
}
