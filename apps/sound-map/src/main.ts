// Phrase Atlas: pick sites on the map, compose, combine through the Python engine, then listen while
// each site pulses on its own onsets.

import { Composer } from "./composer.ts";
import { renderLanes, renderScores, partColor } from "./lanes.ts";
import { activePulses, soundingParts } from "./lib/pulses.ts";
import type { Catalog, CombineMessage, ComboSummary, Manifest, Source, StemName } from "./lib/types.ts";
import { AtlasMap, SPECIES_COLOR, sitesOf, type Countries, type Site } from "./map.ts";
import { Player, type Track } from "./player.ts";

const $ = <T extends Element>(selector: string) => document.querySelector(selector) as T;
const esc = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
const PULSE_LIFETIME = 0.9;
const STEM_LABELS: Record<StemName, string> = { animal: "Recordings", guide: "Guide", response: "Response", ace: "ACE-Step" };

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error ?? `${url}: ${response.status}`);
  return response.json() as Promise<T>;
}

const catalog = await json<Catalog>("/api/catalog");
const countries = await json<Countries>(`/files/${catalog.countries}`);
const sites = sitesOf(catalog.sources);
const player = new Player();
const preview = new Audio();
let result: Manifest | null = null;
let showingResult = false;
const stemOn: Record<StemName, boolean> = { animal: true, guide: false, response: false, ace: true };
let partOn: boolean[] = [];
let setPlayhead: (t: number | null) => void = () => {};
let frame = 0;

const map = new AtlasMap($<SVGSVGElement>("#map"), countries, catalog.points, sites, openSite);
// The map shows the draft while composing; a shown result keeps its own arcs until the draft changes.
const composer = new Composer(catalog, (parts) => {
  if (!showingResult || parts.length) {
    showingResult = false;
    map.setCombination(parts);
  }
});

/* ---------- legend and site list ---------- */
$<HTMLElement>("#legend").innerHTML = (Object.keys(SPECIES_COLOR) as (keyof typeof SPECIES_COLOR)[])
  .map((species) => `<span><i class="swatch" style="--c:${SPECIES_COLOR[species]}"></i>${species}</span>`).join("") +
  `<span><i class="swatch" style="--c:var(--muted)"></i>published</span><span><i class="swatch diamond" style="--c:var(--muted)"></i>approximate</span>` +
  `<span><i class="swatch" style="--c:var(--pt-archive);width:6px;height:6px"></i>other datasets</span>`;
$<HTMLElement>("#site-list").innerHTML = sites.map((site, i) =>
  `<li><button type="button" data-site="${i}"><i class="swatch ${site.location.precision === "published" ? "" : "diamond"}" style="--c:${SPECIES_COLOR[site.species]}"></i>${esc(site.location.label)} · ${site.sources.length}</button></li>`).join("");
$<HTMLElement>("#site-list").addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("button[data-site]");
  const site = button && sites[Number(button.dataset.site)];
  if (site) openSite(site);
});

/* ---------- site popover ---------- */
function openSite(site: Site) {
  const popover = $<HTMLElement>("#popover");
  const rows = site.sources.map((source) => `<div class="row"><b>${esc(source.title)}</b>
    <span class="small">${esc(source.id)} · ${source.duration_s.toFixed(1)} s · ${source.onsets_s.length} ${source.material === "clicks" ? "clicks" : "events"}</span>
    <span class="small">${esc(source.note)}</span>
    <div class="row-actions"><button class="btn" type="button" data-listen="${esc(source.id)}">Listen</button>
    <button class="btn add" type="button" data-add="${esc(source.id)}">Add to combination</button></div></div>`).join("");
  popover.innerHTML = `<button class="close" type="button" aria-label="Close">×</button><h3>${esc(site.location.label)}</h3>
    <span class="small">${site.location.precision === "published" ? "Published hydrophone position." : "Approximate site anchor."} ${esc(site.location.note ?? "")}</span>${rows}`;
  popover.hidden = false;
  const box = $<HTMLElement>("#map-box").getBoundingClientRect();
  const at = map.anchor(site);
  const width = Math.min(320, box.width - 20);
  popover.style.left = `${Math.max(10, Math.min(box.width - width - 10, at.x + 14))}px`;
  popover.style.top = `${Math.max(10, Math.min(box.height - popover.offsetHeight - 10, at.y - 30))}px`;
  map.markOpen(site);
  popover.querySelector<HTMLButtonElement>("[data-add]")?.focus();
}
function closeSite() {
  $<HTMLElement>("#popover").hidden = true;
  preview.pause();
  map.markOpen(null);
}
$<HTMLElement>("#popover").addEventListener("click", (event) => {
  const target = (event.target as Element).closest<HTMLButtonElement>("button");
  if (!target) return;
  const source = catalog.sources.find((s) => s.id === (target.dataset.add ?? target.dataset.listen));
  if (target.classList.contains("close")) closeSite();
  else if (source && target.dataset.add) composer.add(source);
  else if (source && target.dataset.listen) listen(source, target);
});
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeSite(); });
$<SVGSVGElement>("#map").addEventListener("click", () => closeSite());

