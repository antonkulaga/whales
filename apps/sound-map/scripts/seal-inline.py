"""Seal the two open tips in Livia's cleaned Inline STL without bridging them."""

from pathlib import Path
import shutil

import numpy as np
import trimesh


SOURCE = Path('apps/sound-map/demo/silver/media/baseinline-cleaned.stl')
SOURCE_COPY = Path('data/input/silver/+baseinline.stl')
OUTPUT = Path('data/output/silver/baseinline-separated.stl')
DEMO = Path('apps/sound-map/demo/silver/media/baseinline-separated.stl')


def signed_area(points):
    return .5 * np.sum(points[:, 0] * np.roll(points[:, 1], -1) - np.roll(points[:, 0], -1) * points[:, 1])


def cap_fan(loop, vertices, inward, center_index):
    """Close one contour with a shallow inset center and opposite edge winding."""
    loop = loop[::-1]
    xy = vertices[loop, :2]
    next_xy = np.roll(xy, -1, axis=0)
    crosses = xy[:, 0] * next_xy[:, 1] - next_xy[:, 0] * xy[:, 1]
    area = signed_area(xy)
    center_xy = np.sum((xy + next_xy) * crosses[:, None], axis=0) / (6 * area)
    def fan_area_at(point):
        return .5 * np.sum(np.abs((xy[:, 0] - point[0]) * (next_xy[:, 1] - point[1])
                                    - (xy[:, 1] - point[1]) * (next_xy[:, 0] - point[0])))
    fan_area = fan_area_at(center_xy)
    if fan_area > abs(area) * 1.0001:
        for x in np.linspace(xy[:, 0].min(), xy[:, 0].max(), 41):
            for y in np.linspace(xy[:, 1].min(), xy[:, 1].max(), 41):
                candidate = np.array([x, y])
                score = fan_area_at(candidate)
                if score < fan_area:
                    center_xy, fan_area = candidate, score
    print('cap projected fan area ratio', fan_area / abs(area))
    if fan_area > abs(area) * 1.01:
        raise RuntimeError('The end is too concave for a safe radial cap')
    center = [*center_xy, float(np.median(vertices[loop, 2]) + inward * .08)]
    triangles = [[int(loop[j]), int(loop[(j + 1) % len(loop)]), center_index] for j in range(len(loop))]
    return center, triangles


mesh = trimesh.load_mesh(SOURCE, process=True)
if mesh.is_watertight or not mesh.is_winding_consistent:
    raise RuntimeError('The supplied mesh has an unexpected boundary or face winding')

faces = mesh.faces
directed = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
keys = np.sort(directed, axis=1)
_, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
if np.any(counts > 2):
    raise RuntimeError('The supplied mesh has non-manifold edges')
boundary = directed[counts[inverse] == 1]
next_by_vertex = {}
for a, b in boundary:
    if int(a) in next_by_vertex:
        raise RuntimeError('A boundary forks instead of forming an end loop')
    next_by_vertex[int(a)] = int(b)

loops = []
while next_by_vertex:
    first = next(iter(next_by_vertex))
    loop = []
    node = first
    while node in next_by_vertex:
        loop.append(node)
        node = next_by_vertex.pop(node)
    if node != first:
        raise RuntimeError('An end boundary does not close')
    loops.append(np.asarray(loop, dtype=int))
if len(loops) != 2:
    raise RuntimeError(f'Expected two separate open ends, found {len(loops)}')

loops.sort(key=lambda loop: np.median(mesh.vertices[loop, 2]))
upper, lower = (mesh.vertices[loop] for loop in (loops[1], loops[0]))
gap = np.linalg.norm(upper[:, None, :] - lower[None, :, :], axis=2).min()
if gap <= 0:
    raise RuntimeError('The two open ends touch')

# Reverse each oriented boundary for its cap. All cap vertices belong to that
# end alone; no triangle can span the gap or alter the supplied outer surface.
centers, caps = [], []
for loop, inward in zip(loops, (-1, 1)):
    center, triangles = cap_fan(loop, mesh.vertices, inward, len(mesh.vertices) + len(centers))
    centers.append(center)
    caps.extend(triangles)
closed = trimesh.Trimesh(vertices=np.vstack((mesh.vertices, centers)), faces=np.vstack((faces, caps)), process=False)
if not closed.is_watertight or not closed.is_winding_consistent or closed.volume <= 0:
    raise RuntimeError(f'End caps failed: watertight={closed.is_watertight}, winding={closed.is_winding_consistent}, '
                       f'volume={closed.volume}, cap faces={len(caps)}')

SOURCE_COPY.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(SOURCE, SOURCE_COPY)
closed.export(OUTPUT)
closed.export(DEMO)
np.savez('data/baseinline-cut.npz', v=closed.vertices.astype('<f4'), ix=closed.faces.astype('<u4').ravel(),
         loop_lower=loops[0], loop_upper=loops[1], gap_mm=gap)
print('faces', len(closed.faces), 'watertight', closed.is_watertight, 'winding', closed.is_winding_consistent,
      'boundary_gap_mm', round(float(gap), 4), 'end_loop_sizes', [len(loop) for loop in loops])
