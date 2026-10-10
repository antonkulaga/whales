import { expect, test } from "bun:test";
import { silverSTL, smoothSilverMesh } from "../src/lib/silver-stl.ts";
import type { SilverMesh } from "../src/lib/silver-stl.ts";

const octahedron: SilverMesh = {
  positions: new Float32Array([1.1, 0, 0, -1, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 1, 0, 0, -1]),
  indices: new Uint32Array([0, 2, 4, 2, 1, 4, 1, 3, 4, 3, 0, 4, 2, 0, 5, 1, 2, 5, 3, 1, 5, 0, 3, 5]),
};

test("export smoothing moves actual vertices gently and leaves the live mesh untouched", () => {
  const before = octahedron.positions.slice();
  const smooth = smoothSilverMesh(octahedron);
  expect(octahedron.positions).toEqual(before);
  expect(smooth.indices).toEqual(octahedron.indices);
  expect(smooth.positions).not.toEqual(before);
  for (let i = 0; i < before.length; i += 3) {
    const move = Math.hypot(...[0, 1, 2].map(c => smooth.positions[i + c]! - before[i + c]!));
    expect(move).toBeLessThanOrEqual(0.020001);
  }
});

test("STL triangle-soup seams smooth together as a continuous surface", () => {
  const split: SilverMesh = {
    positions: new Float32Array(Array.from(octahedron.indices).flatMap(i => Array.from(octahedron.positions.subarray(i * 3, i * 3 + 3)))),
    indices: Uint32Array.from(octahedron.indices, (_, i) => i),
  };
  const smooth = smoothSilverMesh(split), indexed = smoothSilverMesh(octahedron);
  for (let i = 0; i < split.indices.length; i++) for (let c = 0; c < 3; c++) {
    expect(smooth.positions[3 * i + c]).toBe(indexed.positions[3 * octahedron.indices[i]! + c]);
  }
});

test("open edges and small separate openings are preserved", () => {
  const open: SilverMesh = {
    positions: new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0.001, 1, 0, 0.001, 0, 1, 0.001]),
    indices: new Uint32Array([0, 1, 2, 3, 4, 5]),
  };
  expect(smoothSilverMesh(open).positions).toEqual(open.positions);
});

test("binary STL includes all metal meshes, recomputed unit normals and millimetre coordinates", () => {
  const attachment: SilverMesh = { positions: new Float32Array([10, 0, 0, 11, 0, 0, 10, 1, 0]), indices: new Uint32Array([0, 1, 2]) };
  const output = silverSTL([octahedron, attachment]), view = new DataView(output);
  expect(view.getUint32(80, true)).toBe(9);
  expect(output.byteLength).toBe(84 + 9 * 50);
  for (let i = 0; i < 9; i++) {
    const offset = 84 + i * 50;
    expect(Math.hypot(...[0, 1, 2].map(c => view.getFloat32(offset + c * 4, true)))).toBeCloseTo(1, 6);
    expect(view.getUint16(offset + 48, true)).toBe(0);
  }
  expect(view.getFloat32(84 + 8 * 50 + 12, true)).toBe(10);
});

test("empty, invalid and degenerate surfaces cannot produce corrupt STL triangles", () => {
  expect(() => silverSTL([])).toThrow("no ring surface");
  expect(() => silverSTL([{ positions: new Float32Array([NaN, 0, 0]), indices: new Uint32Array([0, 0, 0]) }])).toThrow("invalid coordinates");
  expect(() => silverSTL([{ ...octahedron, indices: new Uint32Array([0, 1, 99]) }])).toThrow("invalid triangle");
  const output = silverSTL([{ ...octahedron, indices: new Uint32Array([...octahedron.indices, 0, 0, 0]) }]);
  expect(new DataView(output).getUint32(80, true)).toBe(8);
});
