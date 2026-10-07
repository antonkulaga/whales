// Copy a playable Phrase Atlas bundle into apps/sound-map/demo/follow so a fresh clone can run the
// app without the Python pipeline. Only what the player reads is copied: MP3 stems, WebP
// spectrograms, catalog.json, the country outlines and each combination's manifest.json.
// Audio and images are stored with Git LFS (see the root .gitattributes).
// Run: bun scripts/demo.ts [combo-id,combo-id,...]   (default: every combination)

import { mkdir, readdir, rm } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { SPECIES_ICON_FILES } from "../src/lib/species.ts";
import type { Catalog, Manifest } from "../src/lib/types.ts";

const ROOT = resolve(process.env.WHALES_ROOT ?? join(import.meta.dir, "..", "..", ".."));
const OUTPUT = join(ROOT, "data", "output", "follow");
const DEMO = join(import.meta.dir, "..", "demo", "follow");
const artwork = ["concert-hall-atlas-v1.png", "concert-hall-atlas-v1.prompt.json", ...SPECIES_ICON_FILES, "species/credits.json",
  // Retain the About photos and Installation concepts when refreshing the playback bundle.
  "about/livia.jpg", "about/anton.jpg", "about/inline-ring.jpg", "about/roots-ring.jpg", "about/hardata.jpg", "about/livistone.jpg",
  "installation/listening-room-v1.png", "installation/whale-figures-v1.png", "installation/concepts-v1.prompt.json"];
// Preserve the shared artwork before replacing the demo, even after a fresh measurement run.
for (const path of artwork) {
  if (!(await Bun.file(join(OUTPUT, path)).exists())) {
    await Bun.write(join(OUTPUT, path), Bun.file(join(DEMO, path)));
  }
}

const catalog = (await Bun.file(join(OUTPUT, "catalog.json")).json()) as Catalog;
const wanted = process.argv[2]?.split(",").filter(Boolean);
const ids = wanted ?? (await readdir(join(OUTPUT, "combos")));
const manifests: Manifest[] = [];
for (const id of ids) {
  const file = Bun.file(join(OUTPUT, "combos", id, "manifest.json"));
  if (await file.exists()) manifests.push((await file.json()) as Manifest);
  else if (wanted) throw new Error(`No combination ${id} in ${OUTPUT}/combos`);
}

// Provenance fields hold absolute paths on the machine that rendered them; keep them repository-relative.
function relativize<T>(value: T): T {
  if (typeof value === "string") return (value.startsWith(ROOT + "/") ? value.slice(ROOT.length + 1) : value) as T;
  if (Array.isArray(value)) return value.map(relativize) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, relativize(v)])) as T;
  }
  return value;
}

const media = new Set<string>([catalog.countries, ...artwork]);
for (const source of catalog.sources) {
  for (const listening of Object.values(source.files)) media.add(listening.audio).add(listening.image);
}
for (const m of manifests) {
  for (const stem of Object.values(m.stems)) if (stem) media.add(stem.audio).add(stem.image);
  for (const part of m.parts) media.add(part.files.animal).add(part.files.guide);
}

await rm(DEMO, { recursive: true, force: true });
let bytes = 0;
const write = async (path: string, data: Blob | string) => {
  await mkdir(dirname(join(DEMO, path)), { recursive: true });
  bytes += await Bun.write(join(DEMO, path), data);
};
for (const path of [...media].sort()) {
  const file = Bun.file(join(OUTPUT, path));
  if (!(await file.exists())) throw new Error(`Missing ${path}; rerun 'main.py follow catalog' or the combination`);
  await write(path, file);
}
await write("catalog.json", JSON.stringify(relativize(catalog)));
for (const m of manifests) await write(`combos/${m.id}/manifest.json`, JSON.stringify(relativize(m), null, 1));
// Preset names for the bundled pieces travel with them; the server reads them when data/output has none.
const presetFile = Bun.file(join(OUTPUT, "presets.json"));
const presets = (await presetFile.exists() ? await presetFile.json() : {}) as Record<string, { name: string; saved_at_utc: string }>;
const shipped = Object.fromEntries(manifests.filter((m) => presets[m.id]).map((m) => [m.id, presets[m.id]]));
if (Object.keys(shipped).length) await write("presets.json", JSON.stringify(shipped, null, 1));

const rows = catalog.sources.map((s) => `| \`${s.id}\` | ${s.title} | ${s.location.label} | ${s.note ?? ""} |`);
const combos = manifests
  .sort((a, b) => a.title.localeCompare(b.title))
  .map((m) => `| \`${m.id}\` | ${m.title} | ${m.parts.map((p) => p.source).join(", ")} | ${m.stems.ace ? "yes" : "no"} |`);
await write("README.md", `# Phrase Atlas demo bundle

A copy of what the player needs from \`data/output/follow\`: ${catalog.sources.length} source excerpts and
${manifests.length} finished combinations, as MP3 stems and WebP spectrograms (Git LFS). The server reads it
whenever \`data/output/follow\` has not been built, so \`bun run dev\` works on a fresh clone.
Making new combinations still needs the Python pipeline. Regenerate with \`bun scripts/demo.ts\`.

Excerpt choices, measurement settings and download URLs are in \`resources/follow-music.json\`;
the method is in \`docs/follow-the-phrase.md\`. Guides, responses and ACE-Step stems are generated;
only the animal stems are recordings.

## Sources

| Id | Recording | Place | Note |
|---|---|---|---|
${rows.join("\n")}

## Combinations

| Id | Title | Parts | ACE-Step |
|---|---|---|---|
${combos.join("\n")}
`);
console.log(`${media.size} media files + ${manifests.length} manifests, ${(bytes / 1e6).toFixed(1)} MB → ${DEMO}`);
