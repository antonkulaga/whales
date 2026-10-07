// Whale and Dolphin Orchestra: seat recordings from the map, compose them through the Python engine
// (ACE-Step on the combined guide), then listen while each site pulses on its own calls.

import { Composer } from "./composer.ts";
import { renderIndividualTracks, renderLanes, renderScores, partColor } from "./lanes.ts";
import { catalogUrl, comboUrl, combosUrl, fileUrl, isStatic } from "./lib/api.ts";
import { activePulses, soundingParts } from "./lib/pulses.ts";
import type { Catalog, CombineMessage, ComboSummary, Manifest, Source, Species, StemName } from "./lib/types.ts";
import { AtlasMap, SPECIES_COLOR, sitesOf, type Countries, type MapPart, type Site } from "./map.ts";
import { Player, type Track } from "./player.ts";
import "./silver.ts"; // the Sound to silver tab: its idea tabs and images

const $ = <T extends Element>(selector: string) => document.querySelector(selector) as T;
const esc = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const PULSE_LIFETIME = 0.9;
const STEM_LABELS: Record<StemName, string> = { animal: "Recorded voices", guide: "Musical guide", response: "Constructed response", ace: "Generated music" };
const SPECIES_ICON: Record<Species, string> = { humpback: "humpback", dolphin: "dolphin", "sperm whale": "sperm-whale", "killer whale": "killer-whale" };
const SEAT_LABEL: Record<Species, string> = { humpback: "Humpback", dolphin: "Dolphin", "sperm whale": "Sperm whale", "killer whale": "Orca" };
let result: Manifest | null = null;
$<HTMLImageElement>("#hall-image").src = fileUrl("concert-hall-atlas-v1.png");

/* ---------- listening programme beside the map ---------- */
const programmeToggle = $<HTMLButtonElement>("#programme-toggle");
function setProgrammeOpen(open: boolean) {
  programmeToggle.setAttribute("aria-expanded", String(open));
  programmeToggle.title = open ? "Collapse the listening programme" : "Expand the listening programme";
  $("#programme-panel").toggleAttribute("hidden", !open);
  $("#map-workspace").classList.toggle("programme-collapsed", !open);
}
setProgrammeOpen(!matchMedia("(max-width: 850px)").matches);
programmeToggle.addEventListener("click", () => setProgrammeOpen(programmeToggle.getAttribute("aria-expanded") !== "true"));
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && programmeToggle.getAttribute("aria-expanded") === "true" && document.activeElement?.closest(".programme-drawer")) {
    setProgrammeOpen(false);
    programmeToggle.focus();
  }
});

/* ---------- accessible project views ---------- */
type View = "concert" | "technical" | "installation" | "silver" | "about";
const VIEWS: View[] = ["concert", "technical", "installation", "silver", "about"];
// Server-only tabs (Sound to silver) are hidden in the static copy, so keys and URLs never land on them there.
const viewTabs = [...document.querySelectorAll<HTMLButtonElement>("[role=tab][data-view]")]
  .filter((tab) => !(isStatic && tab.hasAttribute("data-server-only")));
// About and Installation photos live with the demo media; lazy loading waits until their panel is shown.
for (const img of document.querySelectorAll<HTMLImageElement>("img[data-file]")) img.src = fileUrl(img.dataset.file!);
// Links to server routes (such as /silver) have no target in the static copy.
if (isStatic) for (const link of document.querySelectorAll<HTMLElement>("[data-server-only]")) link.hidden = true;
function showView(view: View, scroll = false) {
  for (const tab of viewTabs) {
    const active = tab.dataset.view === view;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  }
  for (const name of VIEWS) $(`#${name}-panel`).toggleAttribute("hidden", view !== name);
  const url = new URL(location.href);
  if (view === "concert") url.searchParams.delete("view");
  else url.searchParams.set("view", view);
  history.replaceState(null, "", url);
  if (scroll) {
    $<HTMLElement>(`#${view}-panel`).scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
    $<HTMLButtonElement>(`#${view}-tab`).focus({ preventScroll: true });
  }
}
for (const tab of viewTabs) tab.addEventListener("click", () => showView(tab.dataset.view as View));
for (const tab of viewTabs) tab.addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const index = event.key === "Home" ? 0 : event.key === "End" ? viewTabs.length - 1 : (viewTabs.indexOf(tab) + (event.key === "ArrowRight" ? 1 : viewTabs.length - 1)) % viewTabs.length;
  const next = viewTabs[index]!;
  next.focus();
  showView(next.dataset.view as View);
});
document.addEventListener("click", (event) => {
  const target = (event.target as Element).closest<HTMLElement>("[data-show-technical], [data-show-concert], [data-show-view]");
  if (!target) return;
  event.preventDefault();
  showView((target.dataset.showView as View | undefined) ?? (target.hasAttribute("data-show-technical") ? "technical" : "concert"), true);
});
const requestedView = new URL(location.href).searchParams.get("view") as View | null;
const reachable = (view: View | null): view is View => Boolean(view && viewTabs.some((tab) => tab.dataset.view === view));
showView(reachable(requestedView) ? requestedView : "concert");

