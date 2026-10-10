// Runs inside the generated ring viewer, sharing its analysis and selection functions.
export const SILVER_AUDIO_METHODS = `
selectRecording() {
  state.extra = null;
  $("speed").value = "0.25";
  selectSound(sounds[0]);
},
async loadSound(input) {
  stop();
  let features = orchestraFeatures.get(input.audio);
  if (!features) {
  const response = await fetch(input.audio);
  if (!response.ok) throw new Error("The orchestra audio could not load.");
  const ctx = new AudioContext();
  let decoded;
  try { decoded = await ctx.decodeAudioData(await response.arrayBuffer()); }
  finally { await ctx.close(); }
  features = await measureOrchestra(decoded);
  // Bound memory while keeping recently inspected tracks ready for instant reselection.
  if (orchestraFeatures.size >= 4) orchestraFeatures.delete(orchestraFeatures.keys().next().value);
  orchestraFeatures.set(input.audio, features);
  }
  const escape = value => String(value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[ch]);
  state.extra = { ...features, id: "orchestra", title: escape(input.title),
    kind: escape(input.kind), audio: input.audio, verified: false, summary: null, max_heads: 32 };
  $("speed").value = "1";
  selectSound(state.extra);
  // Music can last minutes: show its complete form now; Play still follows the audio.
  state.held = true; state.t = Infinity; update();
},
`;
