import { describe, expect, test } from "bun:test";
import { buildSpec, draftFor } from "../src/lib/arrange.ts";
import { precomputedPieces, specKey } from "../src/lib/precomputed.ts";
import type { Catalog, PrecomputedIndex } from "../src/lib/types.ts";

const catalog: Catalog = { ...await Bun.file(new URL("../demo/follow/catalog.json", import.meta.url)).json(), config_sha256: "test", render_version: 4 };
const [a, b] = catalog.sources;
const request = buildSpec("", "layer", 1, [draftFor(a!), draftFor(b!)], { task: "cover", audio_cover_strength: 0.6 });
const resolved = buildSpec("", "layer", 1, request.parts.map((p) => ({
  ...p, shift_octaves: catalog.sources.find((s) => s.id === p.source)!.register_shift_octaves,
})), { task: "cover", audio_cover_strength: 0.6, seed: catalog.seed, caption: catalog.species[a!.species].caption });
const index: PrecomputedIndex = { config_sha256: "test", render_version: 4, pieces: [{ id: "123456abcdef", spec: resolved }] };

describe("precomputed playback lookup", () => {
  test("every bundled duo matches the default composer request", async () => {
    const actualCatalog = await Bun.file(new URL("../demo/follow/catalog.json", import.meta.url)).json() as Catalog;
    const bundled = await Bun.file(new URL("../demo/follow/duos.json", import.meta.url)).json() as PrecomputedIndex;
    const pieces = precomputedPieces(bundled, actualCatalog);
    const sources = new Map(actualCatalog.sources.map((s) => [s.id, s]));
    expect(pieces.size).toBe(actualCatalog.sources.length * (actualCatalog.sources.length - 1) / 2);
    for (const piece of bundled.pieces) {
      const parts = piece.spec.parts.map((p) => draftFor(sources.get(p.source)!));
      const defaults = buildSpec("", "layer", 1, parts, { task: "cover", audio_cover_strength: actualCatalog.combination.audio_cover_strength });
      expect(pieces.get(specKey(defaults, actualCatalog))).toBe(piece.id);
      expect(pieces.get(specKey({ ...defaults, parts: [...defaults.parts].reverse() }, actualCatalog))).toBe(piece.id);
    }
  });

  test("default requests find the saved pair in either click order", () => {
    const pieces = precomputedPieces(index, catalog);
    expect(pieces.get(specKey(request, catalog))).toBe("123456abcdef");
    expect(pieces.get(specKey({ ...request, parts: [...request.parts].reverse() }, catalog))).toBe("123456abcdef");
    expect(specKey({ ...request, title: "My renamed preset" }, catalog)).toBe(specKey(request, catalog));
  });

  test("custom timing, balance, registers, captions and takes request their own renders", () => {
    const pieces = precomputedPieces(index, catalog);
    for (const change of [{ offset_s: 4 }, { gain_db: -3 }, { shift_octaves: a!.register_shift_octaves + 1 }, { trim_s: [0, 10] as [number, number] }]) {
      expect(pieces.has(specKey({ ...request, parts: [{ ...request.parts[0]!, ...change }, request.parts[1]!] }, catalog))).toBe(false);
    }
    expect(pieces.has(specKey({ ...request, ace: { ...request.ace!, seed: 7 } }, catalog))).toBe(false);
    expect(pieces.has(specKey({ ...request, ace: { ...request.ace!, caption: "A different composition" } }, catalog))).toBe(false);
    expect(pieces.has(specKey({ ...request, ace: null }, catalog))).toBe(false);
    expect(pieces.has(specKey({ ...request, arrangement: "sequence" }, catalog))).toBe(false);
  });

  test("changed configuration or renderer does not reuse stale bundled pieces", () => {
    expect(precomputedPieces({ ...index, config_sha256: "old" }, catalog).size).toBe(0);
    expect(precomputedPieces({ ...index, render_version: 3 }, catalog).size).toBe(0);
    expect(precomputedPieces(null, catalog).size).toBe(0);
  });
});