function loadError(error: unknown): never {
  const note = $<HTMLElement>("#load-error");
  note.hidden = false;
  note.textContent = `The recordings could not load. Please reload the page. ${(error as Error).message}`;
  throw error;
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error ?? `${url}: ${response.status}`);
  return response.json() as Promise<T>;
}

const catalog = await json<Catalog>(catalogUrl()).catch(loadError);
const countries = await json<Countries>(fileUrl(catalog.countries)).catch(loadError);
const sites = sitesOf(catalog.sources);
const sourceById = new Map(catalog.sources.map((s) => [s.id, s]));
const siteOf = new Map(sites.flatMap((site) => site.sources.map((s) => [s.id, site] as const)));
const player = new Player();
const preview = new Audio();
let pieceKey: string | null = null; // the orchestra spec the piece on screen was made from
const rendered = new Map<string, string>(); // orchestra spec → piece id, for every piece composed or opened this session
let busy = false;
let flash = "";
let flashTimer = 0;
let openSiteKey: string | null = null;
const stemOn: Record<StemName, boolean> = { animal: true, guide: false, response: false, ace: true };
let partOn: boolean[] = [];
let setPlayhead: (t: number | null) => void = () => {};
let setIndividualPlayhead: (t: number | null) => void = () => {};
let frame = 0;
let setTechnicalPlayhead: (t: number | null) => void = () => {};

const technicalSource = $<HTMLSelectElement>("#technical-source");
technicalSource.innerHTML = catalog.sources.map((source) => `<option value="${esc(source.id)}">${esc(source.title)} · ${esc(capital(source.species))}</option>`).join("");
function renderMeasurement(source: Source) {
  preview.pause();
  resetPreview();
  const ticks = source.onsets_s.map((t) => `<line x1="${(t / source.duration_s * 1000).toFixed(1)}" x2="${(t / source.duration_s * 1000).toFixed(1)}" y1="0" y2="12" stroke="${SPECIES_COLOR[source.species]}" stroke-width="1.5" vector-effect="non-scaling-stroke"/>`).join("");
  const overlay = (band: [number, number], shift: number) => ticks + source.events.map((event) => {
    if (event.k !== "t") return "";
    const points = event.c.map(([t, hz]) => {
      const y = Math.max(0, Math.min(100, 100 * (1 - Math.log(hz * 2 ** shift / band[0]) / Math.log(band[1] / band[0]))));
      return `${(t / source.duration_s * 1000).toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    return `<polyline points="${points}" fill="none" stroke="${SPECIES_COLOR[source.species]}" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`;
  }).join("");
  const card = (stem: "animal" | "guide", label: string, title: string) => {
    const file = source.files[stem];
    return `<article class="example-card"><div class="example-head"><div><span class="section-number">${label}</span><h3>${title}</h3></div><button class="btn" type="button" data-example-listen="${esc(source.id)}" data-stem="${stem}" data-label="▶ Listen" aria-label="Listen to ${stem === "animal" ? "recording" : "musical guide"}: ${esc(source.title)}" aria-pressed="false">▶ Listen</button></div><div class="example-spec"><img src="${esc(fileUrl(file.image))}" alt="${stem === "animal" ? "Recording" : "Musical guide"} spectrogram for ${esc(source.title)}"><svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">${overlay(file.band, stem === "guide" ? source.register_shift_octaves : 0)}</svg></div><div class="spec-axis"><span>0 s → ${source.duration_s.toFixed(0)} s</span><span>${file.band[0]}–${file.band[1]} Hz · log scale</span></div></article>`;
  };
  $("#measurement-example").innerHTML = `<div class="example-grid">${card("animal", "Input / Recorded audio", "The animal's voice")}${card("guide", "Guide / Constructed audio", "The measured phrase, played")}</div><div class="measurement-meta"><span><span class="small">Recording site</span><b>${esc(source.location.label)}</b></span><span><span class="small">Measured material</span><b>${source.onsets_s.length} ${source.material === "clicks" ? "click onsets" : "call onsets"}</b></span><span><span class="small">Guide instrument</span><b>${esc(source.instrument)}</b></span><span><span class="small">Register shift</span><b>${source.register_shift_octaves} octaves</b></span></div><p class="measurement-note">${esc(source.note)} Coloured ticks mark measured onsets${source.material === "tonal" ? "; lines trace measured pitch contours" : "; click groups become sequences of mallet strikes"}. The guide changes the sound while preserving those event times.</p>`;
}
technicalSource.addEventListener("change", () => {
  const source = sourceById.get(technicalSource.value);
  if (source) renderMeasurement(source);
});
if (catalog.sources[0]) renderMeasurement(catalog.sources[0]);
$("#measurement-example").addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-example-listen]");
  const source = button && sourceById.get(button.dataset.exampleListen ?? "");
  if (button && source) listen(source, button, button.dataset.stem === "guide" ? "guide" : "animal");
});
$<HTMLElement>("#catalog-summary").textContent = `${catalog.sources.length} recordings / ${sites.length} sites / ${new Set(catalog.sources.map((s) => s.species)).size} species`;
$<HTMLButtonElement>("#hear-piece").addEventListener("click", async () => {
  const first = [...summaries.values()].find((p) => p.preset && p.ace) ?? [...summaries.values()].find((p) => p.ace) ?? [...summaries.values()][0];
  if (result) { showView("concert"); $("#result").scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" }); void play(); }
  else if (first) await openPiece(first.id);
});

const map = new AtlasMap($<SVGSVGElement>("#map"), countries, catalog.points, sites, clickSite);
let composer: Composer | undefined;
composer = new Composer(catalog, () => orchestraChanged());

/* ---------- legend and zoom presets ---------- */
$<HTMLElement>("#legend").innerHTML = (Object.keys(SPECIES_COLOR) as (keyof typeof SPECIES_COLOR)[])
  .map((species) => `<span><i class="swatch" style="--c:${SPECIES_COLOR[species]}"></i>${species}</span>`).join("") +
  `<span><i class="swatch" style="--c:var(--muted)"></i>published position</span><span><i class="swatch diamond" style="--c:var(--muted)"></i>approximate</span>` +
  `<span><i class="swatch halo"></i>in the orchestra</span><span><i class="swatch" style="--c:var(--pt-archive);width:6px;height:6px"></i>other datasets, not playable</span>`;

const near = (lon0: number, lon1: number, lat0: number, lat1: number) =>
  sites.filter((s) => s.location.lon >= lon0 && s.location.lon <= lon1 && s.location.lat >= lat0 && s.location.lat <= lat1);
const zooms: { label: string; sites: Site[] | null }[] = [
  { label: "All sites", sites },
  { label: "North-east Pacific", sites: near(-170, -110, 40, 70) },
  { label: "Salish Sea", sites: near(-123.8, -122, 47.6, 49.3) },
  { label: "World", sites: null },
].filter((z) => !z.sites || z.sites.length >= 2);
$<HTMLElement>("#zooms").innerHTML = zooms.map((z, i) => `<button class="zoom" type="button" data-zoom="${i}" aria-pressed="${i === 0}">${esc(z.label)}</button>`).join("");
$<HTMLElement>("#zooms").addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-zoom]");
  if (!button) return;
  map.fit(zooms[Number(button.dataset.zoom)]!.sites);
  document.querySelectorAll("#zooms [data-zoom]").forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
});
map.fit(sites);

