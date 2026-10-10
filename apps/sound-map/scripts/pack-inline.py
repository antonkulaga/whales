"""Pack the separately capped Inline STL and its measured end guides."""

import base64
import json
import math
import re
from pathlib import Path

import numpy as np

page = Path('apps/sound-map/demo/silver/index.html')
template = Path('experiments/silver_page.html').read_text(encoding='utf8')
html = page.read_text(encoding='utf8')
match = re.search(r'(<script id="silver-data" type="application/json">)(.*?)(</script>)', html, re.S)
if match is None:
    raise RuntimeError('Missing silver payload')
data = json.loads(match.group(2))
piece = next(p for p in data['pieces'] if p['id'] == 'inline')
mesh = np.load('data/baseinline-cut.npz')
vertices = mesh['v'].astype('<f4', copy=False)
indices = mesh['ix'].astype('<u4', copy=False)
piece.update(
    positions_f32=base64.b64encode(vertices.tobytes()).decode('ascii'),
    indices=base64.b64encode(indices.tobytes()).decode('ascii'),
    index_bits=32,
    vertex_count=len(vertices),
    triangle_count=len(indices) // 3,
    box=[vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()],
    opening_cut={'source': '+baseinline.stl', 'gap_mm': float(mesh['gap_mm'])},
)
piece.pop('positions', None)
frame = piece['frame']
center = np.array(frame['center'])
axis = np.array(frame['axis'])
e1 = np.array(frame['e1'])
e2 = np.array(frame['e2'])
ends = []
for point, inward in zip(vertices[-2:].copy(), (-1, 1)):
    # The tube's 0.5 mm radius ends inside each tip, never across the opening.
    point[2] += inward * .6
    # On the cup side, meet its visible upper shoulder instead of hiding the
    # last part of the spine under the middle of the cup.
    if inward > 0:
        point[1] += .9
        point[0] += .5
    relative = point - center
    radial_cos = float(relative @ e1)
    radial_sin = float(relative @ e2)
    ends.append({
        'radius': math.hypot(radial_cos, radial_sin),
        'height': float(relative @ axis),
        'angle': math.atan2(radial_sin, radial_cos) % (2 * math.pi),
    })
frame['inline_ends'] = ends
frame['theta_start'] = ends[0]['angle']
frame['span'] = (ends[1]['angle'] - ends[0]['angle']) % (2 * math.pi)
guide = json.loads(Path('resources/inline-spine-guide.json').read_text(encoding='utf8'))
frame['inline_guide'] = guide
# This short, separate attachment closes only the free wire end. The measured
# centerline above remains untouched; bury the attachment root in the base.
start_angle = frame['theta_start'] + frame['span'] * guide['u_start']
wire_start = (center + guide['radius'][0] * math.cos(start_angle) * e1
              + guide['radius'][0] * math.sin(start_angle) * e2
              + guide['height'][0] * axis)
distances = np.linalg.norm(vertices - wire_start, axis=1)
surface = vertices[int(np.argmin(distances))]
distance = float(np.min(distances))
if not 2 < distance < 3.5:
    raise RuntimeError(f'Unexpected free-wire distance to base: {distance:.3f} mm')
anchor = surface + .35 * (surface - wire_start) / distance
relative = anchor - center
frame['inline_anchor_stage'] = [float(relative @ e1), float(relative @ axis), -float(relative @ e2)]
frame['inline_anchor_gap_mm'] = distance
html = html[:match.start()] + match.group(1) + json.dumps(data, separators=(',', ':')) + match.group(3) + html[match.end():]
module = re.search(r'<script type="module">.*?</script>', template, re.S)
if module is None:
    raise RuntimeError('Missing silver module')
html, count = re.subn(r'<script type="module">.*?</script>', lambda _: module.group(0), html, count=1, flags=re.S)
if count != 1:
    raise RuntimeError('Missing demo module')
page.write_text(html, encoding='utf8')
print('Inline faces', len(indices) // 3, 'ends', ends, 'span', frame['span'])
