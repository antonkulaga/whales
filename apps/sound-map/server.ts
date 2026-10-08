// Sound map server: serves the app, the catalog and listening files, and runs combinations.
// All measurement, generation and scoring happens in Python (`main.py follow ...`); this file only
// writes a spec, runs the CLI and streams its readable log lines back as NDJSON.

import { mkdir, readdir, stat } from "node:fs/promises";
import { join, resolve } from "node:path";
import index from "./src/index.html";
import { contentType, readableLog, safeJoin } from "./src/lib/paths.ts";
import type { CombineMessage, ComboSummary, GenerationRuntime, Manifest } from "./src/lib/types.ts";

const ROOT = resolve(process.env.WHALES_ROOT ?? join(import.meta.dir, "..", ".."));
const OUTPUT = join(ROOT, "data", "output", "follow");
// Committed bundle (Git LFS, `bun scripts/demo.ts`): read when OUTPUT lacks a file, so a fresh clone plays.
const DEMO = join(import.meta.dir, "demo", "follow");
// The Sound to silver tab's files: the bench and motion pages from `main.py art silver`, else the committed copy.
const SILVER = [join(ROOT, "data", "output", "silver"), join(import.meta.dir, "demo", "silver")];
const SILVER_TYPES: Record<string, string> = { ".html": "text/html; charset=utf-8", ".jpg": "image/jpeg", ".svg": "image/svg+xml" };
const SPECS = join(ROOT, "data", "interim", "follow", "combo-specs");
// Preset names live beside the pieces, not in their manifests: re-running a piece rewrites its manifest,
// and a name must never change a piece's id.
const PRESETS = join(OUTPUT, "presets.json");
type Presets = Record<string, { name: string; saved_at_utc: string }>;
// The demo bundle ships the names of its presets, so a fresh clone shows them too; names saved here win.
const readPresets = async (): Promise<Presets> => ({
  ...(await Bun.file(join(DEMO, "presets.json")).json().catch(() => ({}))),
  ...(await Bun.file(PRESETS).json().catch(() => ({}))),
}) as Presets;
// The repository's .env sets ORCHESTRA_PORT and ORCHESTRA_HOST (`uv run start`, `bun run dev`); PORT and HOST still work.
const PORT = Number(process.env.ORCHESTRA_PORT ?? process.env.PORT ?? 3070);
const HOSTNAME = process.env.ORCHESTRA_HOST ?? process.env.HOST ?? "127.0.0.1";
const PYTHON = ["uv", "run", "--group", "art", "--group", "viz", "main.py", "follow"];
const MAX_SPEC_BYTES = 64 * 1024;

let running: Promise<unknown> | null = null; // one combination at a time: the GPU is shared
let runtimeProbe: { expires: number; result: Promise<GenerationRuntime> } | null = null;

async function generationRuntime(): Promise<Response> {
  if (!runtimeProbe || runtimeProbe.expires < Date.now()) {
    const result = (async (): Promise<GenerationRuntime> => {
      const unavailable: GenerationRuntime = { ace_available: false, cuda_available: null, device: null };
      const executable = join(ROOT, "data", "interim", "tools", "ACE-Step-1.5", ".venv", "bin", "python");
      if (!(await Bun.file(executable).exists())) return unavailable;
      try {
        // Ask the same PyTorch environment and detector used by the music runner, not nvidia-smi.
        const child = Bun.spawn([executable, join(ROOT, "experiments", "follow_ace.py"), "--runtime"], {
          cwd: ROOT, env: process.env, stdout: "pipe", stderr: "ignore",
        });
        const output = await new Response(child.stdout).text();
        if (await child.exited !== 0) return unavailable;
        return { ace_available: true, ...JSON.parse(output) } as GenerationRuntime;
      } catch { return unavailable; }
    })();
    runtimeProbe = { expires: Date.now() + 30_000, result };
  }
  return Response.json(await runtimeProbe.result, { headers: { "cache-control": "no-store" } });
}