/* ---------- recordings list ---------- */
// Spectrogram thumbnails carry the onsets our audio analysis measured, so the list shows data, not decoration.
function onsetTicks(source: Source): string {
  return source.onsets_s.map((t) => {
    const x = ((t / source.duration_s) * 1000).toFixed(1);
    return `<line x1="${x}" x2="${x}" y1="0" y2="22"/>`;
  }).join("");
}

$<HTMLElement>("#roster-count").textContent = `${catalog.sources.length} recordings · ${sites.length} sites`;
$<HTMLElement>("#roster").innerHTML = sites.map((site) => `<li class="roster-site" data-site="${esc(site.key)}">
  <h3>${esc(site.location.label)}</h3>
  <ul>${site.sources.map((source) => `<li class="rec" data-id="${esc(source.id)}" style="--c:${SPECIES_COLOR[source.species]}">
    <button class="rec-main" type="button" data-toggle="${esc(source.id)}" aria-pressed="false">
      <span class="seat" aria-hidden="true">+</span>
      <span class="rec-text"><b>${esc(source.title)}</b><span>${esc(capital(source.species))} · ${source.duration_s.toFixed(0)} s · ${source.onsets_s.length} ${source.material === "clicks" ? "clicks" : "calls"}</span></span>
    </button>
    <button class="listen" type="button" data-listen="${esc(source.id)}" data-label="▶" aria-label="Listen to ${esc(source.title)}">▶</button>
    <span class="thumb" aria-hidden="true"><img src="${esc(fileUrl(source.files.animal.image))}" alt="" loading="lazy"><svg viewBox="0 0 1000 22" preserveAspectRatio="none">${onsetTicks(source)}</svg></span>
  </li>`).join("")}</ul></li>`).join("");

$<HTMLElement>("#roster").addEventListener("click", (event) => {
  const target = (event.target as Element).closest<HTMLButtonElement>("button");
  const source = target && sourceById.get(target.dataset.toggle ?? target.dataset.listen ?? "");
  if (!target || !source) return;
  if (target.dataset.toggle) toggle(source);
  else listen(source, target);
});
$<HTMLElement>("#roster").addEventListener("pointerover", (event) => {
  const item = (event.target as Element).closest<HTMLElement>(".roster-site");
  map.highlight(item?.dataset.site ?? null);
});
$<HTMLElement>("#roster").addEventListener("pointerleave", () => map.highlight(null));

