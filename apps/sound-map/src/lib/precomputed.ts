import { buildSpec } from "./arrange.ts";
import type { Catalog, PrecomputedIndex, Spec } from "./types.ts";

/** Same defaults as the Python plan: automatic registers and the catalogue seed are resolved. */
export function specKey(spec: Spec, catalog: Catalog): string {
  const sources = new Map(catalog.sources.map((s) => [s.id, s]));
  const species = new Set(spec.parts.map((p) => sources.get(p.source)?.species));
  const only = species.size === 1 ? [...species][0] : undefined;
  const caption = only ? catalog.species[only].caption : catalog.combination.caption;
  const parts = spec.parts.map((p) => ({ ...p, shift_octaves: p.shift_octaves ?? sources.get(p.source)?.register_shift_octaves ?? null }));
  const ace = spec.ace ? {
    task: spec.ace.task,
    caption: spec.ace.caption || caption,
    audio_cover_strength: spec.ace.audio_cover_strength ?? catalog.combination.audio_cover_strength,
    seed: spec.ace.seed ?? catalog.seed,
  } : null;
  return JSON.stringify(buildSpec("", spec.arrangement, spec.gap_s, parts, ace));
}

export function precomputedPieces(index: PrecomputedIndex | null, catalog: Catalog): Map<string, string> {
  if (!index || index.config_sha256 !== catalog.config_sha256 || index.render_version !== catalog.render_version) return new Map();
  return new Map(index.pieces.map((p) => [specKey(p.spec, catalog), p.id]));
}
