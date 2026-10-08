import { describe, expect, test } from "bun:test";
import { buildSpec, draftFor, place, problems, totalDuration } from "../src/lib/arrange.ts";
import { contentType, readableLog, safeJoin } from "../src/lib/paths.ts";
import { activePulses, soundingParts, upperBound } from "../src/lib/pulses.ts";
import type { CombinationLimits, Source } from "../src/lib/types.ts";

const limits: CombinationLimits = {
  interpretation: "", max_parts: 3, max_duration_s: 60, min_part_s: 1, gain_db: [-24, 6], caption: "", audio_cover_strength: 0.6,
};

function source(id: string, duration_s: number): Source {
  return {
    id, species: "humpback", title: id, note: "", duration_s, material: "tonal", instrument: "bowed tone", register_shift_octaves: 0,
    location: { label: "Orcasound Lab", lon: -123.16, lat: 48.52, precision: "published" },
    events: [], onsets_s: [1, 2, 3], files: { animal: { audio: "", image: "", band: [60, 4000] }, guide: { audio: "", image: "", band: [40, 4000] } },
  };
}

const sources = new Map([["a", source("a", 30)], ["b", source("b", 20)]]);

describe("arrangement mirrors the Python plan", () => {
  test("sequence places parts one after another with the gap", () => {
    const parts = [draftFor(sources.get("a")!), { ...draftFor(sources.get("b")!), trim_s: [5, 15] as [number, number] }];
    const placed = place(parts, "sequence", 2, sources);
    expect(placed.map((p) => p.start_s)).toEqual([0, 32]);
    expect(placed[1]!.length_s).toBe(10);
    expect(totalDuration(placed)).toBe(42.5);
  });

  test("layer keeps offsets and clamps trims to the recording", () => {
    const parts = [draftFor(sources.get("a")!), { ...draftFor(sources.get("b")!, 4), trim_s: [-3, 99] as [number, number] }];
    const placed = place(parts, "layer", 1, sources);
    expect(placed.map((p) => p.start_s)).toEqual([0, 4]);
    expect(placed[1]!.trim_s).toEqual([0, 20]);
    expect(totalDuration(placed)).toBe(30.5);
  });

  test("default layers start together and share a spec in either selection order", () => {
    const parts = [draftFor(sources.get("b")!), draftFor(sources.get("a")!)];
    expect(place(parts, "layer", 1, sources).map((p) => p.start_s)).toEqual([0, 0]);
    expect(buildSpec("", "layer", 1, parts, null)).toEqual(buildSpec("", "layer", 1, [...parts].reverse(), null));
    expect(parts.map((p) => p.source)).toEqual(["b", "a"]); // the visible chairs keep their order
  });

  test("layer normalization keeps each player's custom settings, including repeated sources", () => {
    const parts = [
      { ...draftFor(sources.get("b")!, 7), gain_db: -3, shift_octaves: -1 },
      draftFor(sources.get("a")!),
      { ...draftFor(sources.get("b")!, 2), trim_s: [3, 15] as [number, number] },
    ];
    const spec = buildSpec("", "layer", 1, parts, null);
    expect(spec).toEqual(buildSpec("", "layer", 1, [...parts].reverse(), null));
    expect(spec.parts.filter((p) => p.source === "b")).toEqual([parts[2]!, parts[0]!]);
  });

  test("sequence specs preserve the chosen order", () => {
    const parts = [draftFor(sources.get("b")!), draftFor(sources.get("a")!)];
    expect(buildSpec("", "sequence", 1, parts, null).parts.map((p) => p.source)).toEqual(["b", "a"]);
    expect(buildSpec("", "sequence", 1, parts, null)).not.toEqual(buildSpec("", "sequence", 1, [...parts].reverse(), null));
  });

  test("problems name what the server would reject", () => {
    expect(problems([], limits)).toEqual(["Add at least one recording from the map."]);
    const tooLong = place([draftFor(sources.get("a")!), draftFor(sources.get("b")!)], "sequence", 20, sources);
    expect(problems(tooLong, limits).join(" ")).toContain("limit is 60 s");
    const loud = place([{ ...draftFor(sources.get("a")!), gain_db: 9 }], "layer", 0, sources);
    expect(problems(loud, limits).join(" ")).toContain("gain");
  });

  test("specs round numbers and drop an empty title", () => {
    const spec = buildSpec("  ", "layer", 1, [{ ...draftFor(sources.get("a")!), offset_s: 1.23456 }], null);
    expect(spec.title).toBeUndefined();
    expect(spec.parts[0]!.offset_s).toBe(1.235);
    expect(spec.ace).toBeNull();
  });
});

describe("pulses follow onsets", () => {
  test("upper bound finds the first later onset", () => {
    expect(upperBound([1, 2, 2, 3], 2)).toBe(3);
    expect(upperBound([], 2)).toBe(0);
  });

  test("only fresh onsets of audible parts pulse", () => {
    const pulses = activePulses([[1, 2, 2.5], [2.6, 9]], 2.7, 0.9, (part) => part === 0 || part === 1);
    expect(pulses.map((p) => [p.part, p.onset_s])).toEqual([[0, 2], [0, 2.5], [1, 2.6]]);
    expect(activePulses([[1, 2, 2.5]], 2.7, 0.9, () => false)).toEqual([]);
  });

  test("a part sounds only inside its span", () => {
    const spans = [{ start_s: 0, length_s: 10 }, { start_s: 12, length_s: 5 }];
    expect(soundingParts(spans, 11)).toEqual([]);
    expect(soundingParts(spans, 12)).toEqual([1]);
  });
});

describe("server helpers", () => {
  test("paths cannot leave the served folder", () => {
    expect(safeJoin("/srv/out", "combos/x/ace.mp3")).toBe("/srv/out/combos/x/ace.mp3");
    expect(safeJoin("/srv/out", "../secret")).toBeNull();
    expect(safeJoin("/srv/out", "%2e%2e/secret")).toBeNull();
    expect(safeJoin("/srv/out", "a\0b")).toBeNull();
    expect(safeJoin("/srv/out", "%E0%A4%A")).toBeNull();
  });

  test("content types and readable log lines", () => {
    expect(contentType("a/b.webp")).toBe("image/webp");
    expect(contentType("a/b.bin")).toBe("application/octet-stream");
    expect(readableLog("2026-10-07 19:33:12.489 | INFO     | acestep.inference:generate_music:660 - Skipping LM")).toBe(false);
    expect(readableLog(" 42%|████      | 21/50 [00:02<00:03,  9.6it/s]")).toBe(false);
    expect(readableLog("combo-e3c5fb408486: 8 s → ace.wav")).toBe(true);
    expect(readableLog("# Instruction")).toBe(false);
    expect(readableLog("- bpm: N/A")).toBe(false);
    expect(readableLog("2026-10-08 | WARNING | acestep.gpu_config:_log_gpu_diagnostic_info:727 - You have installed a CPU-only version of PyTorch!")).toBe(false);
    expect(readableLog("ACE-Step: loading the music model on CPU; CPU generation is slower")).toBe(true);
    expect(readableLog("WARNING: Could not load the model")).toBe(true);
  });
});
