// Export a read-only Phrase Atlas next to the media it plays (data/output/follow):
//   atlas.html      page body without a document skeleton, ready to publish as an Artifact
//   atlas-app.js    bundled app in static mode; atlas.css; combos.json
//   atlas-files.json  every file the page reads, relative to data/output/follow
// Run: bun run export

import { readdir } from "node:fs/promises";
import { join, resolve } from "node:path";
import type { Catalog, ComboSummary, Manifest } from "../src/lib/types.ts";

const ROOT = resolve(process.env.WHALES_ROOT ?? join(import.meta.dir, "..", "..", ".."));
const OUTPUT = join(ROOT, "data", "output", "follow");
const APP = join(import.meta.dir, "..");

const build = await Bun.build({ entrypoints: [join(APP, "src", "main.ts")], target: "browser", format: "esm", minify: true });
if (!build.success) throw new AggregateError(build.logs, "Bundling failed");
await Bun.write(join(OUTPUT, "atlas-app.js"), build.outputs[0]!);
await Bun.write(join(OUTPUT, "atlas.css"), Bun.file(join(APP, "src", "style.css")));

const catalog = (await Bun.file(join(OUTPUT, "catalog.json")).json()) as Catalog;
const manifests: Manifest[] = [];
for (const id of await readdir(join(OUTPUT, "combos"))) {
  const file = Bun.file(join(OUTPUT, "combos", id, "manifest.json"));
  if (await file.exists()) manifests.push((await file.json()) as Manifest);
}
manifests.sort((a, b) => b.created_at_utc.localeCompare(a.created_at_utc));
// Preset names live beside the pieces (written by POST /api/combos/:id/preset); manifests stay as rendered.
const presetFile = Bun.file(join(OUTPUT, "presets.json"));
const presets = (await presetFile.exists() ? await presetFile.json() : {}) as Record<string, { name: string; saved_at_utc: string }>;
const summaries: ComboSummary[] = manifests.map((m) => ({
  id: m.id, title: presets[m.id]?.name ?? m.title, created_at_utc: presets[m.id]?.saved_at_utc ?? m.created_at_utc, duration_s: m.duration_s,
  sources: m.parts.map((p) => p.source), ace: Boolean(m.stems.ace), preset: Boolean(presets[m.id]),
}));
await Bun.write(join(OUTPUT, "combos.json"), JSON.stringify(summaries));

const files = new Set<string>(["atlas-app.js", "atlas.css", "catalog.json", "combos.json", catalog.countries]);
for (const source of catalog.sources) {
  for (const listening of Object.values(source.files)) {
    files.add(listening.audio);
    files.add(listening.image);
  }
}
for (const m of manifests) {
  files.add(`combos/${m.id}/manifest.json`);
  for (const stem of Object.values(m.stems)) {
    if (!stem) continue;
    files.add(stem.audio);
    files.add(stem.image);
  }
  for (const part of m.parts) {
    files.add(part.files.animal);
    files.add(part.files.guide);
  }
}
let bytes = 0;
for (const path of files) {
  const file = Bun.file(join(OUTPUT, path));
  if (!(await file.exists())) throw new Error(`Missing ${path}; rerun 'main.py follow catalog' or the combination`);
  bytes += file.size;
}
await Bun.write(join(OUTPUT, "atlas-files.json"), JSON.stringify([...files].sort(), null, 1));

// The page body from index.html, with the static flag and the bundled script instead of main.ts.
const html = await Bun.file(join(APP, "src", "index.html")).text();
const head = html.match(/<title>[\s\S]*?(?=<link rel="stylesheet" href="\.\/style\.css">)/)?.[0] ?? "<title>Phrase Atlas</title>";
const body = html.match(/<body>([\s\S]*)<\/body>/)?.[1] ?? "";
const page = `${head.trim()}
<link rel="stylesheet" href="atlas.css">
${body.replace('<script type="module" src="./main.ts"></script>', '<script>window.PHRASE_ATLAS_STATIC = true;</script>\n  <script type="module" src="atlas-app.js"></script>').trim()}
`;
await Bun.write(join(OUTPUT, "atlas.html"), page);
console.log(`atlas.html + ${files.size} files, ${(bytes / 1e6).toFixed(1)} MB → ${OUTPUT}`);
