// The combination being composed: parts, their trims, offsets, gains and registers, a timeline
// preview that mirrors Python's placement, and the ACE-Step request.

import { buildSpec, clamp, draftFor, place, problems, totalDuration, type PlacedPart } from "./lib/arrange.ts";
import type { AceRequest, Arrangement, Catalog, PartDraft, Source, Spec } from "./lib/types.ts";
import { SPECIES_COLOR, type MapPart } from "./map.ts";

const $ = <T extends Element>(selector: string) => document.querySelector(selector) as T;
const esc = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
const fmt = (value: number) => (Math.round(value * 10) / 10).toString();

export class Composer {
  private parts: PartDraft[] = [];
  private arrangement: Arrangement = "layer";
  private gap_s = 1;
  private captionEdited = false;
  private readonly sources: Map<string, Source>;

  constructor(private readonly catalog: Catalog, private readonly onChange: (parts: MapPart[]) => void) {
    this.sources = new Map(catalog.sources.map((s) => [s.id, s]));
    $<HTMLFieldSetElement>("#arrangement").addEventListener("change", (event) => {
      this.arrangement = (event.target as HTMLInputElement).value as Arrangement;
      $<HTMLElement>("#gap-field").hidden = this.arrangement !== "sequence";
      this.render();
    });
    $<HTMLInputElement>("#gap").addEventListener("input", (event) => {
      this.gap_s = clamp(Number((event.target as HTMLInputElement).value) || 0, 0, 30);
      this.refresh();
    });
    $<HTMLInputElement>("#strength").addEventListener("input", (event) => {
      $<HTMLOutputElement>("#strength-out").value = (event.target as HTMLInputElement).value;
    });
    $<HTMLTextAreaElement>("#caption").addEventListener("input", () => { this.captionEdited = true; });
    $<HTMLInputElement>("#ace-on").addEventListener("change", () => this.syncModel());
    const list = $<HTMLOListElement>("#parts");
    list.addEventListener("input", (event) => this.edit(event.target as HTMLInputElement | HTMLSelectElement));
    list.addEventListener("click", (event) => {
      const button = (event.target as Element).closest<HTMLButtonElement>("button[data-action]");
      if (!button) return;
      const i = Number(button.dataset.index);
      if (button.dataset.action === "remove") this.parts.splice(i, 1);
      if (button.dataset.action === "up" && i > 0) this.parts.splice(i - 1, 0, ...this.parts.splice(i, 1));
      if (button.dataset.action === "down" && i < this.parts.length - 1) this.parts.splice(i + 1, 0, ...this.parts.splice(i, 1));
      this.render();
    });
    this.render();
  }

  add(source: Source) {
    // A new layered part enters a few seconds after the previous one, so layers do not all start together.
    const offset = this.arrangement === "layer" && this.parts.length ? Math.min(30, this.parts.length * 4) : 0;
    this.parts.push(draftFor(source, offset));
    this.render();
  }

  get count(): number {
    return this.parts.length;
  }

  placed(): PlacedPart[] {
    return place(this.parts, this.arrangement, this.gap_s, this.sources);
  }

  mapParts(): MapPart[] {
    return this.parts.flatMap((p) => {
      const source = this.sources.get(p.source);
      return source ? [{ location: source.location, species: source.species }] : [];
    });
  }

  spec(): Spec {
    const on = $<HTMLInputElement>("#ace-on").checked;
    const ace: AceRequest | null = on ? {
      task: (document.querySelector<HTMLInputElement>('input[name="ace-task"]:checked')?.value ?? "cover") as AceRequest["task"],
      caption: $<HTMLTextAreaElement>("#caption").value.trim() || undefined,
      audio_cover_strength: Number($<HTMLInputElement>("#strength").value),
    } : null;
    return buildSpec($<HTMLInputElement>("#title").value, this.arrangement, this.gap_s, this.parts, ace);
  }

  problems(): string[] {
    return problems(this.placed(), this.catalog.combination);
  }

  private edit(target: HTMLInputElement | HTMLSelectElement) {
    const i = Number(target.dataset.index);
    const part = this.parts[i];
    if (!part) return;
    const source = this.sources.get(part.source);
    const value = Number(target.value);
    if (target.value === "" && target.dataset.field !== "shift") return;
    switch (target.dataset.field) {
      case "offset": part.offset_s = Math.max(0, value || 0); break;
      case "trim0": part.trim_s = [clamp(value || 0, 0, source?.duration_s ?? 0), part.trim_s[1]]; break;
      case "trim1": part.trim_s = [part.trim_s[0], clamp(value || 0, 0, source?.duration_s ?? 0)]; break;
      case "gain": part.gain_db = value || 0; break;
      case "shift": part.shift_octaves = target.value === "auto" ? null : value; break;
    }
    this.refresh();
  }

  /** Full re-render: used when parts are added, removed, reordered or the arrangement changes. */
  render() {
    const placed = this.placed();
    $<HTMLOListElement>("#parts").innerHTML = placed.map((p) => this.card(p)).join("");
    $<HTMLElement>("#parts-empty").hidden = this.parts.length > 0;
    this.refresh();
  }

