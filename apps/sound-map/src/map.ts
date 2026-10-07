// The atlas: Equal Earth world from local GeoJSON, catalogue dataset dots, playable recording sites,
// great-circle arcs between the parts of a combination, and pulse rings on each part's onsets.

import { geoEqualEarth, geoGraticule10, geoPath, type GeoProjection } from "d3-geo";
import { select } from "d3-selection";
import { zoom, zoomIdentity, type D3ZoomEvent, type ZoomBehavior } from "d3-zoom";
import type { Pulse } from "./lib/pulses.ts";
import type { DatasetPoint, Location, Source, Species } from "./lib/types.ts";

const NS = "http://www.w3.org/2000/svg";
const W = 960;
const H = 500;

export const SPECIES_COLOR: Record<Species, string> = {
  humpback: "var(--humpback)",
  dolphin: "var(--dolphin)",
  "sperm whale": "var(--sperm)",
  "killer whale": "var(--orca)",
};

export interface Site {
  key: string;
  location: Location;
  species: Species; // the first species recorded here; `others` lists the rest
  others: Species[];
  sources: Source[];
}

export interface MapPart {
  location: Location;
  species: Species;
}

export type Countries = { type: "FeatureCollection"; features: { type: "Feature"; geometry: object; properties: Record<string, unknown> }[] };

export function sitesOf(sources: Source[]): Site[] {
  const sites = new Map<string, Site>();
  for (const source of sources) {
    const key = source.location.label;
    const site = sites.get(key) ?? { key, location: source.location, species: source.species, others: [], sources: [] };
    site.sources.push(source);
    if (source.species !== site.species && !site.others.includes(source.species)) site.others.push(source.species);
    sites.set(key, site);
  }
  return [...sites.values()];
}

function el<K extends keyof SVGElementTagNameMap>(name: K, attrs: Record<string, string | number> = {}, parent?: Element): SVGElementTagNameMap[K] {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  parent?.appendChild(node);
  return node;
}

export class AtlasMap {
  private width = W;
  private readonly projection: GeoProjection;
  private readonly viewport: SVGRectElement;
  private readonly geography: { node: SVGPathElement; shape: object }[] = [];
  private readonly world: SVGGElement;
  private readonly datasets: SVGGElement;
  private readonly arcs: SVGGElement;
  private readonly pulses: SVGGElement;
  private readonly pins: SVGGElement;
  private readonly siteLayer: SVGGElement;
  private readonly behaviour: ZoomBehavior<SVGSVGElement, unknown>;
  private k = 1;
  private panX = 0;
  private parts: MapPart[] = [];
  private framedSites: Site[] | null = null;

