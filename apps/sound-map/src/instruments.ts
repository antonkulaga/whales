// Line icons for the guide instruments, keyed by instrument name rather than species, so a chair
// that later plays another instrument still shows the right one. The guide synthesises these
// timbres; the icons name the family, not a sampled instrument.

const DOT = (x: number, y: number, r = .85) => `<circle class="dot" cx="${x}" cy="${y}" r="${r}"/>`;

const SHAPES: Record<string, string> = {
  // a violin with its bow standing beside it (a bow across the body reads as "crossed out")
  "bowed tone": `<path class="tint" d="M9 9.2c-2.3 0-3.6 1.2-3.6 2.7 0 .9.8 1.4.8 2.1s-1.2 1.3-1.2 3c0 2.2 1.8 3.5 4 3.5s4-1.3 4-3.5c0-1.7-1.2-2.3-1.2-3s.8-1.2.8-2.1c0-1.5-1.3-2.7-3.6-2.7z"/><path d="M9 9.2V2.8M8 3.2h2M8 15.8h2M18.8 2.5c1 5.5 1 13.5 0 19M17.6 19.6h2.2"/>`,
  // transverse flute: a tube with an embouchure hole and three finger holes
  "flute-like tone": `<path class="tint" d="M2.47 15.9 19.47 4.9a1.9 1.9 0 0 1 2.06 3.2L4.53 19.1a1.9 1.9 0 0 1-2.06-3.2z"/>${DOT(6.05, 15.85, 1)}${DOT(12, 12)}${DOT(14.04, 10.68)}${DOT(16.08, 9.36)}`,
  // a mallet striking one wooden bar
  "wood mallet": `<path class="tint" d="M4 17h16a1.75 1.75 0 0 1 0 3.5H4A1.75 1.75 0 0 1 4 17z"/><path d="M20.5 3.5l-7.3 7.9"/>${DOT(7, 18.75, .7)}${DOT(17, 18.75, .7)}${DOT(11.9, 12.9, 2.2)}`,
  // saxophone: mouthpiece, body, bend and bell
  "reed tone": `<path class="thick" d="M5.5 3.2 8.8 5.2c.8.5 1.2 1.3 1.2 2.2v8.1a3.3 3.3 0 0 0 6.6 0V13"/><path class="dot" d="M15.6 13.2h2l1.2-3.6h-4.4z"/>`,
  // cello: a large body on its endpin, scroll, and a bow crossing the strings low and level
  "cello tone": `<path class="tint" d="M12 6.8c-2.9 0-4.4 1.5-4.4 3.4 0 1.1 1 1.7 1 2.6s-1.5 1.6-1.5 3.7c0 2.7 2.2 4.3 4.9 4.3s4.9-1.6 4.9-4.3c0-2.1-1.5-2.8-1.5-3.7s1-1.5 1-2.6c0-1.9-1.5-3.4-4.4-3.4z"/><path d="M12 6.8V2.5M11 2.8h2M12 20.8v2M10.8 15.6h2.4M3 13.2l18 1.6"/>`,
  // french horn: coiled tubing, mouthpiece and a bell opening up and right
  "horn tone": `<circle cx="10" cy="13.5" r="5.5"/><circle cx="10" cy="13.5" r="2.4"/><path d="M4.5 13.5H2.4M2.4 12.4v2.2M14.2 10l1.6-1.6"/><path class="dot" d="M14.8 9.4 16.4 3.8l5.8 5.8z"/>`,
  // tuba: wide bell on top, conical body, rounded foot, three valves
  "tuba tone": `<path class="tint" d="M5 3.5h12l-3.2 5.3v7.7a3.6 3.6 0 0 1-7.2 0V8.8z"/><path d="M14.5 11h3.5M14.5 13.2h3.5M14.5 15.4h3.5M7.6 12H4.5V9.5"/>`,
  // organ: five pipes, the middle one tallest, on a bench
  "organ tone": `<path class="tint" d="M3.8 11V15.5L5 19.5l1.2-4V11zM7.3 7.5V15.5L8.5 19.5l1.2-4V7.5zM10.8 4V15.5L12 19.5l1.2-4V4zM14.3 7.5V15.5L15.5 19.5l1.2-4V7.5zM17.8 11V15.5L19 19.5l1.2-4V11z"/><path d="M4.3 13.6h1.4M7.8 13.6h1.4M11.3 13.6h1.4M14.8 13.6h1.4M18.3 13.6h1.4M2.5 21h19"/>`,
  // a bell with its clapper
  "bell tone": `<path class="tint" d="M5 17.5h14c-1.4-1.4-1.9-3-1.9-6a5.1 5.1 0 0 0-10.2 0c0 3-.5 4.6-1.9 6z"/><path d="M12 4.2v2.2"/>${DOT(12, 19.6, 1.5)}`,
  // trumpet: mouthpiece, valves, looped tubing and a flared bell
  "trumpet tone": `<path d="M2.5 10v2.4M2.5 11.2h12.5M6 11.2v3.6h9v-3.6M8 11.2V7.6M10.5 11.2V7.6M13 11.2V7.6M7.3 7.6h1.4M9.8 7.6h1.4M12.3 7.6h1.4"/><path class="dot" d="M15 9.8 21.5 6.5v9.4L15 12.6z"/>`,
  // glass harmonica: a wine glass rubbed to ring
  "glass tone": `<path class="tint" d="M6.5 3h10c0 5.2-2 8.6-5 8.6s-5-3.4-5-8.6z"/><path d="M11.5 11.6V19M7.8 20.2h7.4M18.8 4.6c1.1.9 1.1 2.5 0 3.4M20.6 3.2c2 1.7 2 4.5 0 6.2"/>`,
  // pan flute: graded tubes with a binding band
  "pan flute": `<path class="thick" d="M5 4v16M7.8 4v14M10.6 4v12M13.4 4v10M16.2 4v8M19 4v6"/><path d="M3.6 7.4h16.8"/>`,
  // ocarina: rounded body, mouthpiece, finger holes
  "ocarina tone": `<path class="tint" d="M5 13.5c0-4 3.6-7 8.3-7S21.5 9.3 21.5 13s-3.7 5.5-8.4 5.5S5 17.4 5 13.5z"/><path d="M5.4 12.2 2 11.1v3.6l3.3-.6"/>${DOT(10.5, 10.6)}${DOT(13.6, 10)}${DOT(16.8, 10.8)}${DOT(13, 15)}`,
  // theremin: cabinet, upright pitch antenna, loop volume antenna, sound waves
  "theremin tone": `<path class="tint" d="M3.5 13h15v5.5h-15z"/><path d="M16.5 13V2.5M6.5 13v-2.6M6.5 10.4H4.3a1.8 1.8 0 0 1 0-3.6h2.2M5.5 18.5V21M16.5 18.5V21M19.6 5c.9.8.9 2.2 0 3M21.3 3.6c1.8 1.6 1.8 4.2 0 5.8"/>`,
  // recorder: beak, window, straight body with finger holes, slightly tilted
  "recorder tone": `<g transform="rotate(28 12 12)"><path d="M10.6 2.5h2.8l-.3 3.4h-2.2zM11.1 7.6h1.8M10.9 5.9v15M13.1 5.9v15M10.5 20.9h3"/>${DOT(12, 10.6)}${DOT(12, 13)}${DOT(12, 15.4)}${DOT(12, 17.8)}</g>`,
  // singing saw: a handle and a blade bent into an S
  "singing saw": `<path class="tint" d="M6 9.2c3.8-1 6.2 2.8 9.2 2.8 2.4 0 3.8-1.9 6.3-1.9v4.3c-2.5 0-3.9 1.9-6.3 1.9-3 0-5.4-3.8-9.2-2.8z"/><path d="M6 8.6v5.8M6 9.4 2.6 8.9v5.4l3.4-.5M8 14.6l.9 1.1.9-1.1l.9 1.1.9-1.1l.9 1.1.9-1.1l.9 1.1.9-1.1l.9 1.1.9-1.1l.9 1.1.9-1.1"/>`,
};
const NOTE = `<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>`;

/** Inline SVG for a guide instrument; unknown names fall back to a note. Decorative: pair it with the name or a title. */
export function instrumentIcon(name: string, className = "instrument-icon"): string {
  return `<svg class="${className}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${SHAPES[name] ?? NOTE}</svg>`;
}