  /** Light update that keeps input focus: timeline, start labels, problems, caption and the map. */
  private refresh() {
    const placed = this.placed();
    placed.forEach((p) => {
      const label = document.querySelector<HTMLElement>(`[data-start="${p.index}"]`);
      if (label) label.textContent = `starts at ${fmt(p.start_s)} s`;
    });
    $<HTMLElement>("#timeline").innerHTML = this.timeline(placed);
    const issues = this.problems();
    $<HTMLElement>("#problems").textContent = issues.join(" ");
    $<HTMLButtonElement>("#combine").disabled = issues.length > 0;
    this.syncModel();
    this.onChange(this.mapParts());
  }

  private syncModel() {
    const caption = $<HTMLTextAreaElement>("#caption");
    const species = new Set(this.parts.map((p) => this.sources.get(p.source)?.species));
    const only = species.size === 1 ? [...species][0] : undefined;
    const fallback = only ? this.catalog.species[only].caption : this.catalog.combination.caption;
    if (!this.captionEdited) caption.value = fallback;
    const on = $<HTMLInputElement>("#ace-on").checked;
    for (const id of ["#ace-task", "#strength", "#caption"]) $<HTMLInputElement>(id).disabled = !on;
  }

  private card(p: PlacedPart): string {
    const source = this.sources.get(p.source);
    if (!source) return "";
    const last = this.parts.length - 1;
    const auto = `auto (${source.register_shift_octaves > 0 ? "+" : ""}${source.register_shift_octaves} oct)`;
    const shifts = [-5, -4, -3, -2, -1, 0, 1, 2].map((v) => `<option value="${v}" ${p.shift_octaves === v ? "selected" : ""}>${v > 0 ? "+" : ""}${v} oct</option>`).join("");
    const tonal = source.material === "tonal";
    return `<li class="part" style="--c:${SPECIES_COLOR[source.species]}">
      <div class="part-head"><div><b>${p.index + 1} · ${esc(source.id)}</b>
        <div class="small">${esc(source.location.label)} · ${fmt(source.duration_s)} s · ${source.onsets_s.length} events</div></div>
        <div class="tools">
          <button class="btn" type="button" data-action="up" data-index="${p.index}" aria-label="Move part ${p.index + 1} earlier" ${p.index === 0 ? "disabled" : ""}>↑</button>
          <button class="btn" type="button" data-action="down" data-index="${p.index}" aria-label="Move part ${p.index + 1} later" ${p.index === last ? "disabled" : ""}>↓</button>
          <button class="btn" type="button" data-action="remove" data-index="${p.index}" aria-label="Remove part ${p.index + 1}">Remove</button>
        </div></div>
      <div class="part-grid">
        ${this.arrangement === "layer"
          ? `<label>Offset (s)<input id="offset-${p.index}" type="number" min="0" step="0.5" value="${p.offset_s}" data-field="offset" data-index="${p.index}"></label>`
          : `<label>Position<span class="mono" data-start="${p.index}">starts at ${fmt(p.start_s)} s</span></label>`}
        <label>Trim from (s)<input id="trim0-${p.index}" type="number" min="0" max="${source.duration_s}" step="0.5" value="${p.trim_s[0]}" data-field="trim0" data-index="${p.index}"></label>
        <label>Trim to (s)<input id="trim1-${p.index}" type="number" min="0" max="${source.duration_s}" step="0.5" value="${fmt(p.trim_s[1])}" data-field="trim1" data-index="${p.index}"></label>
        <label>Gain (dB)<input id="gain-${p.index}" type="number" min="${this.catalog.combination.gain_db[0]}" max="${this.catalog.combination.gain_db[1]}" step="1" value="${p.gain_db}" data-field="gain" data-index="${p.index}"></label>
        <label>Guide register<select id="shift-${p.index}" data-field="shift" data-index="${p.index}" ${tonal ? "" : "disabled"}>
          <option value="auto" ${p.shift_octaves === null ? "selected" : ""}>${tonal ? auto : "clicks: fixed"}</option>${tonal ? shifts : ""}</select></label>
      </div></li>`;
  }

  private timeline(placed: PlacedPart[]): string {
    if (!placed.length) return "";
    const duration = Math.max(1, totalDuration(placed));
    const width = 600;
    const left = 22;
    const row = 22;
    const x = (t: number) => left + (t / duration) * (width - left - 8);
    const step = [5, 10, 15, 30, 60].find((s) => duration / s <= 8) ?? 60;
    const height = placed.length * row + 22;
    let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Timeline: ${placed.length} parts over ${fmt(duration)} seconds">`;
    for (let t = 0; t <= duration; t += step) {
      svg += `<line class="axis" x1="${x(t)}" x2="${x(t)}" y1="0" y2="${height - 14}"/><text x="${x(t)}" y="${height - 2}" text-anchor="middle">${t}s</text>`;
    }
    placed.forEach((p, i) => {
      const source = this.sources.get(p.source);
      if (!source) return;
      const y = i * row + 3;
      const style = `--c:${SPECIES_COLOR[source.species]}`;
      svg += `<text x="2" y="${y + 13}">${i + 1}</text><rect class="bar" style="${style}" x="${x(p.start_s)}" y="${y}" width="${Math.max(1, x(p.start_s + p.length_s) - x(p.start_s))}" height="${row - 6}" rx="2"/>`;
      for (const onset of source.onsets_s) {
        if (onset < p.trim_s[0] || onset >= p.trim_s[1]) continue;
        const at = x(p.start_s + onset - p.trim_s[0]);
        svg += `<line class="tick" style="${style}" x1="${at}" x2="${at}" y1="${y + 3}" y2="${y + row - 9}"/>`;
      }
    });
    return svg + "</svg>";
  }
}