/* ---------- seating ---------- */
function toggle(source: Source) {
  if (isStatic || !composer) return;
  if (!composer.has(source.id) && composer.full) {
    say(`All ${composer.max} seats are taken. Remove a player first.`);
    return;
  }
  composer.toggle(source);
}

function seatAll(site: Site) {
  if (!composer) return;
  for (const source of site.sources) if (!composer.has(source.id) && !composer.add(source)) break;
  if (site.sources.some((s) => !composer!.has(s.id))) say(`All ${composer.max} seats are taken.`);
}

/** One recording at a site: a click seats or removes it. Several: a small menu lists them. */
function clickSite(site: Site) {
  if (!isStatic && site.sources.length === 1) {
    closeSite();
    toggle(site.sources[0]!);
    return;
  }
  openSite(site);
}

function openSite(site: Site) {
  openSiteKey = site.key;
  const popover = $<HTMLElement>("#popover");
  const seatedHere = site.sources.filter((s) => composer?.has(s.id)).length;
  const rows = site.sources.map((source) => {
    const seated = composer?.has(source.id) ?? false;
    return `<div class="row" style="--c:${SPECIES_COLOR[source.species]}"><b>${esc(source.title)}</b>
    <span class="small">${esc(capital(source.species))} · ${source.duration_s.toFixed(0)} s · ${source.onsets_s.length} ${source.material === "clicks" ? "clicks" : "calls"} · ${esc(source.note)}</span>
    <div class="row-actions"><button class="btn" type="button" data-listen="${esc(source.id)}" data-label="Listen">Listen</button>
    ${isStatic ? "" : `<button class="btn ${seated ? "seated" : "add"}" type="button" data-toggle="${esc(source.id)}" aria-pressed="${seated}">${seated ? "✓ In the orchestra · remove" : "+ Seat"}</button>`}</div></div>`;
  }).join("");
  const all = !isStatic && seatedHere < site.sources.length
    ? `<button class="btn add" type="button" data-all>+ Seat all ${site.sources.length}</button>` : "";
  popover.innerHTML = `<button class="close" type="button" aria-label="Close">×</button><h3>${esc(site.location.label)}</h3>
    <span class="small">${site.location.precision === "published" ? "Published hydrophone position." : "Approximate site anchor."} ${esc(site.location.note ?? "")}</span>${all}${rows}`;
  const wasHidden = popover.hidden;
  popover.hidden = false;
  const box = $<HTMLElement>("#map-box").getBoundingClientRect();
  const at = map.anchor(site);
  const width = Math.min(340, box.width - 20);
  popover.style.left = `${Math.max(10, Math.min(box.width - width - 10, at.x + 16))}px`;
  popover.style.top = `${Math.max(10, Math.min(box.height - popover.offsetHeight - 10, at.y - 30))}px`;
  map.markOpen(site);
  if (wasHidden) popover.querySelector<HTMLButtonElement>("[data-toggle], [data-listen]")?.focus();
}

function closeSite() {
  openSiteKey = null;
  $<HTMLElement>("#popover").hidden = true;
  map.markOpen(null);
}

$<HTMLElement>("#popover").addEventListener("click", (event) => {
  const target = (event.target as Element).closest<HTMLButtonElement>("button");
  if (!target) return;
  const site = sites.find((s) => s.key === openSiteKey);
  const source = sourceById.get(target.dataset.toggle ?? target.dataset.listen ?? "");
  if (target.classList.contains("close")) closeSite();
  else if (target.dataset.all !== undefined && site) seatAll(site);
  else if (source && target.dataset.toggle) toggle(source);
  else if (source && target.dataset.listen) listen(source, target);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeSite();
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && !isStatic) { event.preventDefault(); void compose(); }
});
$<SVGSVGElement>("#map").addEventListener("click", () => closeSite());

function resetPreview() {
  document.querySelectorAll<HTMLButtonElement>("[data-listen], [data-example-listen]").forEach((button) => {
    button.textContent = button.dataset.label ?? "Listen";
    button.classList.remove("playing");
    button.setAttribute("aria-pressed", "false");
  });
}

function listen(source: Source, button: HTMLButtonElement, stem: "animal" | "guide" = "animal") {
  const url = fileUrl(source.files[stem].audio);
  if (!preview.paused && preview.src.endsWith(url)) {
    preview.pause();
    resetPreview();
    return;
  }
  if (player.playing) stop();
  resetPreview();
  preview.src = url;
  preview.onended = resetPreview;
  void preview.play().catch(() => {
    resetPreview();
    playbackError("The audio could not load. Please try again.");
  });
  button.textContent = button.dataset.label === "▶" ? "■" : "Stop";
  button.classList.add("playing");
  button.setAttribute("aria-pressed", "true");
}

function playbackError(message: string) {
  const note = $<HTMLElement>("#load-error");
  note.hidden = false;
  note.textContent = message;
}

