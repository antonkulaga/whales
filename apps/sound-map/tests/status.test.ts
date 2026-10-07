import { describe, expect, test } from "bun:test";
import { SPECIES } from "../src/lib/species.ts";
import { THREATENED, VOICE_IDS, mostThreatened, statusLine, statusOf, voiceInfo } from "../src/lib/status.ts";
import type { Catalog, Species } from "../src/lib/types.ts";

const catalog = (await Bun.file(new URL("../demo/follow/catalog.json", import.meta.url)).json()) as Catalog;

describe("conservation status", () => {
  test("every species has a listing and sources", () => {
    for (const species of Object.keys(SPECIES) as Species[]) {
      const status = statusOf({ id: "", species });
      expect(status.listing.length).toBeGreaterThan(0);
      expect(status.refs.length).toBeGreaterThan(0);
    }
  });

  test("voice entries name recordings in the demo catalog", () => {
    const ids = new Set(catalog.sources.map((s) => s.id));
    for (const id of VOICE_IDS) expect(ids.has(id)).toBe(true);
  });

  test("every recording's card cites https sources", () => {
    for (const source of catalog.sources) {
      const { population, species, noteRefs } = voiceInfo(source);
      for (const ref of [...(population?.refs ?? []), ...noteRefs, ...species.refs]) expect(ref.url).toStartWith("https://");
    }
  });

  test("a site shows its most threatened voice", () => {
    const worst = mostThreatened([statusOf({ id: "", species: "humpback" }), statusOf({ id: "orca-bush-point", species: "killer whale" })]);
    expect(worst?.group).toBe("Southern Resident killer whales");
    expect(THREATENED.has(worst!.category)).toBe(true);
  });

  test("the status line carries the count and the trend", () => {
    const line = statusLine(statusOf({ id: "right-whale-stellwagen", species: "right whale" }));
    expect(line).toContain("384 (2024)");
    expect(line).toContain("increasing");
  });
});