async function python(args: string[], onLine?: (line: string) => void): Promise<{ code: number; tail: string[] }> {
  const child = Bun.spawn([...PYTHON, ...args], {
    cwd: ROOT,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    stdout: "pipe",
    stderr: "pipe",
  });
  const tail: string[] = [];
  const pump = async (stream: ReadableStream<Uint8Array>) => {
    const decoder = new TextDecoder();
    const reader = stream.getReader();
    let buffer = "";
    for (;;) {
      const { value: chunk, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(chunk, { stream: true });
      const lines = buffer.split(/\r?\n|\r/);
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        tail.push(line);
        if (tail.length > 40) tail.shift();
        onLine?.(line);
      }
    }
    if (buffer) tail.push(buffer);
  };
  await Promise.all([pump(child.stdout), pump(child.stderr)]);
  return { code: await child.exited, tail };
}

async function catalog(): Promise<Response> {
  const file = Bun.file(join(OUTPUT, "catalog.json"));
  const demo = Bun.file(join(DEMO, "catalog.json"));
  const prepared = await stat(OUTPUT).then(() => true, () => false);
  if (!(await file.exists()) && !prepared && (await demo.exists())) {
    return new Response(demo, { headers: { "content-type": "application/json" } });
  }
  if (!(await file.exists())) {
    const { code, tail } = await python(["catalog"]);
    if (code !== 0) return Response.json({ error: "Could not build the catalog. Run 'main.py follow prepare' first.", log: tail }, { status: 500 });
  }
  return new Response(Bun.file(join(OUTPUT, "catalog.json")), { headers: { "content-type": "application/json" } });
}

async function combos(): Promise<Response> {
  const out: ComboSummary[] = [];
  const seen = new Set<string>();
  const presets = await readPresets();
  for (const folder of [join(OUTPUT, "combos"), join(DEMO, "combos")]) {
    for (const name of await readdir(folder).catch(() => [] as string[])) {
      const file = Bun.file(join(folder, name, "manifest.json"));
      if (seen.has(name) || !(await file.exists())) continue;
      seen.add(name);
      const m = (await file.json()) as Manifest;
      const preset = presets[m.id];
      out.push({ id: m.id, title: preset?.name ?? m.title, created_at_utc: preset?.saved_at_utc ?? m.created_at_utc, duration_s: m.duration_s,
                 sources: m.parts.map((p) => p.source), ace: Boolean(m.stems.ace), preset: Boolean(preset) });
    }
  }
  out.sort((a, b) => b.created_at_utc.localeCompare(a.created_at_utc));
  return Response.json(out);
}

async function combo(id: string): Promise<Response> {
  if (!/^[0-9a-f]{12}$/.test(id)) return Response.json({ error: "Unknown combination" }, { status: 404 });
  for (const root of [OUTPUT, DEMO]) {
    const file = Bun.file(join(root, "combos", id, "manifest.json"));
    if (!(await file.exists())) continue;
    const manifest = (await file.json()) as Manifest;
    const preset = (await readPresets())[id];
    return Response.json(preset ? { ...manifest, title: preset.name, preset: true } : manifest);
  }
  return Response.json({ error: "Unknown combination" }, { status: 404 });
}

/** Name a piece as a preset (an empty name removes it). Only the name is stored; the piece stays as rendered. */
async function savePreset(request: Request, id: string): Promise<Response> {
  if (!/^[0-9a-f]{12}$/.test(id)) return Response.json({ error: "Unknown combination" }, { status: 404 });
  const known = await Promise.all([OUTPUT, DEMO].map((root) => Bun.file(join(root, "combos", id, "manifest.json")).exists()));
  if (!known.some(Boolean)) return Response.json({ error: "Unknown combination" }, { status: 404 });
  const body = (await request.json().catch(() => null)) as { name?: unknown } | null;
  const name = typeof body?.name === "string" ? body.name.trim().slice(0, 120) : "";
  const presets = await readPresets();
  if (name) presets[id] = { name, saved_at_utc: new Date().toISOString() };
  else delete presets[id];
  await mkdir(OUTPUT, { recursive: true });
  await Bun.write(PRESETS, JSON.stringify(presets, null, 1));
  return Response.json({ id, name: name || null });
}