function pieceTitle(title: string, sources: string[]): string {
  if (title !== sources.join(" + ")) return title;
  return [...new Set(sources.map((id) => sourceById.get(id)?.species ?? id))].map(capital).join(" & ") + " ensemble";
}

/* ---------- the orchestra dock ---------- */
function orchestraChanged() {
  if (!composer) return;
  const ids = composer.ids();
  map.setSeated(new Set(ids.map((id) => siteOf.get(id)?.key ?? "")));
  map.setCombination(composer.mapParts());
  document.querySelectorAll<HTMLElement>("#roster .rec").forEach((item) => {
    const seat = ids.indexOf(item.dataset.id ?? "");
    item.classList.toggle("seated", seat >= 0);
    item.querySelector(".rec-main")!.setAttribute("aria-pressed", String(seat >= 0));
    item.querySelector(".seat")!.textContent = seat >= 0 ? String(seat + 1) : "+";
  });
  const open = sites.find((s) => s.key === openSiteKey);
  if (open) openSite(open);
  if (flash && ids.length) flash = "";
  renderDock();
}

function renderDock() {
  if (!composer) return;
  const ids = composer.ids();
  $("#dock").classList.toggle("empty-ensemble", ids.length === 0 && !result);
  renderHallSeats(isStatic && result ? result.parts.map((part) => part.source) : ids);
  $<HTMLElement>("#seats").textContent = `${ids.length} of ${composer.max} seats`;
  $<HTMLElement>("#players").innerHTML = ids.length ? ids.map((id, i) => {
    const source = sourceById.get(id)!;
    return `<li class="player" data-id="${esc(id)}" style="--c:${SPECIES_COLOR[source.species]}" title="${esc(source.title)}">
      <span class="seat">${i + 1}</span><span class="who"><b>${esc(capital(source.species))}</b><span>${esc(source.location.label)}</span></span>
      <button class="x" type="button" data-remove="${esc(id)}" aria-label="Remove ${esc(source.title)}">×</button></li>`;
  }).join("") : `<li class="players-empty">Empty. Click a site on the map or a recording in the list to seat it.</li>`;

  const issues = composer.problems();
  const key = JSON.stringify(composer.spec());
  const combine = $<HTMLButtonElement>("#combine");
  const take = $<HTMLButtonElement>("#take");
  const ready = !busy && ids.length > 0 && issues.length === 0;
  const fresh = result !== null && key === pieceKey;
  combine.disabled = !ready || fresh;
  combine.textContent = busy ? "Composing…" : result ? "Update piece" : "Compose piece";
  combine.hidden = fresh && !busy;
  combine.classList.toggle("pending", ready && !fresh && result !== null);
  const dockPlay = $<HTMLButtonElement>("#dock-play");
  dockPlay.hidden = !result;
  dockPlay.classList.toggle("primary", fresh);
  dockPlay.classList.toggle("btn", !fresh);
  dockPlay.title = result ? `Play “${pieceTitle(result.title, result.parts.map((p) => p.source))}”` : "";
  take.disabled = !ready || !composer.aceOn;
  $<HTMLButtonElement>("#clear").disabled = busy || ids.length === 0;
  if (busy) return;
  const status = $<HTMLElement>("#status");
  status.classList.toggle("bad", issues.length > 0 && ids.length > 0);
  status.textContent = flash || (ids.length === 0 ? "Seat at least one player."
    : issues.length ? issues[0]!
    : fresh ? `“${pieceTitle(result!.title, result!.parts.map((p) => p.source))}” is ready to play.`
    : result ? `Changed since “${pieceTitle(result.title, result.parts.map((p) => p.source))}”.`
    : `${ids.length} player${ids.length === 1 ? "" : "s"} ready${composer.aceOn ? "; composing takes about a minute" : ""}.`);
}

function renderHallSeats(ids: string[]) {
  const chairs = Math.max(catalog.combination.max_parts, ids.length);
  $("#hall-seats").innerHTML = Array.from({ length: chairs }, (_, i) => {
    const source = sourceById.get(ids[i] ?? "");
    const animal = source ? `<img class="species-icon" src="${esc(fileUrl(`species/${SPECIES_ICON[source.species]}.png`))}" alt="" aria-hidden="true">` : "";
    const chair = `<span class="seat-figure"><svg viewBox="0 0 36 42" aria-hidden="true"><path d="M8 19V7a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v12M6 17v13h24V17M9 30v8M27 30v8"/><rect x="9" y="20" width="18" height="8" rx="2"/></svg>${animal}</span><span class="seat-caption">${i + 1}${source ? ` · ${SEAT_LABEL[source.species]}` : " · Empty"}</span>`;
    return source ? `<li class="occupied" style="--c:${SPECIES_COLOR[source.species]}"><button type="button" data-chair="${esc(source.id)}" aria-label="${isStatic ? "Inspect" : "Remove"} ${esc(source.title)}" title="${esc(capital(source.species))} · ${esc(source.location.label)}">${chair}</button></li>` : `<li class="vacant" aria-label="Seat ${i + 1} available">${chair}</li>`;
  }).join("");
}

