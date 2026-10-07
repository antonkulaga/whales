// Server-side path safety: requested files must stay inside the served output folder.

import { resolve, sep } from "node:path";

export function safeJoin(root: string, requested: string): string | null {
  const decoded = (() => {
    try {
      return decodeURIComponent(requested);
    } catch {
      return null;
    }
  })();
  if (decoded === null || decoded.includes("\0")) return null;
  const base = resolve(root);
  const target = resolve(base, "." + sep + decoded.replace(/^\/+/, ""));
  return target === base || target.startsWith(base + sep) ? target : null;
}

const TYPES: Record<string, string> = {
  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
  ".webp": "image/webp",
  ".png": "image/png",
  ".json": "application/json",
  ".geojson": "application/geo+json",
};

export function contentType(path: string): string {
  const dot = path.lastIndexOf(".");
  return TYPES[path.slice(dot).toLowerCase()] ?? "application/octet-stream";
}

/** Keep log lines a person can read: progress and problems, not ACE-Step's prompt dump, DEBUG/INFO chatter or bars. */
export function readableLog(line: string): boolean {
  const text = line.trim();
  if (!text || /\|\s+(DEBUG|INFO)\s+\|/.test(text) || /\d+%\||it\/s\]/.test(text)) return false;
  return /→|ACE-Step:|WARNING|Error|Traceback|Downloaded|events|manifest\.json$/.test(text);
}
