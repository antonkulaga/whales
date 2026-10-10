import { expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { SILVER_AUDIO_RUNTIME } from "../src/lib/silver-performance.ts";

const template = readFileSync(new URL("../../../experiments/silver_page.html", import.meta.url), "utf8");
const config = JSON.parse(readFileSync(new URL("../../../resources/sound-silver.json", import.meta.url), "utf8"));
const featuresSource = template.slice(template.indexOf("function fft("), template.indexOf("// Roots keeps"));
const featureAPI = new Function("TAU", "F", `${featuresSource}; return { fft, spectralFrame, normalise, analyse, BAND, TONALITY_DB };`)(2 * Math.PI, config.features);

test("bounded music analysis retains the full timeline and measured pitch", () => {
  const rate = 8000, samples = Float32Array.from({ length: rate * 60 }, (_, i) => .5 * Math.sin(2 * Math.PI * 1000 * i / rate));
  const measured = featureAPI.analyse(samples, rate, 4096);
  expect(measured.duration_s).toBe(60);
  expect(measured.time_s.length).toBeLessThanOrEqual(4096);
  expect(measured.time_s.at(-1)).toBeGreaterThan(59.8);
  expect(measured.hz.filter((hz: number | null) => hz !== null).length).toBeGreaterThan(4000);
  expect(measured.hz[100]).toBeCloseTo(1000, 1);
});

test("worker measures stereo without changing decoded audio and releases its resources", async () => {
  const urls = new Map<string, Blob>();
  let terminated = false, transferred = 0;
  const urlAPI = { createObjectURL: (blob: Blob) => { urls.set("worker", blob); return "worker"; }, revokeObjectURL: (url: string) => urls.delete(url) };
  class WorkerHarness {
    onmessage!: (event: any) => void;
    onerror!: (event: any) => void;
    constructor(private url: string) {}
    postMessage(data: any, buffers: ArrayBuffer[]) {
      transferred = buffers.length;
      void urls.get(this.url)!.text().then(source => {
        const handler = new Function("postMessage", `let onmessage; ${source}; return onmessage;`)((result: any) => this.onmessage({ data: result }));
        handler({ data });
      });
    }
    terminate() { terminated = true; }
  }
  const measure = new Function("TAU", "F", "fft", "spectralFrame", "normalise", "analyse", "BAND", "TONALITY_DB", "Worker", "URL", `${SILVER_AUDIO_RUNTIME}; return measureOrchestra;`)(
    2 * Math.PI, config.features, featureAPI.fft, featureAPI.spectralFrame, featureAPI.normalise, featureAPI.analyse, featureAPI.BAND, featureAPI.TONALITY_DB, WorkerHarness, urlAPI);
  const left = Float32Array.from({ length: 8000 }, (_, i) => Math.sin(2 * Math.PI * 1000 * i / 8000)), right = left.slice();
  const before = left.slice();
  const decoded = { numberOfChannels: 2, sampleRate: 8000, getChannelData: (i: number) => i ? right : left };
  const result = await measure(decoded);
  expect(result.duration_s).toBe(1);
  expect(result.hz[20]).toBeCloseTo(1000, 1);
  expect(left).toEqual(before);
  expect(transferred).toBe(2);
  expect(terminated).toBe(true);
  expect(urls.size).toBe(0);
  await expect(measure({ ...decoded, getChannelData: () => new Float32Array(1) })).rejects.toThrow("too short");
  expect(urls.size).toBe(0);
});

test("integrated profiles skip unused band work and cache complete Inline peak locations", () => {
  const source = template.slice(template.indexOf("const inlineFullWaves"), template.indexOf("// ------------------------------------------------------------ features"));
  let fullWaves = 0;
  const profiles = new Function("M", "TAU", "INTEGRATED_VIEWER", "inlineWave", "inlineNodes", `${source};return profiles;`)(config.mapping, 2 * Math.PI, true,
    (_sound: any, until = Infinity) => { if (!Number.isFinite(until)) fullWaves++; return new Float64Array([0, .5, 0]); }, () => [.5]);
  const sound = {};
  expect(profiles(sound, { roots: true }).lift.every((v: number) => v === 0)).toBe(true);
  const first = profiles(sound, { spine: true });
  first.wave.fill(0); // Neutral view must not erase the cache's sound wave.
  expect(profiles(sound, { spine: true }).wave[1]).toBe(.5);
  expect(profiles(sound, { spine: true }, .2).nodes).toEqual([.5]);
  expect(fullWaves).toBe(1);
});

test("long orchestra tracks retain their strongest Roots peaks in temporal order", () => {
  const source = template.slice(template.indexOf("const rootsPlans"), template.indexOf("function rootsAnchor"));
  const rootsPlan = new Function("TAU", `${source}; return rootsPlan;`)(2 * Math.PI);
  const sound = { time_s: Array.from({ length: 600 }, (_, i) => i * .02), level: Array.from({ length: 600 }, (_, i) => i % 6 === 3 ? .5 + i / 1200 : 0) };
  const all = rootsPlan(sound), bounded = rootsPlan({ ...sound, max_heads: 32 });
  expect(all.length).toBeGreaterThan(32);
  expect(bounded.length).toBe(32);
  expect(bounded.map((head: any) => head.time)).toEqual(all.slice(-32).map((head: any) => head.time));
});
