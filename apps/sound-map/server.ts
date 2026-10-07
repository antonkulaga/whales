// Sound map server: serves the app, the catalog and listening files, and runs combinations.
// All measurement, generation and scoring happens in Python (`main.py follow ...`); this file only
// writes a spec, runs the CLI and streams its readable log lines back as NDJSON.

import { mkdir, readdir } from "node:fs/promises";
import { join, resolve } from "node:path";
import index from "./src/index.html";
import { contentType, readableLog, safeJoin } from "./src/lib/paths.ts";
import type { CombineMessage, ComboSummary, Manifest } from "./src/lib/types.ts";

const ROOT = resolve(process.env.WHALES_ROOT ?? join(import.meta.dir, "..", ".."));
const OUTPUT = join(ROOT, "data", "output", "follow");
const SPECS = join(ROOT, "data", "interim", "follow", "combo-specs");
const PORT = Number(process.env.PORT ?? 3070);
const HOSTNAME = process.env.HOST ?? "127.0.0.1";
const PYTHON = ["uv", "run", "--group", "art", "--group", "viz", "main.py", "follow"];
const MAX_SPEC_BYTES = 64 * 1024;

let running: Promise<unknown> | null = null; // one combination at a time: the GPU is shared

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
  if (!(await file.exists())) {
    const { code, tail } = await python(["catalog"]);
    if (code !== 0) return Response.json({ error: "Could not build the catalog. Run 'main.py follow prepare' first.", log: tail }, { status: 500 });
  }
  return new Response(Bun.file(join(OUTPUT, "catalog.json")), { headers: { "content-type": "application/json" } });
}

async function combos(): Promise<Response> {
  const folder = join(OUTPUT, "combos");
  const names = await readdir(folder).catch(() => [] as string[]);
  const out: ComboSummary[] = [];
  for (const name of names) {
    const file = Bun.file(join(folder, name, "manifest.json"));
    if (!(await file.exists())) continue;
    const m = (await file.json()) as Manifest;
    out.push({ id: m.id, title: m.title, created_at_utc: m.created_at_utc, duration_s: m.duration_s,
               sources: m.parts.map((p) => p.source), ace: Boolean(m.stems.ace) });
  }
  out.sort((a, b) => b.created_at_utc.localeCompare(a.created_at_utc));
  return Response.json(out);
}

async function combo(id: string): Promise<Response> {
  if (!/^[0-9a-f]{12}$/.test(id)) return Response.json({ error: "Unknown combination" }, { status: 404 });
  const file = Bun.file(join(OUTPUT, "combos", id, "manifest.json"));
  return (await file.exists()) ? new Response(file, { headers: { "content-type": "application/json" } })
    : Response.json({ error: "Unknown combination" }, { status: 404 });
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
          running = null;
          controller.close();
        });
    },
  });
  return new Response(stream, { headers: { "content-type": "application/x-ndjson", "cache-control": "no-store" } });
}

async function files(request: Request): Promise<Response> {
  const requested = new URL(request.url).pathname.slice("/files/".length);
  const path = safeJoin(OUTPUT, requested);
  if (!path) return new Response("Not found", { status: 404 });
  const file = Bun.file(path);
  if (!(await file.exists())) return new Response("Not found", { status: 404 });
  return new Response(file, { headers: { "content-type": contentType(path), "cache-control": "no-cache" } });
}

const server = Bun.serve({
  port: PORT,
  hostname: HOSTNAME,
  development: process.env.NODE_ENV !== "production",
  idleTimeout: 255, // ACE-Step runs can take a minute; keep the stream open
  routes: {
    "/": index,
    "/api/catalog": { GET: catalog },
    "/api/combos": { GET: combos },
    "/api/combos/:id": { GET: (request) => combo(request.params.id) },
    "/api/combine": { POST: combine },
    "/files/*": { GET: files },
  },
  fetch: () => new Response("Not found", { status: 404 }),
});

console.log(`Sound map: ${server.url} (data: ${OUTPUT})`);
