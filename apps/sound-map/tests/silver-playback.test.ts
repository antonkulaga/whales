import { expect, test } from "bun:test";
import { readFileSync } from "node:fs";

const server = readFileSync(new URL("../server.ts", import.meta.url), "utf8");
const previewStart = server.indexOf("let previewOrigin");
const preview = server.slice(previewStart, server.indexOf("\nreturn {", previewStart));

for (const file of ["../../../experiments/silver_page.html", "../demo/silver/index.html"]) {
  const html = readFileSync(new URL(file, import.meta.url), "utf8");
  const playback = html.slice(html.indexOf("function stop()"), html.indexOf("async function loadFile"));

  test(`${file}: dragging keeps growth and the bubble on the audio clock; completed shape stays`, () => {
    const callbacks: (() => void)[] = [];
    const elements = new Map<string, any>();
    const $ = (id: string) => {
      if (!elements.has(id)) elements.set(id, { value: "1", textContent: "", getAttribute() {}, setAttribute() {} });
      return elements.get(id);
    };
    const sound = { id: "nana", audio: "nana.wav", duration_s: 2 };
    const audio = { currentTime: 0, play: () => Promise.resolve(), pause() {}, onended: () => {} };
    const state = { piece: { id: "roots" }, sound, live: null, playing: false, held: false, t: 0, audio };
    let now = 160, updates = 0, markers = 0, renders = 0;
    const api = new Function("state", "$", "performance", "requestAnimationFrame", "update", "placeHead", "root", "controls", "renderer", `
      let rotating=true, lastGeometryTick=0, needsRender=false;
      const scene={}, camera={}, arcLine={visible:false};
      ${playback}
      ${preview}
      return { play, animateViewer };
    `)(state, $, { now: () => now }, (fn: () => void) => callbacks.push(fn), () => updates++, () => markers++,
      { querySelectorAll: () => [] }, { update: () => true }, { render: () => renders++ });

    api.play();
    expect(state.held).toBe(true);
    audio.currentTime = 0.5;
    callbacks.shift()!();
    expect(state.t).toBe(0.5);
    expect(updates).toBe(2);
    expect(markers).toBe(1);
    now = 170; audio.currentTime = 0.6;
    callbacks.shift()!();
    expect(updates).toBe(2);
    expect(markers).toBe(2);
    audio.onended();
    expect(state.t).toBe(Infinity);
    expect(state.playing).toBe(false);
    const completedUpdates = updates;
    for (now = 200; now < 500; now += 60) api.animateViewer();
    expect(updates).toBe(completedUpdates);
    expect(state.t).toBe(Infinity);
    expect($("preview-note").textContent).toBe("Generated shape · drag to inspect");
    expect(renders).toBeGreaterThan(0);
    api.play();
    expect(state.t).toBe(0);
    expect(state.playing).toBe(true);
    api.play(); // Stop finishes the generated form and keeps it available to inspect.
    expect(state.t).toBe(Infinity);
    expect(state.held).toBe(true);
    api.animateViewer();
    expect(state.t).toBe(Infinity);
    state.held = false; // Selecting a new recording resets the preview.
    now += 100;
    api.animateViewer();
    expect(Number.isFinite(state.t)).toBe(true);
  });
}