$("#hall-seats").addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-chair]");
  const source = button && sourceById.get(button.dataset.chair ?? "");
  if (!button || !source) return;
  if (isStatic) openSite(siteOf.get(source.id)!);
  else composer?.remove(source.id);
});

function say(text: string) {
  flash = text;
  clearTimeout(flashTimer);
  flashTimer = window.setTimeout(() => { flash = ""; renderDock(); }, 3500);
  renderDock();
}

$<HTMLElement>("#players").addEventListener("click", (event) => {
  const id = (event.target as Element).closest<HTMLButtonElement>("[data-remove]")?.dataset.remove;
  if (id) composer?.remove(id);
});
$<HTMLElement>("#players").addEventListener("pointerover", (event) => {
  const id = (event.target as Element).closest<HTMLElement>(".player")?.dataset.id;
  map.highlight(id ? siteOf.get(id)?.key ?? null : null);
});
$<HTMLElement>("#players").addEventListener("pointerleave", () => map.highlight(null));
$<HTMLButtonElement>("#clear").addEventListener("click", () => composer?.clear());
$<HTMLButtonElement>("#combine").addEventListener("click", () => void compose());
$<HTMLButtonElement>("#take").addEventListener("click", () => void compose(true));

/* ---------- compose ---------- */
async function compose(newTake = false) {
  if (busy || !composer || composer.count === 0 || composer.problems().length) return;
  if (newTake) composer.newSeed();
  const spec = composer.spec();
  const key = JSON.stringify(spec);
  if (!newTake && result && key === pieceKey) return;
  const known = newTake ? undefined : rendered.get(key);
  if (known) {
    const manifest = await piece(known).catch(() => null);
    if (manifest) {
      pieceKey = key;
      showResult(manifest, { seat: false, autoplay: true });
      return;
    }
  }
  const log = $<HTMLPreElement>("#log");
  const status = $<HTMLElement>("#status");
  busy = true;
  renderDock();
  status.classList.remove("bad");
  status.textContent = "Starting the engine…";
  log.textContent = "";
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
        if (message.type === "log") {
          log.textContent += message.text + "\n";
          log.scrollTop = log.scrollHeight;
          status.textContent = "Composing your piece… Details in the technical score.";
        }
        if (message.type === "error") throw new Error(message.message);
        if (message.type === "done") {
          pieceKey = key;
          rendered.set(key, message.manifest.id);
          busy = false;
          showResult(message.manifest, { seat: false, autoplay: true });
          void loadSaved();
        }
      }
    }
  } catch (error) {
    busy = false;
    renderDock();
    status.classList.add("bad");
    status.textContent = `Composing failed: ${(error as Error).message}. The engine log has details.`;
    return;
  } finally {
    busy = false;
  }
  renderDock();
}

