import { expect, test } from "bun:test";
import { SILVER_AUDIO_METHODS } from "../src/lib/silver-audio.ts";

function harness(ok = true, decodeFails = false) {
  const state: any = { sound: { id: "original" }, extra: null };
  const original = state.sound;
  const speed = { value: "0.25" };
  let closed = false;
  let measured: Float32Array | undefined;
  let downloads = 0;
  const length = 44100 * 13;
  class Context {
    async decodeAudioData() {
      if (decodeFails) throw new Error("Decode failed");
      return { length, sampleRate: 44100, numberOfChannels: 2,
        getChannelData: (channel: number) => new Float32Array(length).fill(channel ? .6 : .2) };
    }
    async close() { closed = true; }
  }
  const create = new Function("state", "sounds", "$", "stop", "fetch", "AudioContext", "measureOrchestra", "selectSound", "orchestraFeatures", "update",
    `return { ${SILVER_AUDIO_METHODS} };`);
  const engine = create(state, [original], () => speed, () => {},
    async () => { downloads++; return { ok, arrayBuffer: async () => new ArrayBuffer(0) }; }, Context,
    async (decoded: any) => {
      measured = new Float32Array(decoded.length);
      for (let c = 0; c < decoded.numberOfChannels; c++) {
        const channel = decoded.getChannelData(c);
        for (let i = 0; i < decoded.length; i++) measured[i] = measured[i]! + channel[i] / decoded.numberOfChannels;
      }
      return { duration_s: decoded.length / decoded.sampleRate };
    },
    (sound: any) => { state.sound = sound; state.held = false; }, new Map(), () => {});
  return { engine, state, original, speed, length, closed: () => closed, measured: () => measured, downloads: () => downloads };
}

test("orchestra audio measures the full stereo piece and uses the same audio for playback", async () => {
  const h = harness();
  await h.engine.loadSound({ title: '<Piece & "music">', kind: "Generated music", audio: "/files/ace.mp3" });
  expect(h.measured()!.length).toBe(h.length);
  expect(h.measured()![0]).toBeCloseTo(.4);
  expect(h.state.sound.duration_s).toBe(13);
  expect(h.state.sound.audio).toBe("/files/ace.mp3");
  expect(h.state.sound.title).toBe("&lt;Piece &amp; &quot;music&quot;&gt;");
  expect(h.state.sound.verified).toBe(false);
  expect(h.speed.value).toBe("1");
  expect(h.closed()).toBe(true);
  expect(h.state.sound.max_heads).toBe(32);
  expect(h.state.held).toBe(true);
  expect(h.state.t).toBe(Infinity);
  await h.engine.loadSound({ title: "Same track", kind: "music", audio: "/files/ace.mp3" });
  expect(h.downloads()).toBe(1);
  h.engine.selectRecording();
  expect(h.state.sound).toBe(h.original);
  expect(h.state.extra).toBeNull();
  expect(h.speed.value).toBe("0.25");
});

test("failed downloads and decodes preserve the selected sound and release the audio context", async () => {
  const missing = harness(false);
  await expect(missing.engine.loadSound({ audio: "/missing" })).rejects.toThrow("could not load");
  expect(missing.state.sound).toBe(missing.original);
  const broken = harness(true, true);
  await expect(broken.engine.loadSound({ audio: "/broken" })).rejects.toThrow("Decode failed");
  expect(broken.closed()).toBe(true);
  expect(broken.state.sound).toBe(broken.original);
});
