/** Ring meshes use millimetres. STL stores those coordinates without a unit field. */
export type SilverMesh = { positions: Float32Array; indices: Uint32Array };
export type SilverSnapshot = { meshes: SilverMesh[]; name: string };

const MAX_MOVE_MM = 0.02;

/** Two gentle Taubin passes reduce faceting without ordinary Laplacian shrinkage.
 * Weld coincident STL vertices for adjacency, and keep open/nonmanifold edges fixed.
 * Work on a copy: exporting must never change the live shape.
 */
export function smoothSilverMesh(mesh: SilverMesh): SilverMesh {
  const { positions, indices } = mesh;
  if (positions.length % 3 || indices.length % 3) throw new Error("Incomplete ring mesh");
  const welded = new Map<string, number>(), remap = new Uint32Array(positions.length / 3);
  const original: number[] = [];
  for (let i = 0; i < remap.length; i++) {
    const p = [positions[3 * i]!, positions[3 * i + 1]!, positions[3 * i + 2]!];
    if (!p.every(Number.isFinite)) throw new Error("The ring contains invalid coordinates");
    // Exact welding preserves small deliberate openings instead of merging nearby surfaces.
    const key = p.join(",");
    let id = welded.get(key);
    if (id === undefined) { id = original.length / 3; welded.set(key, id); original.push(...p); }
    remap[i] = id;
  }
  const neighbours = Array.from({ length: original.length / 3 }, () => new Set<number>());
  const edges = new Map<number, number>();
  const count = neighbours.length;
  for (let f = 0; f < indices.length; f += 3) {
    const triangle = [indices[f]!, indices[f + 1]!, indices[f + 2]!].map(i => {
      if (i >= remap.length) throw new Error("The ring contains an invalid triangle");
      return remap[i]!;
    });
    if (new Set(triangle).size < 3) continue;
    for (let j = 0; j < 3; j++) {
      const a = triangle[j]!, b = triangle[(j + 1) % 3]!;
      neighbours[a]!.add(b); neighbours[b]!.add(a);
      const key = Math.min(a, b) * count + Math.max(a, b);
      edges.set(key, (edges.get(key) ?? 0) + 1);
    }
  }
  const pinned = new Set<number>();
  for (const [edge, uses] of edges) if (uses !== 2) {
    pinned.add(Math.floor(edge / count)); pinned.add(edge % count);
  }
  let current = new Float64Array(original);
  for (const factor of [0.2, -0.21, 0.2, -0.21]) {
    const next = current.slice();
    for (let i = 0; i < count; i++) {
      const adjacent = neighbours[i]!;
      if (pinned.has(i) || !adjacent.size) continue;
      for (let c = 0; c < 3; c++) {
        let sum = 0;
        for (const j of adjacent) sum += current[3 * j + c]!;
        next[3 * i + c] = current[3 * i + c]! + factor * (sum / adjacent.size - current[3 * i + c]!);
      }
      const distance = Math.hypot(...[0, 1, 2].map(c => next[3 * i + c]! - original[3 * i + c]!));
      if (distance > MAX_MOVE_MM) for (let c = 0; c < 3; c++) {
        next[3 * i + c] = original[3 * i + c]! + (next[3 * i + c]! - original[3 * i + c]!) * MAX_MOVE_MM / distance;
      }
    }
    current = next;
  }
  const result = positions.slice();
  for (let i = 0; i < remap.length; i++) for (let c = 0; c < 3; c++) result[3 * i + c] = current[3 * remap[i]! + c]!;
  return { positions: result, indices: indices.slice() };
}

/** Export only the metal surfaces, including generated Roots attachments. */
export function silverSTL(meshes: SilverMesh[]): ArrayBuffer {
  const smoothed = meshes.map(smoothSilverMesh);
  const triangles: number[][] = [];
  for (const { positions, indices } of smoothed) for (let f = 0; f < indices.length; f += 3) {
    const p = [indices[f]!, indices[f + 1]!, indices[f + 2]!].flatMap(i => Array.from(positions.subarray(3 * i, 3 * i + 3)));
    const ux = p[3]! - p[0]!, uy = p[4]! - p[1]!, uz = p[5]! - p[2]!;
    const vx = p[6]! - p[0]!, vy = p[7]! - p[1]!, vz = p[8]! - p[2]!;
    const normal = [uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx];
    const length = Math.hypot(...normal);
    if (length === 0) continue;
    triangles.push([...normal.map(n => n / length), ...p]);
  }
  if (!triangles.length) throw new Error("There is no ring surface to export");
  const output = new ArrayBuffer(84 + triangles.length * 50), view = new DataView(output);
  new Uint8Array(output, 0, 80).set(new TextEncoder().encode("Sound to silver | millimetres | gentle smoothing <= 0.02 mm"));
  view.setUint32(80, triangles.length, true);
  triangles.forEach((triangle, i) => triangle.forEach((value, j) => view.setFloat32(84 + i * 50 + j * 4, value, true)));
  return output;
}