/* ---------- result and playback ---------- */
function showResult(manifest: Manifest | null, options: { seat: boolean; autoplay?: boolean; scroll?: boolean }) {
  if (!manifest) return;
  stop();
  player.rewind();
  result = manifest;
  if (options.scroll !== false) showView("concert");
  $("#load-error").setAttribute("hidden", "");
  $<HTMLButtonElement>("#hear-piece").disabled = false;
  if (options.seat && composer && !isStatic) {
    composer.load(manifest);
    pieceKey = JSON.stringify(composer.spec());
    rendered.set(pieceKey, manifest.id);
  }
  partOn = manifest.parts.map(() => true);
  stemOn.ace = Boolean(manifest.stems.ace);
  stemOn.response = !manifest.stems.ace;
  if (isStatic || !composer) map.setCombination(resultParts());
  const section = $<HTMLElement>("#result");
  section.hidden = false;
  $<HTMLElement>("#result-eyebrow").textContent = `Now on stage / ${manifest.spec.arrangement === "layer" ? "Together" : "In sequence"} · ${manifest.parts.length} player${manifest.parts.length === 1 ? "" : "s"} · ${manifest.duration_s.toFixed(1)} s`;
  $<HTMLElement>("#result-title").textContent = pieceTitle(manifest.title, manifest.parts.map((p) => p.source));
  const resultNote = document.querySelector<HTMLElement>("#result-note");
  if (resultNote) resultNote.textContent = manifest.interpretation;
  $<HTMLInputElement>("#preset-name").value = manifest.preset ? manifest.title : "";
  $<HTMLElement>("#preset-status").textContent = manifest.preset ? "Saved as a preset." : "";
  const stems = (Object.keys(STEM_LABELS) as StemName[]).filter((key) => manifest.stems[key]);
  $<HTMLElement>("#stems").innerHTML = "<legend>Listen to</legend>" + stems.map((key) =>
    `<button class="toggle" type="button" data-stem="${key}" aria-pressed="${stemOn[key]}">${STEM_LABELS[key]}</button>`).join("");
  $<HTMLElement>("#part-toggles").innerHTML = "<legend>Players</legend>" + manifest.parts.map((p, i) =>
    `<button class="toggle" type="button" data-part="${i}" aria-pressed="true" title="${esc(p.title)} · Mute this player's recording and guide"><i class="swatch" style="--c:${partColor(p)}"></i>${i + 1} ${esc(capital(p.species))}</button>`).join("");
  $<HTMLElement>("#individual-track-count").textContent = `${manifest.parts.length} recordings · shared timeline`;
  setIndividualPlayhead = renderIndividualTracks($<HTMLElement>("#individual-lanes"), manifest, sourceById, (t) => void play(t));
  setPlayhead = renderLanes($<HTMLElement>("#lanes"), manifest, (t) => void play(t), ["guide", manifest.stems.ace ? "ace" : "response"]);
  document.querySelectorAll<HTMLButtonElement>("#saved [data-combo]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.combo === manifest.id)));
  renderScores($<HTMLElement>("#scores"), manifest);
  renderTechnicalOutput(manifest);
  $<HTMLElement>("#clock").textContent = `0.0 / ${manifest.duration_s.toFixed(1)} s`;
  $<HTMLElement>("#technical-clock").textContent = `0.0 / ${manifest.duration_s.toFixed(1)} s`;
  if (location.hash.slice(1) !== manifest.id) history.replaceState(null, "", `#${manifest.id}`);
  if (options.scroll !== false) section.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
  renderDock();
  if (options.autoplay) void play(0);
}

function renderTechnicalOutput(manifest: Manifest) {
  const section = $<HTMLElement>("#technical-result");
  section.hidden = false;
  $<HTMLElement>("#technical-result-title").textContent = pieceTitle(manifest.title, manifest.parts.map((p) => p.source));
  const note = document.querySelector<HTMLElement>("#result-note");
  if (note) note.textContent = `${manifest.interpretation} Coloured ticks reference measured source onsets. Pitch contours appear on the guide; the generated spectrogram shows the model's output.`;
  setTechnicalPlayhead = renderLanes($<HTMLElement>("#technical-lanes"), manifest, (t) => void play(t), ["guide", "response", "ace"]);
}

function resultParts(): MapPart[] {
  return result ? result.parts.map((p) => ({ location: p.location, species: p.species })) : [];
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
    { key: `animal-${i}`, url: fileUrl(p.files.animal), gain: g[`animal-${i}`] ?? 0 },
    { key: `guide-${i}`, url: fileUrl(p.files.guide), gain: g[`guide-${i}`] ?? 0 },
  ]);
  for (const key of ["response", "ace"] as const) {
    const stem = result.stems[key];
    if (stem) out.push({ key, url: fileUrl(stem.audio), gain: g[key] ?? 0 });
  }
  return out;
}

/** The result's Play and the dock's Play always show the same state. */
function playButtons(state: "play" | "pause" | "loading") {
  for (const button of document.querySelectorAll<HTMLButtonElement>("#play, #dock-play, #technical-play")) {
    button.setAttribute("aria-pressed", String(state === "pause"));
    button.textContent = state === "loading" ? "Loading…" : state === "pause" ? "❚❚ Pause" : "▶ Play";
  }
}

async function play(offset?: number) {
  if (!result) return;
  preview.pause();
  resetPreview();
  playButtons("loading");
  try {
    await player.play(tracks(), offset ?? player.time, result.duration_s);
    playButtons("pause");
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(tick);
  } catch (error) {
    playButtons("play");
    playbackError(`Audio could not load: ${(error as Error).message}`);
  }
}

function stop() {
  player.stop();
  cancelAnimationFrame(frame);
  playButtons("play");
  map.clearPlayback();
}

player.onEnded = () => {
  stop();
  setPlayhead(null);
  setIndividualPlayhead(null);
  setTechnicalPlayhead(null);
};

function tick() {
  if (!result || !player.playing) return;
  const t = player.time;
  const onsets = result.parts.map((p) => p.onsets_s);
  const spans = result.parts.map((p) => ({ start_s: p.offset_s, length_s: p.trim_s[1] - p.trim_s[0] }));
  map.setPlayback(reducedMotion() ? [] : activePulses(onsets, t, PULSE_LIFETIME, (i) => partOn[i] ?? false), PULSE_LIFETIME,
    soundingParts(spans, t).filter((i) => partOn[i]), resultParts());
  setPlayhead(t);
  setIndividualPlayhead(t);
  setTechnicalPlayhead(t);
  $<HTMLElement>("#clock").textContent = `${t.toFixed(1)} / ${result.duration_s.toFixed(1)} s`;
  $<HTMLElement>("#technical-clock").textContent = `${t.toFixed(1)} / ${result.duration_s.toFixed(1)} s`;
  frame = requestAnimationFrame(tick);
}

for (const id of ["#play", "#dock-play", "#technical-play"]) $<HTMLButtonElement>(id).addEventListener("click", () => (player.playing ? stop() : void play()));
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
  document.querySelector<HTMLElement>(`[data-track-part="${i}"]`)?.classList.toggle("muted", !partOn[i]);
  for (const [track, gain] of Object.entries(gains())) player.setGain(track, gain);
});

