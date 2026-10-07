// Where data lives. The local server answers /api/* and /files/*; a published static copy
// (window.PHRASE_ATLAS_STATIC) reads the same JSON and media files by relative path.

export const isStatic = Boolean((globalThis as { PHRASE_ATLAS_STATIC?: boolean }).PHRASE_ATLAS_STATIC);

export function fileUrl(path: string): string {
  return isStatic ? path : `/files/${path}`;
}

export function catalogUrl(): string {
  return isStatic ? "catalog.json" : "/api/catalog";
}

export function combosUrl(): string {
  return isStatic ? "combos.json" : "/api/combos";
}

export function comboUrl(id: string): string {
  return isStatic ? `combos/${id}/manifest.json` : `/api/combos/${id}`;
}
