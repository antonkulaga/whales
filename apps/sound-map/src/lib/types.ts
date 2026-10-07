// Shapes written by experiments/follow_combine.py (catalog.json, manifest.json) and the spec it reads.

export type Species =
  | "humpback" | "right whale" | "fin whale" | "blue whale" | "minke whale" | "bowhead whale"
  | "sperm whale" | "killer whale" | "false killer whale" | "pilot whale"
  | "dolphin" | "common dolphin" | "spinner dolphin" | "striped dolphin" | "rough-toothed dolphin" | "Atlantic spotted dolphin";

export interface Location {
  label: string;
  lon: number;
  lat: number;
  precision: "published" | "approximate";
  map_point?: number;
  note?: string;
}

/** Tonal events carry a thinned contour [[t, hz], ...]; clicks carry one time and a coda group. */
export type PhraseEvent =
  | { k: "t"; s: number; e: number; l: string; c: [number, number][] }
  | { k: "c"; t: number; g: number };

export interface Listening {
  audio: string;
  image: string;
  band: [number, number];
}

export interface Source {
  id: string;
  species: Species;
  title: string;
  note: string;
  duration_s: number;
  location: Location;
  material: "tonal" | "clicks";
  instrument: string;
  register_shift_octaves: number;
  events: PhraseEvent[];
  onsets_s: number[];
  files: { animal: Listening; guide: Listening };
}

export interface DatasetPoint {
  id: number;
  label: string;
  dataset: string;
  lon: number;
  lat: number;
  kind: "published" | "archive" | "regional";
  species: string[];
  source: string;
  note: string;
}

export interface CombinationLimits {
  interpretation: string;
  max_parts: number;
  max_duration_s: number;
  min_part_s: number;
  gain_db: [number, number];
  caption: string;
  audio_cover_strength: number;
}

export interface Catalog {
  created_at_utc: string;
  sources: Source[];
  points: DatasetPoint[];
  countries: string;
  combination: CombinationLimits;
  seed: number;
  species: Record<Species, { caption: string; instrument: string; material: string; lego_track: string }>;
}

export type Arrangement = "layer" | "sequence";

export interface PartDraft {
  source: string;
  offset_s: number;
  trim_s: [number, number];
  gain_db: number;
  shift_octaves: number | null;
}

export interface AceRequest {
  task: "cover" | "lego";
  caption?: string;
  audio_cover_strength: number;
  seed?: number; // omitted: the experiment seed; set by "New take"
}

export interface Spec {
  title?: string;
  arrangement: Arrangement;
  gap_s: number;
  parts: PartDraft[];
  ace?: AceRequest | null;
}

export interface Timing {
  value: number;
  null_mean: number;
  null_sd: number;
  z: number;
  p: number;
}

export interface OutputScores {
  all: Timing | null;
  parts: (Timing | null)[];
  envelope: number[];
  envelope_rate_hz: number;
  leakage?: number;
}

export interface ManifestPart {
  index: number;
  source: string;
  species: Species;
  title: string;
  trim_s: [number, number];
  offset_s: number;
  gain_db: number;
  shift_octaves: number;
  location: Location;
  instrument: string;
  events: PhraseEvent[];
  onsets_s: number[];
  files: { animal: string; guide: string };
}

export type StemName = "animal" | "guide" | "response" | "ace";

export interface Manifest {
  id: string;
  title: string;
  created_at_utc: string;
  duration_s: number;
  scale: number;
  spec: Spec & { id: string; duration_s: number; parts: ManifestPart[] };
  parts: ManifestPart[];
  stems: Partial<Record<StemName, Listening>>;
  scores: Partial<Record<"response" | "ace", OutputScores>>;
  ace: { caption: string; seed: number; task: string; seconds: number; audio_cover_strength: number } | null;
  interpretation: string;
  preset?: boolean; // set by the server when the user named this piece
}

export interface ComboSummary {
  id: string;
  title: string;
  created_at_utc: string;
  duration_s: number;
  sources: string[];
  ace: boolean;
  preset?: boolean; // named by the user; unnamed pieces are kept as recent work
}

/** Lines streamed by POST /api/combine as NDJSON. */
export type CombineMessage =
  | { type: "log"; text: string }
  | { type: "done"; manifest: Manifest }
  | { type: "error"; message: string };
export interface GenerationRuntime {
  ace_available: boolean;
  cuda_available: boolean | null;
  device: "cuda" | "cpu" | null;
}
