"""Moving versions of the silver study: five mechanisms animated on Livia's real rings.

Input: the bending study's viewer data (`art silver` first), Roots' print file for its cups, precedent images.
Schema: the measured pitch and level of each recording drive a schematic of each mechanism, with simple lags.
Output: data/output/silver/motion.html, one self-contained page.
"""

import base64
import io
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

from .data import ROOT, Layout
from .silver import DRIVE, cylindrical, load_config, load_piece, ring_frame

PAGE = Path(__file__).with_name("silver_motion_page.html")
AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def viewer_data(output: Path):
    """The data block embedded in the bending viewer, so both pages share one decimated mesh and one analysis."""
    page = (output / "index.html").read_text()
    start = page.index('<script id="silver-data" type="application/json">') + len('<script id="silver-data" type="application/json">')
    return json.loads(page[start:page.index("</script>", start)])


def cups(mesh, frame, spacing: float = 0.4, rays: int = 64):
    """Centres of open bowls: air points about half enclosed by metal and well clear of it.

    Narrow crevices are more enclosed and closer to metal; open air is less enclosed. The largest clearance
    in each of the three clusters is the cup centre; escaping rays give its opening direction.
    """
    import numpy as np
    from scipy.cluster.vq import kmeans2

    from .silver import circular_interp

    v = np.asarray(mesh.vertices)
    r, theta, _ = cylindrical(v, frame)
    outer = v[r - circular_interp(frame["bore"], theta) > 1.5]
    low, high = outer.min(axis=0) - 2, outer.max(axis=0) + 2
    grid = np.stack(np.meshgrid(*[np.arange(low[i], high[i], spacing) for i in range(3)], indexing="ij"), -1).reshape(-1, 3)
    grid = grid[~mesh.contains(grid)]
    i = np.arange(rays) + 0.5
    polar, turn = np.arccos(1 - 2 * i / rays), math.pi * (1 + 5 ** 0.5) * i
    directions = np.stack([np.cos(turn) * np.sin(polar), np.sin(turn) * np.sin(polar), np.cos(polar)], 1)
    origins, cast = np.repeat(grid, rays, 0), np.tile(directions, (len(grid), 1))
    locations, index, _ = mesh.ray.intersects_location(origins, cast, multiple_hits=False)
    distance = np.full(len(origins), np.inf)
    distance[index] = np.linalg.norm(locations - origins[index], axis=1)
    distance = distance.reshape(len(grid), rays)
    hit = distance < 6
    enclosure, clearance = hit.mean(1), np.where(np.isfinite(distance), distance, 99).min(1)
    candidates = np.flatnonzero((enclosure >= 0.45) & (enclosure <= 0.8) & (clearance > 1.5))
    _, labels = kmeans2(grid[candidates], 3, minit="++", seed=3)
    found = []
    for cluster in range(3):
        members = candidates[labels == cluster]
        if not len(members):
            continue
        best = members[np.argmax(clearance[members])]
        opening = directions[~hit[best]].mean(0)
        found.append({"center": grid[best].round(3).tolist(), "opening": (opening / np.linalg.norm(opening)).round(3).tolist(),
                      "radius": float(clearance[best].round(2))})
    return found


def precedent_images(layout: Layout, precedents: list[dict], size: int = 640):
    """Download each precedent's image once into data/input/silver-precedents; embed a small JPEG."""
    from PIL import Image

    directory = layout.input / "silver-precedents"
    directory.mkdir(parents=True, exist_ok=True)
    result = []
    for item in precedents:
        path = directory / f"{item['id']}{Path(item['image_url'].split('?')[0]).suffix or '.jpg'}"
        if not path.exists():
            with urlopen(Request(item["image_url"], headers={"User-Agent": AGENT}), timeout=30) as response:
                path.write_bytes(response.read())
        image = Image.open(path)
        image.seek(min(item.get("frame", 0), getattr(image, "n_frames", 1) - 1))
        image = image.convert("RGB")
        image.thumbnail((size, size))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80)
        result.append({**{k: v for k, v in item.items() if k != "image_url"},
                       "image": "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()})
    return result


def run(layout: Layout, drive: Path = DRIVE, output: Path | None = None, log=print):
    config = load_config()
    motion = config["motion"]
    output = output or layout.output / "silver"
    data = viewer_data(output)
    results = json.loads((output / "results.json").read_text())
    roots, _ = load_piece(drive / config["pieces"]["roots"]["source"])
    found = cups(roots, ring_frame(roots, config))
    log(f"Roots cups: {[(c['radius'], c['opening']) for c in found]}")
    pieces = {p["id"]: {k: p[k] for k in ("positions", "indices", "index_bits", "box", "frame", "title")} for p in data["pieces"]}
    page_data = {
        "mapping": data["config"]["mapping"],
        "pieces": pieces,
        "roots_cups": found,
        "sounds": [{k: s[k] for k in ("id", "title", "kind", "duration_s", "hop_s", "time_s", "pitch", "level", "slope", "audio")}
                   for s in data["sounds"]],
        "lift_limit": {sid: entry["variants"]["lift"]["safe_gain_mm"] for sid, entry in results["pieces"]["inline"]["sounds"].items()},
        "compare": motion["compare"],
        "precedents": precedent_images(layout, motion["precedents"]),
    }
    page = PAGE.read_text().replace("/*MOTION_DATA*/null", json.dumps(page_data, separators=(",", ":")))
    path = output / "motion.html"
    path.write_text(page)
    log(f"motion studies: {path} ({path.stat().st_size / 1e6:.1f} MB)")
    return path


if __name__ == "__main__":
    run(Layout(ROOT / "data"))