/* ---------- presets ---------- */
// Naming happens only here, after a piece exists, so it never slows down putting an orchestra together.
$<HTMLFormElement>("#preset-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!result || isStatic) return;
  const name = $<HTMLInputElement>("#preset-name").value.trim();
  const status = $<HTMLElement>("#preset-status");
  try {
    await json(`/api/combos/${result.id}/preset`, { method: "POST", body: JSON.stringify({ name }) });
    result = { ...result, title: name || result.title, preset: Boolean(name) };
    if (name) $<HTMLElement>("#result-title").textContent = name;
    $<HTMLElement>("#technical-result-title").textContent = result.title;
    renderDock();
    status.textContent = name ? "Saved as a preset." : "Removed from presets.";
    void loadSaved();
  } catch (error) {
    status.textContent = `Could not save: ${(error as Error).message}`;
  }
});

/* ---------- presets and recent pieces ---------- */
function savedItem(c: ComboSummary): string {
  const species = [...new Set(c.sources.map((id) => sourceById.get(id)?.species ?? id))].map(capital);
  return `<li><button type="button" data-combo="${c.id}" aria-pressed="${c.id === result?.id}" class="${c.preset ? "is-preset" : ""}" title="Fill the orchestra with this piece's players"><b><span class="go" aria-hidden="true">+</span>${c.preset ? "★ " : ""}${esc(pieceTitle(c.title, c.sources))}</b>
    <span>${species.map(esc).join(" + ")}</span>
    <span class="piece-meta">${c.sources.length} voices · ${c.duration_s.toFixed(0)} seconds · ${c.ace ? "Generated composition" : "Constructed response"}</span></button></li>`;
}

let summaries = new Map<string, ComboSummary>();

/** A saved piece. The server already applies preset names; the published copy applies them from combos.json. */
async function piece(id: string): Promise<Manifest> {
  const manifest = await json<Manifest>(comboUrl(id));
  const summary = summaries.get(id);
  return isStatic && summary?.preset ? { ...manifest, title: summary.title, preset: true } : manifest;
}

async function loadSaved() {
  const saved = await json<ComboSummary[]>(combosUrl()).catch(() => [] as ComboSummary[]);
  summaries = new Map(saved.map((c) => [c.id, c]));
  $<HTMLButtonElement>("#hear-piece").disabled = saved.length === 0 && !result;
  const presets = saved.filter((c) => c.preset).sort((a, b) => b.created_at_utc.localeCompare(a.created_at_utc));
  const recent = saved.filter((c) => !c.preset);
  const group = (title: string, items: ComboSummary[]) => items.length ? `<li class="group-title">${title}</li>${items.map(savedItem).join("")}` : "";
  $<HTMLElement>("#saved").innerHTML = saved.length
    ? (presets.length ? group("Presets", presets) + group("Recent pieces", recent) : recent.map(savedItem).join(""))
    : `<li class="small">None yet. Seat some players and compose; each piece appears here.</li>`;
}
async function openPiece(id: string, options: { autoplay?: boolean; scroll?: boolean } = {}) {
  if (busy) { say("Wait for the current composition to finish before loading another ensemble."); return false; }
  try { showResult(await piece(id), { seat: true, autoplay: options.autoplay ?? true, scroll: options.scroll }); return true; }
  catch (error) { playbackError(`This piece could not open: ${(error as Error).message}`); return false; }
}
$<HTMLElement>("#saved").addEventListener("click", async (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-combo]");
  if (button && await openPiece(button.dataset.combo!, { autoplay: false, scroll: false })) {
    $<HTMLButtonElement>('#zooms [data-zoom="0"]').click();
    $("#programme-status").textContent = `${result!.parts.length} players seated. Play below, or change the ensemble.`;
    if (matchMedia("(max-width: 850px)").matches) { setProgrammeOpen(false); programmeToggle.focus(); }
  }
});

// The published copy uses the same programme drawer; composition controls stay hidden.
if (isStatic) {
  document.body.classList.add("static");
  $<HTMLElement>("#map-hint").textContent = "Scroll or pinch to zoom. Select a site to hear its recordings.";
}
orchestraChanged();
await loadSaved();
if (isStatic && !location.hash) {
  const first = document.querySelector<HTMLButtonElement>("#saved [data-combo]");
  if (first) showResult(await piece(first.dataset.combo!), { seat: false, scroll: false }); // land at the top of the page
}

// A bare #<piece id> opens that piece and seats its players, so pieces can be linked.
async function openFromHash(scroll = true) {
  const id = location.hash.slice(1);
  if (/^[0-9a-f]{12}$/.test(id) && id !== result?.id) showResult(await piece(id).catch(() => null), { seat: true, scroll });
}
window.addEventListener("hashchange", () => void openFromHash());
await openFromHash(false);