async function combine(request: Request): Promise<Response> {
  if (running) return Response.json({ error: "A combination is already running. Wait for it to finish." }, { status: 409 });
  const body = await request.text();
  if (body.length > MAX_SPEC_BYTES) return Response.json({ error: "The spec is too large." }, { status: 413 });
  let spec: unknown;
  try {
    spec = JSON.parse(body);
  } catch {
    return Response.json({ error: "The spec is not valid JSON." }, { status: 400 });
  }
  const url = new URL(request.url);
  const model = url.searchParams.get("model") !== "0";
  await mkdir(SPECS, { recursive: true });
  const specPath = join(SPECS, `${new Date().toISOString().replace(/[:.]/g, "-")}.json`);
  await Bun.write(specPath, JSON.stringify(spec, null, 2));

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const send = (message: CombineMessage) => controller.enqueue(encoder.encode(JSON.stringify(message) + "\n"));
      // Blank NDJSON lines keep long CPU jobs connected without adding messages to the UI.
      const heartbeat = setInterval(() => {
        try { controller.enqueue(encoder.encode("\n")); }
        catch { clearInterval(heartbeat); }
      }, 20_000);
      const job = (async () => {
        const args = ["combine", specPath, ...(model ? [] : ["--no-model"])];
        const { code, tail } = await python(args, (line) => {
          if (readableLog(line) && !line.startsWith("ERROR: ")) send({ type: "log", text: line.trim() });
        });
        const last = tail.filter((line) => line.trim()).at(-1) ?? "";
        if (code === 0 && last.endsWith("manifest.json")) {
          send({ type: "done", manifest: (await Bun.file(last.trim()).json()) as Manifest });
        } else {
          const reason = tail.find((line) => line.startsWith("ERROR: "))?.slice(7) ?? tail.filter((line) => /Error|Traceback/.test(line)).at(-1);
          send({ type: "error", message: reason?.trim() || `Python exited with code ${code}.` });
        }
      })();
      running = job;
      job.catch((error) => send({ type: "error", message: String(error) }))
        .finally(() => {
          clearInterval(heartbeat);
          running = null;
          controller.close();
        });
    },
  });
  return new Response(stream, { headers: { "content-type": "application/x-ndjson", "cache-control": "no-store" } });
}

async function files(request: Request): Promise<Response> {
  const requested = new URL(request.url).pathname.slice("/files/".length);
  for (const root of [OUTPUT, DEMO]) {
    const path = safeJoin(root, requested);
    if (!path) return new Response("Not found", { status: 404 });
    const file = Bun.file(path);
    if (await file.exists()) {
      return new Response(file, { headers: { "content-type": contentType(path), "cache-control": "no-cache" } });
    }
  }
  return new Response("Not found", { status: 404 });
}

async function silverFiles(request: Request): Promise<Response> {
  const requested = new URL(request.url).pathname.slice("/silver/files/".length);
  for (const root of SILVER) {
    const path = safeJoin(root, requested);
    if (!path) return new Response("Not found", { status: 404 });
    const file = Bun.file(path);
    if (await file.exists()) {
      const type = SILVER_TYPES[path.slice(path.lastIndexOf(".")).toLowerCase()] ?? contentType(path);
      return new Response(file, { headers: { "content-type": type, "cache-control": "no-cache" } });
    }
  }
  return new Response("Not found", { status: 404 });
}

