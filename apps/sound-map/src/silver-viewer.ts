// Mount the existing ring engine in this page without a second scrolling document.
import { silverSTL } from "./lib/silver-stl.ts";
import type { SilverSnapshot } from "./lib/silver-stl.ts";
import { addOrchestraChoices, type OrchestraAudioViewer } from "./silver-orchestra.ts";
type Viewer = OrchestraAudioViewer & { setActive(active: boolean): void; setSpineNeutral(neutral: boolean): void; snapshot(): SilverSnapshot };
type Piece = { id: string; title: string; photo: string | null; year: number };
type ViewerModule = { mountViewer(root: ShadowRoot, data: unknown): Viewer };

let active = false;
let viewer: Viewer | undefined;
let loading: Promise<void> | undefined;

const INTEGRATED_STYLE = `
:host {
  display: block; min-width: 0; color-scheme: light;
  --plaster: #faf8f2; --sheet: #faf8f2; --ink: #242d2c; --ink-soft: #505850; --rule: #d8d5cb;
  --wax: #776899; --wax-soft: #ede8f2; --pass: #326749; --warn: #856218; --fail: #ac3832;
  --font-display: "Instrument Serif", Georgia, serif;
  --font-body: "DM Sans", system-ui, sans-serif;
  --font-data: "IBM Plex Mono", monospace;
  font: 400 .9rem/1.55 var(--font-body);
}
[hidden] { display: none !important }
.bench { display: grid; grid-template-columns: minmax(0, 1fr) minmax(280px, 340px); gap: 36px; align-items: start }
.viewer-controls { display: grid; gap: 28px; min-width: 0; padding: 18px 20px; background: #faf8f2e8 }
.viewer-controls .group { gap: 12px }
.viewer-controls .label { font: 500 1.12rem/1.35 var(--font-body); letter-spacing: 0; text-transform: none; color: var(--ink) }
.viewer-controls .seg button { min-height: 48px; padding: 12px; font-size: 1rem }
.sounds { gap: 8px }
.sound-source { margin-bottom: 12px }
.orchestra-select { width: 100%; min-height: 48px; padding: 10px; font: inherit; background: var(--sheet); color: var(--ink); border: 1px solid var(--rule) }
.orchestra-note { margin: 8px 0; color: var(--ink-soft); font-size: .85rem }
.sound { min-height: 76px; padding: 12px; border-radius: 2px; gap: 5px 10px }
.sound b { font-size: 1.02rem }
.sound small { font-size: .85rem; line-height: 1.4 }
.sound em { font-size: .8rem }
.sound .dot { width: 12px; height: 12px }
.stagecol { gap: 8px }
.spine-view { display: flex; gap: 6px; justify-content: center }
.spine-view button { min-height: 40px; padding: 8px 16px; border: 1px solid var(--rule); background: var(--sheet); color: var(--ink); font: inherit; cursor: pointer }
.spine-view button[aria-pressed="true"] { background: var(--ink); color: var(--sheet) }
.stl-export { display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 8px 14px }
.stl-export .btn { min-height: 44px; padding: 10px 18px }
.stl-export span { color: var(--ink-soft); font-size: .8rem }
.stage { height: min(62vh, 720px); min-height: 360px; aspect-ratio: auto; background: none; border: 0; border-radius: 0 }
.stage .tag { left: 0; top: 0 }
.stage .tag b { font-size: 1.5rem }
.stage .status { left: 0; bottom: 0; font-size: .7rem; max-width: 100% }
.stage .legend { bottom: 25px; right: 0 }
.viewer-play-prompt { position: absolute; left: 50%; top: 52%; transform: translate(-50%, -50%); z-index: 2; display: grid; justify-items: center; gap: 8px }
.viewer-play-prompt .btn.primary { min-height: 64px; padding: 18px 30px; font-size: 1.2rem; white-space: nowrap; background: #af462e; border-color: #af462e; color: #fffaf0; box-shadow: 0 4px 18px #242d2c24 }
:host([data-roots]) .viewer-play-prompt { top: auto; bottom: 5px; transform: translateX(-50%); }
.viewer-play-prompt .btn.primary:hover { background: #913a26 }
.preview-note { font-size: .8rem; color: var(--ink-soft); background: #faf8f2e8; padding: 3px 8px; text-align: center; white-space: nowrap }
.seg, .btn { border-radius: 2px }
.seg button[aria-pressed="true"] { background: var(--ink); color: var(--sheet) }
.btn.primary { background: var(--ink); border-color: var(--ink) }
.stage .legend { display: none }
@media (max-width: 820px) {
  .bench { grid-template-columns: minmax(0, 1fr); gap: 24px }
  .viewer-controls { grid-template-columns: 160px minmax(0, 1fr); gap: 24px }
}
@media (max-width: 560px) {
  .viewer-controls { grid-template-columns: minmax(0, 1fr); gap: 14px }
  #pieces { max-width: 240px }
  .stage { height: 52vh; min-height: 300px }
  .stage .status { font-size: .62rem }
  .viewer-play-prompt .btn.primary { min-height: 54px; padding: 14px 22px; font-size: 1rem }
}
`;

