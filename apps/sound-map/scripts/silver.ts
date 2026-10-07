// Copy what the "Sound to silver" page shows into apps/sound-map/demo/silver, so a fresh clone can
// open it without the silver pipeline: the bench and motion pages from data/output/silver (written by
// `main.py art silver` and `art silver-motion`), the study's figures, the CLAP/FLUX concept renders and
// photographs of Livia's pieces. Images and pages are stored with Git LFS.
// Run: bun scripts/silver.ts

import { mkdir, rm } from "node:fs/promises";
import { join, resolve } from "node:path";

const ROOT = resolve(process.env.WHALES_ROOT ?? join(import.meta.dir, "..", "..", ".."));
const DEMO = join(import.meta.dir, "..", "demo", "silver");

// published name → source, relative to the repository root
const FILES: Record<string, string> = {
  "index.html": "data/output/silver/index.html",
  "motion.html": "data/output/silver/motion.html",
  "media/silver-inline-lift.png": "docs/figures/silver-inline-lift.png",
  "media/silver-roots-all.png": "docs/figures/silver-roots-all.png",
  "media/silver-roots-naive.png": "docs/figures/silver-roots-naive.png",
  "media/hardata-ii-rate-distortion.svg": "docs/figures/hardata-ii-rate-distortion.svg",
  "media/pilot-band.jpg": "docs/atlas/media/pilot-band.jpg",
  "media/livia-hardata.jpg": "docs/atlas/media/livia-hardata.jpg",
  "media/livia-mitoring.jpg": "docs/atlas/media/livia-mitoring.jpg",
  "media/livia-mycelium.jpg": "docs/atlas/media/livia-mycelium.jpg",
  "media/livia-nanot.jpg": "docs/atlas/media/livia-nanot.jpg",
  "media/mitoring-whistle.png": "data/output/jewelry/mitoring-whistle.png",
  "media/mitoring-clicks.png": "data/output/jewelry/mitoring-clicks.png",
  "media/mycelium-wavering.png": "data/output/jewelry/mycelium-wavering.png",
  "media/mycelium-neutral.png": "data/output/jewelry/mycelium-neutral.png",
};

const missing: string[] = [];
for (const source of Object.values(FILES)) if (!(await Bun.file(join(ROOT, source)).exists())) missing.push(source);
if (missing.length) {
  throw new Error(`Missing ${missing.join(", ")}. Run 'main.py art silver', 'art silver-motion' and 'art jewelry' first.`);
}
await rm(DEMO, { recursive: true, force: true });
await mkdir(join(DEMO, "media"), { recursive: true });
let bytes = 0;
for (const [name, source] of Object.entries(FILES)) bytes += await Bun.write(join(DEMO, name), Bun.file(join(ROOT, source)));
console.log(`${Object.keys(FILES).length} files, ${(bytes / 1e6).toFixed(1)} MB → ${DEMO}`);
