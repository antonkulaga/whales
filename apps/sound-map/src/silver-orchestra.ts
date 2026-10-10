import type { ComboSummary, Manifest } from "./lib/types.ts";

export type OrchestraAudioViewer = {
  selectRecording(): void;
  loadSound(sound: { title: string; kind: string; audio: string }): Promise<void>;
};

export function addOrchestraChoices(group: Element, engine: OrchestraAudioViewer): void {
  const recordings = group.querySelector<HTMLElement>("#sounds")!;
  const source = document.createElement("div");
  source.className = "seg sound-source";
  source.setAttribute("role", "group");
  source.setAttribute("aria-label", "Sound source");
  const orchestra = document.createElement("div");
  orchestra.hidden = true;
  const pieces = document.createElement("select");
  pieces.className = "orchestra-select";
  pieces.setAttribute("aria-label", "Orchestra piece");
  const tracks = document.createElement("div");
  tracks.className = "sounds";
  const note = document.createElement("p");
  note.className = "orchestra-note";
  note.setAttribute("role", "status");
  orchestra.append(pieces, note, tracks);
  recordings.before(source, orchestra);
  let revision = 0;
  let busy = false;
  const buttons: HTMLButtonElement[] = [];
  const report = (error: unknown) => { note.textContent = (error as Error).message; };
  const showPiece = async () => {
    const current = ++revision;
    tracks.replaceChildren();
    if (!pieces.value) return;
    note.textContent = "Loading piece…";
    try {
      const response = await fetch(`/api/combos/${encodeURIComponent(pieces.value)}`);
      if (!response.ok) throw new Error("This piece could not load. Choose another piece.");
      const manifest = await response.json() as Manifest;
      if (current !== revision) return;
      note.textContent = "Choose a track to shape the ring, then press Play sound.";
      const choices = [
        ["ace", "Orchestra music", "Generated music · ACE-Step"],
        ["response", "Musical response", "Generated musical response"],
        ["guide", "Musical guide", "Measured phrases arranged as instruments"],
        ["animal", "Animal voices", "Original recordings arranged by the orchestra"],
      ] as const;
      for (const [stem, label, kind] of choices) {
        const audio = manifest.stems[stem]?.audio;
        if (!audio) continue;
        const button = document.createElement("button");
        button.type = "button";
        button.className = "sound";
        button.setAttribute("aria-pressed", "false");
        const dot = document.createElement("span");
        dot.className = "dot";
        const title = document.createElement("b");
        title.textContent = label;
        const duration = document.createElement("em");
        duration.textContent = `${manifest.duration_s.toFixed(1)} s`;
        const detail = document.createElement("small");
        detail.textContent = kind;
        button.append(dot, title, duration, detail);
        button.addEventListener("click", async () => {
          if (busy) return;
          busy = true;
          pieces.disabled = true;
          for (const item of buttons) item.disabled = true;
          for (const item of tracks.querySelectorAll<HTMLButtonElement>("button")) item.disabled = true;
          note.textContent = "Measuring the piece for the ring…";
          try {
            await engine.loadSound({ title: manifest.title, kind, audio: `/files/${audio.split("/").map(encodeURIComponent).join("/")}` });
            for (const item of tracks.querySelectorAll("button")) item.setAttribute("aria-pressed", String(item === button));
            note.textContent = `${label} shaped the ring. Press Play sound to listen.`;
          } catch (error) { report(error); }
          finally {
            busy = false;
            pieces.disabled = false;
            for (const item of buttons) item.disabled = false;
            for (const item of tracks.querySelectorAll<HTMLButtonElement>("button")) item.disabled = false;
          }
        });
        tracks.append(button);
      }
      if (!tracks.childElementCount) note.textContent = "This piece has no playable tracks. Choose another piece.";
    } catch (error) { if (current === revision) report(error); }
  };
  pieces.addEventListener("change", () => { void showPiece(); });
  for (const [index, label] of ["Original sounds", "Orchestra pieces"].entries()) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute("aria-pressed", String(index === 0));
    buttons.push(button);
    source.append(button);
    button.addEventListener("click", async () => {
      if (busy) return;
      const current = ++revision;
      for (const item of buttons) item.setAttribute("aria-pressed", String(item === button));
      recordings.hidden = index !== 0;
      orchestra.hidden = index === 0;
      engine.selectRecording();
      if (index === 0) return;
      tracks.replaceChildren();
      pieces.replaceChildren();
      note.textContent = "Loading orchestra pieces…";
      try {
        const response = await fetch("/api/combos");
        if (!response.ok) throw new Error("Orchestra pieces could not load. Select Orchestra pieces to retry.");
        const list = await response.json() as ComboSummary[];
        if (current !== revision) return;
        // Keep named pieces easy to find ahead of the bundled combinations.
        list.sort((a, b) => Number(Boolean(b.preset)) - Number(Boolean(a.preset)));
        for (const piece of list) {
          const option = document.createElement("option");
          option.value = piece.id;
          option.textContent = piece.title;
          pieces.append(option);
        }
        pieces.hidden = !list.length;
        if (!list.length) note.textContent = "Compose a piece in the orchestra, then return here to use it on a ring.";
        else await showPiece();
      } catch (error) { if (current === revision) report(error); }
    });
  }
}