function listen(source: Source, button: HTMLButtonElement) {
  const url = `/files/${source.files.animal.audio}`;
  if (!preview.paused && preview.src.endsWith(url)) {
    preview.pause();
    button.textContent = "Listen";
    return;
  }
  preview.src = url;
  preview.onended = () => { button.textContent = "Listen"; };
  void preview.play();
  document.querySelectorAll<HTMLButtonElement>("[data-listen]").forEach((b) => { b.textContent = "Listen"; });
  button.textContent = "Stop";
}

/* ---------- combine ---------- */
$<HTMLButtonElement>("#combine").addEventListener("click", combine);

async function combine() {
  const button = $<HTMLButtonElement>("#combine");
  const log = $<HTMLPreElement>("#log");
  const spec = composer.spec();
  button.disabled = true;
  button.textContent = spec.ace ? "Combining and generating…" : "Combining…";
  log.hidden = false;
  log.textContent = "";
  $<HTMLElement>("#problems").textContent = "";
  try {
    const response = await fetch(`/api/combine?model=${spec.ace ? 1 : 0}`, { method: "POST", body: JSON.stringify(spec) });
    if (!response.ok || !response.body) throw new Error((await response.json().catch(() => ({}))).error ?? `Server answered ${response.status}`);
    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value;
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines.filter(Boolean)) {
        const message = JSON.parse(line) as CombineMessage;
        if (message.type === "log") log.textContent += message.text + "\n";
        if (message.type === "error") throw new Error(message.message);
        if (message.type === "done") {
          showResult(message.manifest);
          void loadSaved();
        }
        log.scrollTop = log.scrollHeight;
      }
    }
  } catch (error) {
    $<HTMLElement>("#problems").textContent = `Combination failed: ${(error as Error).message}`;
  } finally {
    button.textContent = "Combine";
    button.disabled = composer.problems().length > 0;
  }
}

/* ---------- result and playback ---------- */
function showResult(manifest: Manifest | null) {
  if (!manifest) return;
  stop();
  player.rewind();
  result = manifest;
  showingResult = true;
  partOn = manifest.parts.map(() => true);
  stemOn.ace = Boolean(manifest.stems.ace);
  stemOn.response = !manifest.stems.ace;
  map.setCombination(manifest.parts.map((p) => ({ location: p.location, species: p.species })));
  const section = $<HTMLElement>("#result");
  section.hidden = false;
  $<HTMLElement>("#result-eyebrow").textContent = `${manifest.spec.arrangement} · ${manifest.parts.length} part${manifest.parts.length === 1 ? "" : "s"} · ${manifest.duration_s.toFixed(1)} s · ${manifest.id}`;
  $<HTMLElement>("#result-title").textContent = manifest.title;
  $<HTMLElement>("#result-note").textContent = manifest.interpretation;
  const stems = (Object.keys(STEM_LABELS) as StemName[]).filter((key) => manifest.stems[key]);
  $<HTMLElement>("#stems").innerHTML = "<legend>Listen to</legend>" + stems.map((key) =>
    `<button class="toggle" type="button" data-stem="${key}" aria-pressed="${stemOn[key]}">${STEM_LABELS[key]}</button>`).join("");
  $<HTMLElement>("#part-toggles").innerHTML = "<legend>Parts</legend>" + manifest.parts.map((p, i) =>
    `<button class="toggle" type="button" data-part="${i}" aria-pressed="true" title="Mutes this part's recording and guide"><i class="swatch" style="--c:${partColor(p)}"></i>${i + 1} ${esc(p.source)}</button>`).join("");
  setPlayhead = renderLanes($<HTMLElement>("#lanes"), manifest, (t) => void play(t));
  renderScores($<HTMLElement>("#scores"), manifest);
  $<HTMLElement>("#clock").textContent = `0.0 / ${manifest.duration_s.toFixed(1)} s`;
  if (location.hash.slice(1) !== manifest.id) history.replaceState(null, "", `#${manifest.id}`);
  section.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
}

