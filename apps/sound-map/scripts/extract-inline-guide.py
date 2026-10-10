"""Measure the separate thin centerline in Livia's ++baseinline STL.

The supplied strip is only about 0.2 mm thick. It is a drawing reference,
not printable metal; the viewer generates its own 1 mm spine from this path.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh


SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('apps/sound-map/demo/silver/media/++baseinline.stl')
PAGE = Path('apps/sound-map/demo/silver/index.html')
OUTPUT = Path('resources/inline-spine-guide.json')


def components(mesh):
    """Connected vertex labels without an optional graph library."""
    parent = np.arange(len(mesh.vertices), dtype=np.int32)
    rank = np.zeros(len(parent), dtype=np.uint8)

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, c in mesh.faces:
        for x, y in ((a, b), (a, c)):
            x, y = root(x), root(y)
            if x == y:
                continue
            if rank[x] < rank[y]:
                x, y = y, x
            parent[y] = x
            if rank[x] == rank[y]:
                rank[x] += 1
    labels = np.fromiter((root(i) for i in range(len(parent))), dtype=np.int32)
    ids, counts = np.unique(labels, return_counts=True)
    return labels, sorted(zip(ids, counts), key=lambda p: p[1], reverse=True)


html = PAGE.read_text(encoding='utf8')
marker = '<script id="silver-data" type="application/json">'
payload = json.loads(html.split(marker, 1)[1].split('</script>', 1)[0])
frame = next(p for p in payload['pieces'] if p['id'] == 'inline')['frame']
mesh = trimesh.load_mesh(SOURCE, process=True)
labels, parts = components(mesh)
if len(parts) != 2 or parts[1][1] < 1000:
    raise RuntimeError('Expected the supplied ring and one separate thin guide')
guide_mask = labels == parts[1][0]
guide = mesh.vertices[guide_mask]
relative = guide - np.asarray(frame['center'])
e1, e2, axis = (np.asarray(frame[k]) for k in ('e1', 'e2', 'axis'))
theta = np.mod(np.arctan2(relative @ e2, relative @ e1), 2 * math.pi)
u = np.mod(theta - frame['theta_start'], 2 * math.pi) / frame['span']
if not (.08 < u.min() < .2 and .9 < u.max() < 1):
    raise RuntimeError('The thin guide is not aligned with the current Inline ring')

# Intersect the actual wire edges with each angular section. The midpoint of
# the section's inner and outer boundaries is its geometric centerline. There
# is no smoothing, radial shift, or hand-drawn replacement curve here.
edges = mesh.edges_unique
edges = edges[guide_mask[edges[:, 0]] & guide_mask[edges[:, 1]]]
all_relative = mesh.vertices - np.asarray(frame['center'])
X, Y, H = (all_relative @ vector for vector in (e1, e2, axis))
all_theta = np.mod(np.arctan2(Y, X), 2 * math.pi)
all_u = np.mod(all_theta - frame['theta_start'], 2 * math.pi) / frame['span']
low = np.minimum(all_u[edges[:, 0]], all_u[edges[:, 1]])
high = np.maximum(all_u[edges[:, 0]], all_u[edges[:, 1]])
N = 1024
# The two extreme sections graze rounded end caps rather than crossing the
# full strip. The adjacent sections are the first complete wire sections.
outer_start, outer_end = float(u.min()), float(u.max())
inset = (outer_end - outer_start) / N
positions = np.linspace(outer_start + inset, outer_end - inset, N + 1)
start, end = float(positions[0]), float(positions[-1])
raw_r, raw_h = [], []
for p in positions:
    crossing = edges[(low <= p + 1e-10) & (high >= p - 1e-10)]
    theta = frame['theta_start'] + frame['span'] * p
    cosine, sine = math.cos(theta), math.sin(theta)
    a, b = crossing[:, 0], crossing[:, 1]
    da, db = -sine * X[a] + cosine * Y[a], -sine * X[b] + cosine * Y[b]
    denominator = da - db
    valid = np.abs(denominator) > 1e-12
    a, b, da, denominator = a[valid], b[valid], da[valid], denominator[valid]
    fraction = da / denominator
    valid = (fraction >= -1e-8) & (fraction <= 1 + 1e-8)
    a, b, fraction = a[valid], b[valid], fraction[valid]
    radial = cosine * (X[a] + fraction * (X[b] - X[a])) + sine * (Y[a] + fraction * (Y[b] - Y[a]))
    axial = H[a] + fraction * (H[b] - H[a])
    if not len(radial):
        raise RuntimeError(f'No wire cross-section at u={p}')
    raw_r.append(float((radial.min() + radial.max()) / 2))
    raw_h.append(float((axial.min() + axial.max()) / 2))

OUTPUT.write_text(json.dumps({
    'source': SOURCE.name,
    'u_start': round(start, 8),
    'u_end': round(end, 8),
    'radius': [round(x, 5) for x in raw_r],
    'height': [round(x, 5) for x in raw_h],
}, separators=(',', ':')), encoding='utf8')
print('guide vertices', len(guide), 'u', round(start, 4), round(end, 4),
      'radius', round(min(raw_r), 3), round(max(raw_r), 3), 'saved', OUTPUT)