// Reuse the generated bench's rendering and sound analysis inside the project page.
// A shadow root keeps its controls separate from the orchestra's own IDs and styles.
async function silverViewerModule(): Promise<Response> {
  for (const root of SILVER) {
    const file = Bun.file(join(root, "index.html"));
    if (!(await file.exists())) continue;
    const html = await file.text();
    const source = html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
    if (!source) return new Response("The ring viewer module is missing", { status: 500 });
    const module = source
      .replace('from "three"', 'from "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js"')
      .replace(/from "three\/addons\/([^\"]+)"/g, 'from "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/$1"')
      .replace('const DATA = JSON.parse(document.getElementById("silver-data").textContent);', 'export function mountViewer(root, DATA) {')
      .replace('document.getElementById(id)', 'root.getElementById(id)')
      .replace('getComputedStyle(document.documentElement)', 'getComputedStyle(root.host)')
      .replace('const w = stage.clientWidth, h = stage.clientHeight;', 'const w = stage.clientWidth, h = stage.clientHeight; if (!w || !h) return;')
      .replace(' · ${piece.triangle_count.toLocaleString()} triangles shown', '')
      .replace('mode: "silver", ghost: true', 'mode: "silver", ghost: false')
      .replace('ghost.visible = true; scene.add(ghost);', 'ghost.visible = false; scene.add(ghost);')
      .replaceAll('"Play and bend"', '"▶ Play sound"')
      .replace('textContent = "Stop"', 'textContent = "■ Stop sound"')
      .replace('Drag to turn the ring. Play bends it as the sound plays.', 'Drag to turn the ring.');
    return new Response(`${module}
let previewOrigin = performance.now(), lastPreview = 0, previousPlaying = false;
let previewSound = state.sound, previewPiece = state.piece;
function animateViewer() {
  const now = performance.now(), sound = state.live || state.sound;
  if (state.playing !== previousPlaying || sound !== previewSound || state.piece !== previewPiece) {
    previewOrigin = now; previousPlaying = state.playing; previewSound = sound; previewPiece = state.piece;
  }
  if (!state.playing && now - lastPreview >= 50) {
    // A silent loop makes the sound-to-form interaction visible before the first click.
    const elapsed = (now - previewOrigin) / 1000 * Number($("speed").value);
    state.t = Math.min(elapsed % (sound.duration_s + 0.35), sound.duration_s);
    update(); lastPreview = now;
  }
  $("preview-note").textContent = state.playing ? "Playing at ¼ speed" : "Silent preview";
  $("play").setAttribute("aria-pressed", String(state.playing));
  arcLine.visible = state.playing;
  controls.update(); renderer.render(scene, camera);
}
return { setActive(active) {
  if (!active) stop();
  renderer.setAnimationLoop(active ? animateViewer : null);
  if (active) resize();
} };
}
`, {
      headers: { "content-type": "text/javascript; charset=utf-8", "cache-control": "no-cache" },
    });
  }
  return new Response("The ring viewer is missing", { status: 404 });
}

const server = Bun.serve({
  port: PORT,
  hostname: HOSTNAME,
  development: process.env.NODE_ENV !== "production",
  idleTimeout: 255, // Heartbeats keep slow ACE-Step CPU runs connected.
  routes: {
    "/": index,
    "/silver": () => Response.redirect("/?view=silver", 302), // the page is now a tab; old #idea links keep their hash
    "/silver/viewer.js": { GET: silverViewerModule },
    "/silver/files/*": { GET: silverFiles },
    "/api/catalog": { GET: catalog },
    "/api/runtime": { GET: generationRuntime },
    "/api/combos": { GET: combos },
    "/api/combos/:id": { GET: (request) => combo(request.params.id) },
    "/api/combos/:id/preset": { POST: (request) => savePreset(request, request.params.id) },
    "/api/combine": { POST: combine },
    "/files/*": { GET: files },
  },
  fetch: () => new Response("Not found", { status: 404 }),
});

console.log(`Sound map: ${server.url} (data: ${OUTPUT})`);