function gains(): Record<string, number> {
  const out: Record<string, number> = {};
  if (!result) return out;
  result.parts.forEach((_, i) => {
    out[`animal-${i}`] = stemOn.animal && partOn[i] ? 1 : 0;
    out[`guide-${i}`] = stemOn.guide && partOn[i] ? 1 : 0;
  });
  out.response = stemOn.response ? 1 : 0;
  out.ace = stemOn.ace ? 1 : 0;
  return out;
}

function tracks(): Track[] {
  if (!result) return [];
  const g = gains();
  const out: Track[] = result.parts.flatMap((p, i) => [
    { key: `animal-${i}`, url: `/files/${p.files.animal}`, gain: g[`animal-${i}`] ?? 0 },
    { key: `guide-${i}`, url: `/files/${p.files.guide}`, gain: g[`guide-${i}`] ?? 0 },
  ]);
  for (const key of ["response", "ace"] as const) {
    const stem = result.stems[key];
    if (stem) out.push({ key, url: `/files/${stem.audio}`, gain: g[key] ?? 0 });
  }
  return out;
}

async function play(offset?: number) {
  if (!result) return;
  const button = $<HTMLButtonElement>("#play");
  button.textContent = "Loading…";
  try {
    await player.play(tracks(), offset ?? player.time, result.duration_s);
    button.setAttribute("aria-pressed", "true");
    button.textContent = "Pause";
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(tick);
  } catch (error) {
    button.textContent = "Play";
    $<HTMLElement>("#result-note").textContent = `Audio could not load: ${(error as Error).message}`;
  }
}

function stop() {
  player.stop();
  cancelAnimationFrame(frame);
  const button = $<HTMLButtonElement>("#play");
  button.setAttribute("aria-pressed", "false");
  button.textContent = "Play";
  map.clearPlayback();
}

player.onEnded = () => {
  stop();
  setPlayhead(null);
};

function tick() {
  if (!result || !player.playing) return;
  const t = player.time;
  const onsets = result.parts.map((p) => p.onsets_s);
  const spans = result.parts.map((p) => ({ start_s: p.offset_s, length_s: p.trim_s[1] - p.trim_s[0] }));
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  map.setPlayback(reduced ? [] : activePulses(onsets, t, PULSE_LIFETIME, (i) => partOn[i] ?? false), PULSE_LIFETIME,
    soundingParts(spans, t).filter((i) => partOn[i]));
  setPlayhead(t);
  $<HTMLElement>("#clock").textContent = `${t.toFixed(1)} / ${result.duration_s.toFixed(1)} s`;
  frame = requestAnimationFrame(tick);
}

$<HTMLButtonElement>("#play").addEventListener("click", () => (player.playing ? stop() : void play()));
$<HTMLElement>("#stems").addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-stem]");
  if (!button) return;
  const key = button.dataset.stem as StemName;
  stemOn[key] = !stemOn[key];
  button.setAttribute("aria-pressed", String(stemOn[key]));
  for (const [track, gain] of Object.entries(gains())) player.setGain(track, gain);
});
$<HTMLElement>("#part-toggles").addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-part]");
  if (!button) return;
  const i = Number(button.dataset.part);
  partOn[i] = !partOn[i];
  button.setAttribute("aria-pressed", String(partOn[i]));
  for (const [track, gain] of Object.entries(gains())) player.setGain(track, gain);
});

/* ---------- saved combinations ---------- */
async function loadSaved() {
  const saved = await json<ComboSummary[]>("/api/combos").catch(() => []);
  $<HTMLElement>("#saved").innerHTML = saved.length ? saved.map((c) => `<li><button type="button" data-combo="${c.id}"><b>${esc(c.title)}</b>
    <span>${c.sources.map(esc).join(" + ")} · ${c.duration_s.toFixed(0)} s${c.ace ? " · ACE-Step" : ""}</span>
    <span>${new Date(c.created_at_utc).toLocaleString()}</span></button></li>`).join("")
    : `<li class="small">None yet. Combine some recordings and the result appears here.</li>`;
}
$<HTMLElement>("#saved").addEventListener("click", async (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-combo]");
  if (button) showResult(await json<Manifest>(`/api/combos/${button.dataset.combo}`));
});

await loadSaved();

// A bare #<combination id> opens that saved combination, so results can be linked.
async function openFromHash() {
  const id = location.hash.slice(1);
  if (/^[0-9a-f]{12}$/.test(id) && id !== result?.id) showResult(await json<Manifest>(`/api/combos/${id}`).catch(() => null) ?? result!);
}
window.addEventListener("hashchange", () => void openFromHash());
await openFromHash();
