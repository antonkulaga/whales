// Result lanes for one combination: spectrograms with each part's onsets (and contours on the guide),
// onset-strength envelopes, a shared playhead, and per-part timing scores.

import { fileUrl } from "./lib/api.ts";
import type { Manifest, ManifestPart, OutputScores, PhraseEvent, Source, StemName, Timing } from "./lib/types.ts";
import { SPECIES_COLOR } from "./map.ts";

const esc = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
const signed = (z: number | undefined | null) => (z == null ? "—" : `${z > 0 ? "+" : ""}${z.toFixed(1)}`);

const LANES: { key: StemName; title: string; material: string; caption: (m: Manifest) => string }[] = [
  { key: "animal", title: "Animal voices", material: "Recorded", caption: () => "The original recordings, arranged on one timeline." },
  { key: "guide", title: "Combined guide", material: "Constructed from measurements", caption: () => "Measured events rendered in each player's instrument and register." },
  { key: "response", title: "Deterministic response", material: "Constructed", caption: () => "Pads, bass and drums placed on each player's events." },
  { key: "ace", title: "The composition", material: "Generated · ACE-Step 1.5", caption: () => "One musical interpretation generated from the combined guide." },
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

export function renderLanes(container: HTMLElement, manifest: Manifest, onSeek: (t: number) => void, keys?: readonly StemName[]): (t: number | null) => void {
  const parts = manifest.parts;
  container.innerHTML = LANES.filter((lane) => manifest.stems[lane.key] && (!keys || keys.includes(lane.key))).map((lane) => {
    const stem = manifest.stems[lane.key]!;
    const overlay = ticks(parts, manifest.duration_s) + (lane.key === "guide" ? contours(parts, manifest.duration_s, stem.band) : "");
    const scores = lane.key === "response" || lane.key === "ace" ? manifest.scores[lane.key] : undefined;
    return `<div class="lane"><div><span class="material-label">${esc(lane.material)}</span><h3>${esc(lane.title)}</h3><div class="small">${esc(lane.caption(manifest))}</div></div>
      <div><div class="spec" data-lane="${lane.key}" role="slider" tabindex="0" aria-label="Seek in ${esc(lane.title)}" aria-valuemin="0" aria-valuemax="${manifest.duration_s}" aria-valuenow="0"><img src="${esc(fileUrl(stem.image))}" alt="Spectrogram of ${esc(lane.title)}" loading="lazy">
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">${overlay}</svg><div class="playhead"></div></div>${envelope(scores, manifest.duration_s)}</div></div>`;
  }).join("");
  return bindTimeline(container, manifest.duration_s, onSeek);
}

/** Actual source spectrograms, cropped to the selected trims and placed on the piece's timeline. */
export function renderIndividualTracks(container: HTMLElement, manifest: Manifest, sources: ReadonlyMap<string, Source>, onSeek: (t: number) => void): (t: number | null) => void {
  container.innerHTML = manifest.parts.map((part, i) => {
    const source = sources.get(part.source);
    const length = part.trim_s[1] - part.trim_s[0];
    const left = 100 * part.offset_s / manifest.duration_s;
    const width = 100 * length / manifest.duration_s;
    const image = source && length > 0 ? `<img src="${esc(fileUrl(source.files.animal.image))}" alt="Recorded ${esc(part.species)} spectrogram, trimmed to this player's excerpt" style="width:${100 * source.duration_s / length}%;left:${-100 * part.trim_s[0] / length}%" loading="lazy">` : "";
    return `<div class="individual-lane" data-track-part="${i}" style="--c:${partColor(part)}"><div><span class="material-label">Recorded · ${part.offset_s.toFixed(1)}–${(part.offset_s + length).toFixed(1)} s</span><h3>${i + 1} · ${esc(part.species)}</h3><div class="small">${esc(part.location.label)}</div></div>
      <div class="spec" data-lane="part-${i}" role="slider" tabindex="0" aria-label="Seek in recording ${i + 1}: ${esc(part.title)}" aria-valuemin="0" aria-valuemax="${manifest.duration_s}" aria-valuenow="0"><div class="recording-clip" style="left:${left}%;width:${width}%">${image}</div><svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">${ticks([part], manifest.duration_s)}</svg><div class="playhead"></div></div></div>`;
  }).join("") + `<div class="track-ruler" aria-label="Shared time in seconds">${[0, .25, .5, .75, 1].map(fraction => `<span>${(fraction * manifest.duration_s).toFixed(1)} s</span>`).join("")}</div>`;
  return bindTimeline(container, manifest.duration_s, onSeek);
}

function bindTimeline(container: HTMLElement, duration: number, onSeek: (t: number) => void): (t: number | null) => void {
  container.querySelectorAll<HTMLElement>(".spec").forEach((spec) => {
    spec.addEventListener("click", (event) => {
      const box = spec.getBoundingClientRect();
      onSeek(((event.clientX - box.left) / box.width) * duration);
    });
    spec.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const current = Number(spec.getAttribute("aria-valuenow"));
      const next = event.key === "Home" ? 0 : event.key === "End" ? duration - .1 : current + (event.key === "ArrowRight" ? 1 : -1);
      onSeek(Math.max(0, Math.min(duration - .1, next)));
    });
  });
  const heads = [...container.querySelectorAll<HTMLElement>(".playhead")];
  return (t) => {
    for (const head of heads) {
      head.style.display = t == null ? "none" : "block";
      if (t != null) {
        head.style.left = `${((t / duration) * 100).toFixed(3)}%`;
        head.parentElement?.setAttribute("aria-valuenow", t.toFixed(1));
      }
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
    `<p class="small">Timing z compares an output's onset envelope with the measured onsets against the same output shifted in time. In this experiment, z ≈ 3 or above suggests stronger timing alignment; near 0 shows no extra alignment. Source leak is peak waveform correlation with the guide; values ≥ 0.15 flag possible copying.</p>`;
}