async function mount(host: HTMLElement): Promise<void> {
  const moduleUrl = new URL("/silver/viewer.js", location.href).href;
  const [response, module] = await Promise.all([
    fetch("/silver/files/index.html"),
    import(moduleUrl) as Promise<ViewerModule>,
  ]);
  if (!response.ok) throw new Error(`Ring data: ${response.status}`);
  const doc = new DOMParser().parseFromString(await response.text(), "text/html");
  const data = JSON.parse(doc.getElementById("silver-data")!.textContent!);
  const soundLabels: Record<string, { title: string; kind: string }> = {
    nana: { title: "Dolphin whistle · Nana", kind: "Recorded signature whistle · OpenWhistle" },
    neo: { title: "Dolphin whistle · Neo", kind: "Recorded whistle and clicks · OpenWhistle" },
    nsw: { title: "Dolphin whistle and clicks", kind: "Recorded non-signature whistle · OpenWhistle" },
    coda: { title: "Sperm whale clicks", kind: "Recorded coda · Dominica Sperm Whale Project" },
    wave: { title: "Wave", kind: "Generated sound · sound brush" },
  };
  data.sounds = data.sounds.map((sound: { id: string }) => ({ ...sound, ...soundLabels[sound.id] }));
  const root = host.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = doc.querySelector("style")!.textContent!.replaceAll(":root", ":host") + INTEGRATED_STYLE;
  const bench = doc.querySelector<HTMLElement>("main.bench")!;
  const stage = bench.querySelector<HTMLElement>(".stagecol")!;
  const groups = [...bench.querySelector<HTMLElement>(".ticket")!.children];
  const primary = document.createElement("aside");
  primary.className = "viewer-controls";
  primary.setAttribute("aria-label", "Choose a ring and sound");
  primary.append(...groups.slice(0, 2));
  groups[0]!.querySelector(".label")!.textContent = "Ring";
  const soundGroup = groups[1]!;
  soundGroup.querySelector(".label")!.textContent = "Choose a sound";
  const playPrompt = document.createElement("div");
  playPrompt.className = "viewer-play-prompt";
  playPrompt.append(soundGroup.querySelector("#play")!);
  const previewNote = document.createElement("span");
  previewNote.id = "preview-note";
  previewNote.className = "preview-note";
  previewNote.textContent = "Silent preview";
  playPrompt.append(previewNote);
  stage.querySelector("#stage")!.append(playPrompt);
  // The shared engine still uses these inputs, but the project view exposes only selection and playback.
  const engineControls = document.createElement("div");
  engineControls.hidden = true;
  engineControls.append(...soundGroup.querySelectorAll(".row"), soundGroup.querySelector("#sound-note")!,
    stage.querySelector(".strip")!, ...groups.slice(2));
  const slot = document.createElement("slot");
  slot.name = "reference";
  stage.append(slot);
  bench.replaceChildren(stage, primary, engineControls);
  // The standalone research report supplies IDs used by the shared engine, but is not repeated here.
  const report = doc.querySelector<HTMLElement>(".explain")!;
  report.hidden = true;
  root.append(style, bench, report);

  const reference = host.querySelector<HTMLElement>(".silver-ring-reference")!;
  const syncPhoto = () => {
    const name = root.getElementById("piece-name")!.textContent;
    const piece = (data.pieces as Piece[]).find(item => item.title === name);
    if (!piece?.photo) return;
    const image = reference.querySelector("img")!;
    image.src = piece.photo;
    image.alt = `${piece.title}, cast silver, photographed by Livia Zaharia`;
    reference.querySelector("[data-reference-name]")!.textContent = piece.title;
    reference.querySelector("[data-reference-year]")!.textContent = String(piece.year);
  };
  new MutationObserver(syncPhoto).observe(root.getElementById("piece-name")!, { childList: true });
  viewer = module.mountViewer(root, data);
  addOrchestraChoices(soundGroup, viewer);
  const spineView = document.createElement("div");
  spineView.className = "spine-view";
  spineView.setAttribute("aria-label", "Inline spine view");
  for (const [label, neutral] of [["Neutral", true], ["Sound", false]] as const) {
    const button = document.createElement("button");
    button.type = "button"; button.textContent = label;
    button.dataset.neutral = String(neutral);
    button.setAttribute("aria-pressed", String(neutral));
    button.addEventListener("click", () => {
      viewer!.setSpineNeutral(neutral);
      for (const sibling of spineView.querySelectorAll("button")) sibling.setAttribute("aria-pressed", String(sibling === button));
    });
    spineView.append(button);
  }
  stage.querySelector("#stage")!.after(spineView);
  const exportRow = document.createElement("div");
  exportRow.className = "stl-export";
  const exportButton = document.createElement("button");
  exportButton.type = "button"; exportButton.className = "btn";
  exportButton.textContent = "Export STL";
  const exportNote = document.createElement("span");
  exportNote.textContent = "Current shape · mm · lightly smoothed";
  exportNote.setAttribute("role", "status");
  exportButton.addEventListener("click", () => {
    exportButton.disabled = true;
    exportNote.textContent = "Smoothing the current shape…";
    const snapshot = viewer!.snapshot();
    // Allow the busy state to paint before processing the captured mesh.
    setTimeout(() => {
      try {
        const url = URL.createObjectURL(new Blob([silverSTL(snapshot.meshes)], { type: "model/stl" }));
        const link = document.createElement("a");
        link.href = url; link.download = `${snapshot.name.replace(/[^a-z0-9._-]/gi, "-")}.stl`;
        document.body.append(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 60_000);
        exportNote.textContent = "STL saved · mm · lightly smoothed";
      } catch (error) {
        console.error("Could not export ring", error);
        exportNote.textContent = "Export failed. Please try again.";
      } finally { exportButton.disabled = false; }
    }, 0);
  });
  exportRow.append(exportButton, exportNote);
  spineView.after(exportRow);
  const description = document.getElementById("silver-shape-description");
  const inlineDescription = description?.innerHTML || "";
  const syncSpineView = () => {
    const isRoots = root.getElementById("piece-name")!.textContent === "Roots Ring";
    spineView.hidden = isRoots;
    root.host.toggleAttribute("data-roots", isRoots);
    if (description) description.innerHTML = isRoots ? "Roots keeps its three original cupped heads. The recording grows more around the front and sides: peaks set the number, intensity sets the size, and the waveform distributes their angles. Rounded cups and curved stems retain a minimum thickness. Select a recording for a silent preview, or press <b>Play sound</b>." : inlineDescription;
  };
  new MutationObserver(syncSpineView).observe(root.getElementById("piece-name")!, { childList: true });
  syncSpineView();
  root.querySelector<HTMLCanvasElement>("#stage canvas")!.setAttribute("aria-label", "Interactive ring shaped by the recording; drag to turn");
  syncPhoto();
  host.querySelector(".silver-loading")?.remove();
  viewer.setActive(active);
}

export function setSilverViewerActive(next: boolean): void {
  active = next;
  if (viewer) { viewer.setActive(active); return; }
  if (!active || loading) return;
  const host = document.getElementById("silver-viewer");
  if (!host) return;
  loading = mount(host).catch(error => {
    console.error("Could not load the ring viewer", error);
    host.querySelector(".silver-loading")?.remove();
    const message = document.createElement("p");
    message.setAttribute("role", "alert");
    message.textContent = "The ring animation could not load. Please reload the page.";
    (host.shadowRoot ?? host).prepend(message);
  });
}
