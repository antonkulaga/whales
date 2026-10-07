// One row per species in resources/follow-music.json: its map colour (a style.css variable), its icon under
// species/ (PhyloPic silhouettes, credited in species/credits.json) and the short label under a chair.
// Baleen whales take blues and greens, toothed whales reds and violets, dolphins golds and browns.

import type { Species } from "./types.ts";

export const SPECIES: Record<Species, { color: string; icon: string; seat: string }> = {
  humpback: { color: "var(--humpback)", icon: "humpback", seat: "Humpback" },
  "right whale": { color: "var(--right)", icon: "right-whale", seat: "Right whale" },
  "fin whale": { color: "var(--fin)", icon: "fin-whale", seat: "Fin whale" },
  "blue whale": { color: "var(--blue)", icon: "blue-whale", seat: "Blue whale" },
  "minke whale": { color: "var(--minke)", icon: "minke-whale", seat: "Minke" },
  "bowhead whale": { color: "var(--bowhead)", icon: "bowhead-whale", seat: "Bowhead" },
  "sperm whale": { color: "var(--sperm)", icon: "sperm-whale", seat: "Sperm whale" },
  "killer whale": { color: "var(--orca)", icon: "killer-whale", seat: "Orca" },
  "false killer whale": { color: "var(--false-killer)", icon: "false-killer-whale", seat: "False killer" },
  "pilot whale": { color: "var(--pilot)", icon: "pilot-whale", seat: "Pilot whale" },
  dolphin: { color: "var(--dolphin)", icon: "dolphin", seat: "Dolphin" },
  "common dolphin": { color: "var(--common)", icon: "common-dolphin", seat: "Common" },
  "spinner dolphin": { color: "var(--spinner)", icon: "spinner-dolphin", seat: "Spinner" },
  "striped dolphin": { color: "var(--striped)", icon: "striped-dolphin", seat: "Striped" },
  "rough-toothed dolphin": { color: "var(--rough-toothed)", icon: "rough-toothed-dolphin", seat: "Rough-toothed" },
  "Atlantic spotted dolphin": { color: "var(--spotted)", icon: "atlantic-spotted-dolphin", seat: "Spotted" },
};

/** Icon files the demo bundle and the static export copy. */
export const SPECIES_ICON_FILES = Object.values(SPECIES).map((s) => `species/${s.icon}.png`);