  constructor(
    private readonly svg: SVGSVGElement,
    countries: Countries,
    points: DatasetPoint[],
    private readonly sites: Site[],
    private readonly onSite: (site: Site) => void,
  ) {
    const box = svg.getBoundingClientRect();
    this.width = box.height ? H * box.width / box.height : W;
    svg.setAttribute("viewBox", `0 0 ${this.width} ${H}`);
    // Clip only at the rectangular viewport. Hall scenery belongs behind the map,
    // so decorative seating cannot hide sites when the geography is zoomed or panned.
    const defs = el("defs", {}, svg);
    const clip = el("clipPath", { id: "map-viewport-clip" }, defs);
    this.viewport = el("rect", { x: 0, y: 0, width: this.width, height: H }, clip);
    this.projection = geoEqualEarth().fitExtent([[25, 32], [this.width - 25, H - 32]], { type: "Sphere" });
    const path = geoPath(this.projection);
    const mapStage = el("g", { "clip-path": "url(#map-viewport-clip)" }, svg);
    this.world = el("g", {}, mapStage);
    const sphere = { type: "Sphere" } as const;
    const graticule = geoGraticule10();
    this.geography.push({ node: el("path", { class: "sphere", d: path(sphere) ?? "" }, this.world), shape: sphere });
    this.geography.push({ node: el("path", { class: "graticule", d: path(graticule) ?? "" }, this.world), shape: graticule });
    const land = el("g", {}, this.world);
    for (const feature of countries.features) {
      this.geography.push({ node: el("path", { class: "land", d: path(feature as never) ?? "" }, land), shape: feature });
    }
    this.datasets = el("g", {}, this.world);
    for (const point of points) {
      const xy = this.projection([point.lon, point.lat]);
      if (!xy) continue;
      const dot = el("circle", { class: `dataset ${point.kind}`, cx: xy[0], cy: xy[1], r: 2.2, "data-lon": point.lon, "data-lat": point.lat }, this.datasets);
      el("title", {}, dot).textContent = `${point.label} · ${point.dataset}`;
    }
    this.arcs = el("g", {}, this.world);
    this.pulses = el("g", {}, this.world);
    this.siteLayer = el("g", {}, this.world);
    this.pins = el("g", {}, this.world);
    this.drawSites();
    this.behaviour = zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 64])
      .translateExtent([[0, 0], [this.width, H]])
      .on("zoom", (event: D3ZoomEvent<SVGSVGElement, unknown>) => {
        this.world.setAttribute("transform", event.transform.toString());
        this.k = event.transform.k;
        this.panX = event.transform.x;
        this.rescale();
      });
    select(svg).call(this.behaviour);
    new ResizeObserver(() => { this.resize(); this.rescale(); }).observe(svg);
  }

  /** Match the available width at the chosen height without stretching the geography. */
  private resize() {
    const box = this.svg.getBoundingClientRect();
    if (!box.width || !box.height) return;
    const width = H * box.width / box.height;
    if (Math.abs(width - this.width) < 1) return;
    this.width = width;
    this.svg.setAttribute("viewBox", `0 0 ${width} ${H}`);
    this.viewport.setAttribute("width", String(width));
    this.projection.fitExtent([[25, 32], [width - 25, H - 32]], { type: "Sphere" });
    const path = geoPath(this.projection);
    for (const { node, shape } of this.geography) node.setAttribute("d", path(shape as never) ?? "");
    this.datasets.querySelectorAll<SVGCircleElement>("circle").forEach((dot) => {
      const xy = this.projection([Number(dot.dataset.lon), Number(dot.dataset.lat)]);
      if (xy) { dot.setAttribute("cx", String(xy[0])); dot.setAttribute("cy", String(xy[1])); }
    });
    this.siteLayer.querySelectorAll<SVGGElement>(".site").forEach((group, i) => {
      const [x, y] = this.xy(this.sites[i]!.location);
      group.dataset.x = String(x);
      group.dataset.y = String(y);
    });
    this.setCombination(this.parts);
    this.pulses.replaceChildren();
    this.behaviour.translateExtent([[0, 0], [width, H]]);
    this.fit(this.framedSites);
  }

  /** Frame a set of sites (null: the whole world). Zoom stays within the behaviour's limits. */
  fit(subset: Site[] | null) {
    this.framedSites = subset;
    let transform = zoomIdentity;
    if (subset?.length) {
      const points = subset.map((site) => this.xy(site.location));
      const xs = points.map((p) => p[0]);
      const ys = points.map((p) => p[1]);
      const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      // Labels sit to the right of their marks, so the right margin is wider.
      const [left, right, pad] = [75, 115, 65];
      const k = Math.max(1, Math.min(64, (this.width - left - right) / Math.max(x1 - x0, 1), (H - 2 * pad) / Math.max(y1 - y0, 1)));
      const cx = left + (this.width - left - right) / 2;
      transform = zoomIdentity.translate(cx - (k * (x0 + x1)) / 2, H / 2 - (k * (y0 + y1)) / 2).scale(k);
    }
    select(this.svg).call(this.behaviour.transform, transform);
  }

  /** Sites with at least one recording in the orchestra get a halo. */
  setSeated(keys: Set<string>) {
    this.siteLayer.querySelectorAll<SVGGElement>(".site").forEach((node) => {
      const seated = keys.has(node.dataset.key ?? "");
      node.classList.toggle("seated", seated);
      node.setAttribute("aria-pressed", String(seated));
    });
  }

  /** Mirror a hover in the recordings list. */
  highlight(key: string | null) {
    this.siteLayer.querySelectorAll<SVGGElement>(".site").forEach((node) => node.classList.toggle("hover", node.dataset.key === key));
  }

  private xy(location: Location): [number, number] {
    return this.projection([location.lon, location.lat]) ?? [0, 0];
  }

  private drawSites() {
    for (const site of this.sites) {
      const [x, y] = this.xy(site.location);
      const group = el("g", {
        class: `site ${site.location.precision}`, "data-key": site.key, tabindex: 0, role: "button", "aria-pressed": "false",
        "aria-label": `${site.location.label}: ${site.sources.length} recording${site.sources.length === 1 ? "" : "s"}`,
        style: `--c:${SPECIES_COLOR[site.species]}`, "data-x": x, "data-y": y,
      }, this.siteLayer);
      el("title", {}, group).textContent = `${site.location.label} · ${site.sources.length} recording${site.sources.length === 1 ? "" : "s"}`;
      el("circle", { class: "hit", r: 18 }, group);
      el("circle", { class: "halo", r: 15 }, group);
      // A second species recorded at the same site shows as an outer ring in its colour.
      site.others.slice(0, 1).forEach((other) => el("circle", { class: "ring", r: 11.5, style: `--c:${SPECIES_COLOR[other]}` }, group));
      const mark = site.location.precision === "published"
        ? el("circle", { class: "mark", r: 8 }, group)
        : el("rect", { class: "mark", x: -7, y: -7, width: 14, height: 14, transform: "rotate(45)" }, group);
      mark.setAttribute("data-shape", site.location.precision);
      el("text", { class: "badge", y: 0.5 }, group).textContent = String(site.sources.length);
      el("text", { class: "site-label", x: 13, y: 4 }, group).textContent = site.location.label;
      const open = () => this.onSite(site);
      group.addEventListener("click", (event) => { event.stopPropagation(); open(); });
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); }
      });
    }
    this.rescale();
  }

  /** Keep marks, labels and rings the same on-screen size at every zoom level. */
  private rescale() {
    const k = this.displayZoom();
    this.datasets.querySelectorAll("circle").forEach((dot) => dot.setAttribute("r", String(2.2 / k)));
    const groups = [...this.siteLayer.querySelectorAll<SVGGElement>(".site")];
    const at = groups.map((g) => [Number(g.dataset.x), Number(g.dataset.y)] as const);
    groups.forEach((group, i) => {
      group.setAttribute("transform", `translate(${group.dataset.x},${group.dataset.y}) scale(${1 / k})`);
      // Show a label only when no other site sits within 70 screen units; zooming in reveals the rest.
      const [x, y] = at[i]!;
      const crowded = at.some(([ox, oy], j) => j !== i && Math.hypot(ox - x, oy - y) * k < 70);
      const label = group.querySelector<SVGTextElement>(".site-label");
      if (label) {
        const nearRight = x * this.k + this.panX > this.width * .68;
        label.setAttribute("x", nearRight ? "-13" : "13");
        label.setAttribute("text-anchor", nearRight ? "end" : "start");
        label.setAttribute("visibility", crowded ? "hidden" : "visible");
      }
    });
    this.drawPins();
  }

  /** Match SVG viewBox scaling as well as zoom, so mobile pins remain readable and tappable. */
  private displayZoom(): number {
    const box = this.svg.getBoundingClientRect();
    return this.k * (Math.min(box.width / this.width, box.height / H) || 1);
  }

  /** Where a site sits inside the map box, in CSS pixels, for anchoring the popover. */
  anchor(site: Site): { x: number; y: number } {
    const node = this.siteLayer.querySelector<SVGGElement>(`[data-key="${CSS.escape(site.key)}"]`);
    const box = this.svg.getBoundingClientRect();
    const rect = node?.getBoundingClientRect();
    return rect ? { x: rect.left + rect.width / 2 - box.left, y: rect.top + rect.height / 2 - box.top } : { x: box.width / 2, y: box.height / 2 };
  }

  markOpen(site: Site | null) {
    this.siteLayer.querySelectorAll(".site").forEach((node) => node.classList.toggle("open", node.getAttribute("data-key") === site?.key));
  }

  /** Arcs connect consecutive parts at different places; numbered pins show the order. */
  setCombination(parts: MapPart[]) {
    this.parts = parts;
    this.arcs.replaceChildren();
    const path = geoPath(this.projection);
    parts.forEach((part, i) => {
      const next = parts[i + 1];
      if (!next || next.location.label === part.location.label) return;
      el("path", {
        class: "arc", "data-from": i, "data-to": i + 1,
        d: path({ type: "LineString", coordinates: [[part.location.lon, part.location.lat], [next.location.lon, next.location.lat]] }) ?? "",
      }, this.arcs);
    });
    this.drawPins();
  }

  /** Seat numbers beside each site, joined when several players sit at one place ("2·4·5"). */
  private drawPins() {
    this.pins.replaceChildren();
    const seats = new Map<string, { location: Location; numbers: number[] }>();
    this.parts.forEach((part, i) => {
      const entry = seats.get(part.location.label) ?? { location: part.location, numbers: [] };
      entry.numbers.push(i + 1);
      seats.set(part.location.label, entry);
    });
    for (const { location, numbers } of seats.values()) {
      const [x, y] = this.xy(location);
      const k = this.displayZoom();
      el("text", { class: "part-pin", x: x - 15 / k, y: y - 13 / k, "font-size": 11 / k, "stroke-width": 3 / k, "text-anchor": "end" }, this.pins)
        .textContent = numbers.join("·");
    }
  }

  /** One ring per fresh onset; sounding parts light the arcs that touch them. */
  setPlayback(pulses: Pulse[], lifetime: number, sounding: number[], parts: MapPart[] = this.parts) {
    this.pulses.replaceChildren();
    for (const pulse of pulses) {
      const part = parts[pulse.part];
      if (!part) continue;
      const [x, y] = this.xy(part.location);
      const u = pulse.age_s / lifetime;
      el("circle", {
        class: "pulse", cx: x, cy: y, r: (9 + 30 * u) / this.displayZoom(),
        style: `--c:${SPECIES_COLOR[part.species]};stroke-opacity:${(1 - u).toFixed(3)};stroke-width:${2.2 - 1.4 * u}`,
      }, this.pulses);
    }
    this.arcs.querySelectorAll<SVGPathElement>(".arc").forEach((arc) => {
      const from = Number(arc.dataset.from);
      const to = Number(arc.dataset.to);
      arc.classList.toggle("active", sounding.includes(from) || sounding.includes(to));
    });
  }

  clearPlayback() {
    this.setPlayback([], 1, []);
  }
}
