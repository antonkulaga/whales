"""Sound bends a real cast-silver ring without tearing it.

Input: one of Livia's stoneless ring STLs (Inline, Roots) and a recording.
Schema: time → angle along the metal; pitch → lift along the finger; level → outward swell;
pitch slope → lean. Every point keeps its angle, moves only outward from the finger and may slide
along it, so the map is one-to-one by construction: no tearing, no self-crossing, finger hole kept.
Output: casting checks (wall, gap, interpenetration, bore, mass), the largest gain that still casts,
full-resolution deformed STLs and one self-contained live 3D viewer.
"""

from datetime import datetime, timezone
import base64
import hashlib
import json
import math
from pathlib import Path

from .data import ROOT, Layout, write_json

CONFIG = ROOT / "resources" / "sound-silver.json"
PAGE = Path(__file__).with_name("silver_page.html")
DRIVE = Path.home() / "Downloads" / "drive-folder"
GESTURES = ("lift", "swell", "lean")


def load_config(path: Path = CONFIG):
    return json.loads(path.read_text())


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- piece and ring frame

def load_piece(path: Path):
    """Welded mesh of the main body: print debris (shells under 1% of faces) removed."""
    import numpy as np
    import trimesh

    mesh = trimesh.load(path, force="mesh")
    mesh.merge_vertices(digits_vertex=4)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    shells = mesh.split(only_watertight=False)
    kept = [shell for shell in shells if len(shell.faces) >= 0.01 * len(mesh.faces)]
    body = trimesh.util.concatenate(kept) if len(kept) > 1 else kept[0]
    if body.volume < 0:
        body.invert()
    return body, {"source_triangles": int(len(mesh.faces)), "shells_removed": len(shells) - len(kept),
                  "triangles": int(len(body.faces)), "vertices": int(len(body.vertices)),
                  "watertight": bool(body.is_watertight), "volume_mm3": float(body.volume),
                  "extent_mm": np.round(body.extents, 2).tolist()}


def cylindrical(points, frame):
    import numpy as np

    relative = points - frame["center"]
    h = relative @ frame["axis"]
    x, y = relative @ frame["e1"], relative @ frame["e2"]
    return np.hypot(x, y), np.arctan2(y, x) % (2 * math.pi), h


def circular_interp(values, theta):
    """Linear interpolation of a periodic profile sampled at bins (i + 0.5) / n of a turn."""
    import numpy as np

    n = len(values)
    position = theta / (2 * math.pi) * n - 0.5
    low = np.floor(position).astype(int)
    fraction = position - low
    return values[low % n] * (1 - fraction) + values[(low + 1) % n] * fraction


def circular_smooth(values, sigma_bins: float):
    import numpy as np

    n = len(values)
    offsets = np.arange(n)
    distance = np.minimum(offsets, n - offsets)
    kernel = np.exp(-0.5 * (distance / sigma_bins) ** 2)
    kernel /= kernel.sum()
    return np.real(np.fft.ifft(np.fft.fft(values) * np.fft.fft(kernel)))


def bore_profile(points, frame, bins: int):
    """Innermost radius per angular bin; empty bins (the opening) are NaN."""
    import numpy as np

    r, theta, _ = cylindrical(points, frame)
    index = np.minimum((theta / (2 * math.pi) * bins).astype(int), bins - 1)
    inner = np.full(bins, np.inf)
    np.minimum.at(inner, index, r)
    inner[~np.isfinite(inner)] = np.nan
    return inner


def ring_frame(mesh, config: dict):
    """Finger axis, centre, a smooth bore radius per angle and the arc the metal covers."""
    import numpy as np

    m = config["mapping"]
    moments = mesh.principal_inertia_components
    axis = np.array(mesh.principal_inertia_vectors[int(np.argmax(moments))], dtype=float)
    axis /= np.linalg.norm(axis)
    if axis[np.argmax(np.abs(axis))] < 0:
        axis = -axis
    helper = np.eye(3)[int(np.argmin(np.abs(axis)))]
    e1 = np.cross(axis, helper)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    vertices = np.asarray(mesh.vertices)
    center = np.array(mesh.center_mass, dtype=float)
    frame = {"axis": axis, "e1": e1, "e2": e2, "center": center}
    for _ in range(4):  # fit a circle to the innermost points of 72 sectors
        inner = bore_profile(vertices, frame, 72)
        r, theta, _ = cylindrical(vertices, frame)
        index = np.minimum((theta / (2 * math.pi) * 72).astype(int), 71)
        points = []
        for sector in np.flatnonzero(np.isfinite(inner)):
            members = np.flatnonzero(index == sector)
            best = members[np.argmin(r[members])]
            relative = vertices[best] - frame["center"]
            points.append([relative @ e1, relative @ e2])
        points = np.asarray(points)
        design = np.column_stack([2 * points, np.ones(len(points))])
        solution = np.linalg.lstsq(design, (points ** 2).sum(axis=1), rcond=None)[0]
        frame["center"] = frame["center"] + solution[0] * e1 + solution[1] * e2
    raw = bore_profile(vertices, frame, m["bore_bins"])
    filled = raw.copy()
    known = np.flatnonzero(np.isfinite(raw))
    unknown = np.flatnonzero(~np.isfinite(raw))
    if len(unknown):
        filled[unknown] = np.interp(unknown, known, raw[known], period=len(raw))
    # Smooth upper envelope: never below the innermost metal, so the finger-hole surface never moves outward.
    from scipy.ndimage import maximum_filter1d

    sigma_bins = m["bore_smooth_degrees"] / 360 * m["bore_bins"]
    bore = circular_smooth(maximum_filter1d(filled, 2 * math.ceil(2.5 * sigma_bins) + 1, mode="wrap"), sigma_bins)
    bore = np.maximum(bore, filled)
    # The opening: the longest circular run of empty bins.
    empty = ~np.isfinite(raw)
    best_start, best_length = 0, 0
    if empty.any() and not empty.all():
        doubled = np.concatenate([empty, empty])
        run = 0
        for i, value in enumerate(doubled):
            run = run + 1 if value else 0
            if run > best_length and run <= len(empty):
                best_length, best_start = run, i - run + 1
    bin_angle = 2 * math.pi / m["bore_bins"]
    if best_length * bin_angle >= math.radians(m["opening_min_degrees"]):
        theta_start = ((best_start + best_length) % m["bore_bins"]) * bin_angle
        span = 2 * math.pi - best_length * bin_angle
    else:
        theta_start, span = 0.0, 2 * math.pi
    r, _, h = cylindrical(vertices, frame)
    frame["center"] = frame["center"] + float(np.median(h)) * axis
    r_ref = float(np.median(r))
    frame.update({"bore": bore, "bore_raw": raw, "theta_start": float(theta_start), "span": float(span),
                  "r_ref": r_ref, "sigma": m["sigma_mm"] / r_ref})
    return frame


def frame_summary(frame: dict):
    import numpy as np

    raw = frame["bore_raw"]
    return {"center": np.round(frame["center"], 4).tolist(), "axis": np.round(frame["axis"], 5).tolist(),
            "bore_radius_mm": [float(np.nanmin(raw)), float(np.nanmedian(raw)), float(np.nanmax(raw))],
            "bore_diameter_median_mm": float(2 * np.nanmedian(raw)),
            "opening_degrees": float(360 - math.degrees(frame["span"])), "theta_start_degrees": math.degrees(frame["theta_start"]),
            "metal_arc_mm": float(frame["span"] * frame["r_ref"]), "r_ref_mm": frame["r_ref"],
            "sigma_degrees": math.degrees(frame["sigma"])}


# ---------------------------------------------------------------- sound features

def features(path: Path, config: dict):
    """Per-frame pitch (octaves from the median), level above the floor and pitch slope, each in [-1, 1] or [0, 1]."""
    import numpy as np
    from scipy.ndimage import uniform_filter1d
    from scipy.signal import stft

    from .brush import load_config as brush_config, measure, read_audio

    f = config["features"]
    analysis = brush_config()
    a = analysis["analysis"]
    waveform, rate = read_audio(path)
    measured = measure(waveform, rate, analysis)
    times = np.asarray(measured["frames"]["time_s"])
    frequencies, _, spectrum = stft(waveform, rate, window="hann", nperseg=a["n_fft"], noverlap=a["n_fft"] - a["hop"],
                                    boundary=None, padded=False)
    band = (frequencies >= a["band_hz"][0]) & (frequencies <= min(a["band_hz"][1], rate / 2 - 1))
    level_db = 10 * np.log10(np.maximum((np.abs(spectrum[band]) ** 2).sum(axis=0), 1e-30))
    hop_s = a["hop"] / rate
    width = max(1, round(f["smooth_s"] / hop_s))
    floor = float(np.percentile(level_db, f["level_floor_percentile"]) + f["level_headroom_db"])
    peak = float(level_db.max())
    level = uniform_filter1d(np.clip((level_db - floor) / max(peak - floor, 1e-6), 0, 1), width)
    tonal = [s for s in measured["segments"] if s["kind"] == "tonal"]
    hz = np.full(len(times), np.nan)
    for segment in tonal:
        begin, end = segment["frames"]
        hz[begin:end] = segment["hz"]
    pitch, slope = np.zeros(len(times)), np.zeros(len(times))
    if tonal:
        reference = float(np.nanmedian(np.log2(hz)))
        for segment in tonal:
            begin, end = segment["frames"]
            octaves = np.log2(np.asarray(segment["hz"]))
            pitch[begin:end] = np.clip((octaves - reference) / f["pitch_full_scale_octaves"], -1, 1)
            if end - begin >= 3:
                rate_of_change = uniform_filter1d(np.gradient(octaves, hop_s), min(width, end - begin))
                slope[begin:end] = np.clip(rate_of_change / f["slope_full_scale_octaves_per_s"], -1, 1)
    clicks = sum(len(s["time_s"]) for s in measured["segments"] if s["kind"] == "clicks")
    return {"path": str(path), "sha256": sha256(path), "sample_rate": rate, "duration_s": len(waveform) / rate,
            "hop_s": hop_s, "time_s": times.tolist(), "pitch": pitch.tolist(), "level": level.tolist(), "slope": slope.tolist(),
            "hz": [None if not np.isfinite(v) else float(v) for v in hz], "level_db": level_db.tolist(),
            "summary": {"tonal_segments": len(tonal), "tonal_fraction": float(np.isfinite(hz).mean()), "clicks": int(clicks),
                        "median_hz": float(2 ** np.nanmedian(np.log2(hz))) if tonal else None,
                        "level_floor_db": floor, "level_peak_db": peak}}


# ---------------------------------------------------------------- sound → angular profiles → deformation

def profiles(feature: dict, frame: dict, config: dict, until_s: float | None = None):
    """Lift, swell and lean around the ring: each frame's value spread by a Gaussian at its angle.

    Normalised so a value held over a long arc reaches that value; time runs along the metal arc.
    """
    import numpy as np

    bins = config["mapping"]["profile_bins"]
    times = np.asarray(feature["time_s"])
    keep = times <= (until_s if until_s is not None else math.inf)
    angles = frame["theta_start"] + frame["span"] * times[keep] / feature["duration_s"]
    step = frame["span"] * feature["hop_s"] / feature["duration_s"]
    centres = (np.arange(bins) + 0.5) / bins * 2 * math.pi
    difference = (centres[:, None] - angles[None, :] + math.pi) % (2 * math.pi) - math.pi
    sigma = frame["sigma"]
    weight = np.exp(-0.5 * (difference / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi)) * step
    return {"lift": weight @ np.asarray(feature["pitch"])[keep], "swell": weight @ np.asarray(feature["level"])[keep],
            "lean": weight @ np.asarray(feature["slope"])[keep]}


def deform(points, frame: dict, profile: dict, gain: float, config: dict, gestures=GESTURES):
    """r' = r + g·swell(θ)·w(r), h' = h + g·lift(θ) + g·lean(θ)·(r − bore)/ref; θ unchanged.

    swell ≥ 0 and w is non-decreasing in r, so r' is strictly increasing in r and h' in h: one-to-one.
    w = 0 at the bore, so the finger hole keeps its radius.
    """
    import numpy as np

    m = config["mapping"]
    r, theta, h = cylindrical(points, frame)
    bore = circular_interp(frame["bore"], theta)
    x = np.clip((r - bore) / m["lock_ramp_mm"], 0, 1)
    w = x * x * (3 - 2 * x)
    r_new = r.copy()
    h_new = h.copy()
    if "swell" in gestures:
        r_new = r + gain * m["swell"] * np.maximum(circular_interp(profile["swell"], theta), 0) * w
    if "lift" in gestures:
        h_new = h_new + gain * m["lift"] * circular_interp(profile["lift"], theta)
    if "lean" in gestures:
        h_new = h_new + gain * m["lean"] * circular_interp(profile["lean"], theta) * (r - bore) / m["lean_reference_mm"]
    radial = points - frame["center"] - np.outer(h, frame["axis"])
    unit = radial / np.maximum(r, 1e-9)[:, None]
    return frame["center"] + unit * r_new[:, None] + np.outer(h_new, frame["axis"])


def naive(points, normals, frame: dict, profile: dict, gain: float, config: dict):
    """The usual audio-reactive move, for contrast: push each point along its surface normal."""
    import numpy as np

    m = config["mapping"]
    _, theta, _ = cylindrical(points, frame)
    amount = gain * (m["lift"] * circular_interp(profile["lift"], theta) + m["swell"] * circular_interp(profile["swell"], theta))
    return points + normals * amount[:, None]


# ---------------------------------------------------------------- casting checks

def rays(mesh, origins, directions):
    """Distance to the first hit along each ray; inf when the ray escapes."""
    import numpy as np

    locations, index, _ = mesh.ray.intersects_location(origins, directions, multiple_hits=False)
    distance = np.full(len(origins), np.inf)
    distance[index] = np.linalg.norm(locations - origins[index], axis=1)
    return distance


def walls_and_gaps(mesh):
    """Wall thickness along the inward normal and clearance along the outward normal, per vertex."""
    import numpy as np

    v, n = np.asarray(mesh.vertices), np.asarray(mesh.vertex_normals)
    return rays(mesh, v - n * 1e-4, -n), rays(mesh, v + n * 1e-4, n)


def vertex_areas(mesh):
    import numpy as np

    areas = np.zeros(len(mesh.vertices))
    np.add.at(areas, np.asarray(mesh.faces).ravel(), np.repeat(mesh.area_faces / 3, 3))
    return areas


def interpenetrations(mesh, measurable, offset: float = 0.02):
    """Vertices whose point just outside the surface lies inside the solid: the surface passed through itself.

    Only measurable vertices count; in a concave crease the offset point legitimately lands in the neighbouring wall.
    """
    import numpy as np

    v, n = np.asarray(mesh.vertices)[measurable], np.asarray(mesh.vertex_normals)[measurable]
    return int(np.count_nonzero(mesh.contains(v + n * offset)))


def baseline(mesh, frame: dict, config: dict):
    """Original walls and gaps; tips and creases where a single ray cannot measure either are set aside."""
    import numpy as np

    c = config["casting"]
    wall, gap = walls_and_gaps(mesh)
    measurable = (wall >= c["measurable_wall_mm"]) & (gap >= c["measurable_gap_mm"])
    return {"wall": wall, "gap": gap, "areas": vertex_areas(mesh), "measurable": measurable,
            "inside": interpenetrations(mesh, measurable),
            "bore": bore_profile(np.asarray(mesh.vertices), frame, config["mapping"]["bore_bins"]),
            "edges": np.asarray(mesh.edges_unique_length), "volume": float(mesh.volume)}


def check(mesh, vertices, frame: dict, base: dict, config: dict):
    """Casting verdict for deformed vertex positions on the original triangles."""
    import numpy as np
    import trimesh

    c = config["casting"]
    after = trimesh.Trimesh(vertices, mesh.faces, process=False)
    wall, gap = walls_and_gaps(after)
    tolerance = c["relative_tolerance"]
    measurable = base["measurable"]
    thin = measurable & (wall < c["min_wall_mm"]) & (wall < tolerance * base["wall"])
    close = measurable & (gap < c["min_gap_mm"]) & (gap < tolerance * base["gap"])
    total = base["areas"].sum()
    inside = interpenetrations(after, measurable)
    bore = bore_profile(vertices, frame, config["mapping"]["bore_bins"])
    metal = np.isfinite(bore) & np.isfinite(base["bore"])
    ratio = np.asarray(after.edges_unique_length) / np.maximum(base["edges"], 1e-12)
    moved = np.linalg.norm(vertices - np.asarray(mesh.vertices), axis=1)
    finite_wall, finite_gap = wall[np.isfinite(wall)], gap[np.isfinite(gap)]
    result = {
        "thin_area_fraction": float(base["areas"][thin].sum() / total),
        "close_area_fraction": float(base["areas"][close].sum() / total),
        "thin_vertices": int(thin.sum()), "close_vertices": int(close.sum()),
        "min_wall_mm": float(finite_wall.min()), "wall_p1_mm": float(np.percentile(finite_wall, 1)),
        "min_gap_mm": float(finite_gap.min()), "gap_p1_mm": float(np.percentile(finite_gap, 1)),
        "interpenetrating_vertices": inside, "interpenetrating_vertices_before": base["inside"],
        "bore_change_mm": float(np.abs(bore[metal] - base["bore"][metal]).max()),
        "mass_g": float(after.volume / 1000 * c["density_g_cm3"]),
        "mass_change_percent": float(100 * (after.volume / base["volume"] - 1)),
        "edge_stretch_p0_1": float(np.percentile(ratio, 0.1)), "edge_stretch_p99_9": float(np.percentile(ratio, 99.9)),
        "displacement_max_mm": float(moved.max()), "displacement_p95_mm": float(np.percentile(moved, 95)),
    }
    result["casts"] = bool(result["thin_area_fraction"] + result["close_area_fraction"] <= c["max_violating_area_fraction"]
                           and inside <= base["inside"])
    return result, thin | close


def safe_gain(mesh, frame: dict, profile: dict, base: dict, config: dict):
    """Largest gain (mm at full scale) whose deformation still passes every casting check, by bisection."""
    s = config["search"]
    vertices = mesh.vertices
    low, high = 0.0, s["max_gain_mm"]
    top, _ = check(mesh, deform(vertices, frame, profile, high, config), frame, base, config)
    if top["casts"]:
        return high, True
    for _ in range(s["steps"]):
        middle = (low + high) / 2
        result, _ = check(mesh, deform(vertices, frame, profile, middle, config), frame, base, config)
        low, high = (middle, high) if result["casts"] else (low, middle)
    return low, False


# ---------------------------------------------------------------- viewer data

def decimate(mesh, triangles: int):
    import fast_simplification
    import numpy as np
    import trimesh

    if len(mesh.faces) <= triangles:
        return mesh.copy()
    points, faces = fast_simplification.simplify(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces),
                                                 target_reduction=1 - triangles / len(mesh.faces))
    small = trimesh.Trimesh(points, faces, process=True)
    small.update_faces(small.nondegenerate_faces())
    small.remove_unreferenced_vertices()
    return small


def opposite_points(full, small):
    """For each viewer vertex, the points straight across its wall and its gap on the full-resolution surface.

    Deforming both ends of each pair with the same map gives a live wall and gap estimate in the browser.
    """
    import numpy as np

    v, n = np.asarray(small.vertices), np.asarray(small.vertex_normals)
    result = {}
    for name, sign in (("inner", -1), ("outer", 1)):
        origins = v + sign * n * 1e-3
        locations, index, _ = full.ray.intersects_location(origins, sign * n, multiple_hits=False)
        points = np.full(v.shape, np.nan)
        points[index] = locations
        result[name] = points
    return result


def pack(array, dtype):
    import numpy as np

    return base64.b64encode(np.ascontiguousarray(array, dtype=dtype).tobytes()).decode()


def quantized(points, low, high):
    """uint16 per coordinate inside the piece's padded box; 65535 marks a missing point."""
    import numpy as np

    scaled = np.round((points - low) / (high - low) * 65534)
    scaled = np.where(np.isfinite(scaled), np.clip(scaled, 0, 65534), 65535)
    return pack(scaled, np.uint16)


def viewer_piece(full, small, frame: dict, info: dict, pairs: dict):
    import numpy as np

    pad = 2.0
    low = np.minimum(np.asarray(small.vertices).min(axis=0), np.nanmin(pairs["inner"], axis=0)) - pad
    high = np.maximum(np.asarray(small.vertices).max(axis=0), np.nanmax(pairs["inner"], axis=0)) + pad
    finite_outer = pairs["outer"][np.isfinite(pairs["outer"]).all(axis=1)]
    low = np.minimum(low, finite_outer.min(axis=0) - pad)
    high = np.maximum(high, finite_outer.max(axis=0) + pad)
    indices = np.asarray(small.faces)
    return {
        **info,
        "box": [low.tolist(), high.tolist()],
        "vertex_count": int(len(small.vertices)), "triangle_count": int(len(indices)),
        "positions": quantized(np.asarray(small.vertices), low, high),
        "indices": pack(indices, np.uint16 if len(small.vertices) < 65535 else np.uint32),
        "index_bits": 16 if len(small.vertices) < 65535 else 32,
        "inner": quantized(pairs["inner"], low, high), "outer": quantized(pairs["outer"], low, high),
        "frame": {"center": frame["center"].tolist(), "axis": frame["axis"].tolist(), "e1": frame["e1"].tolist(),
                  "e2": frame["e2"].tolist(), "bore": np.asarray(frame["bore"]).tolist(), "theta_start": frame["theta_start"],
                  "span": frame["span"], "r_ref": frame["r_ref"], "sigma": frame["sigma"]},
    }


def estimate(small, pairs: dict, vertices, deformed_pairs: dict):
    """The browser's live wall and gap: distance between a vertex and its deformed opposite point."""
    import numpy as np

    return (np.linalg.norm(vertices - deformed_pairs["inner"], axis=1),
            np.linalg.norm(vertices - deformed_pairs["outer"], axis=1))


def downsample_wav(path: Path, target_rate: int = 44100):
    import io

    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly

    samples, rate = sf.read(path, dtype="float32", always_2d=True)
    samples = samples.mean(axis=1)
    if rate > target_rate:
        divisor = math.gcd(rate, target_rate)
        samples, rate = resample_poly(samples, target_rate // divisor, rate // divisor).astype(np.float32), target_rate
    samples = samples / max(float(np.abs(samples).max()), 1e-9) * 0.9
    buffer = io.BytesIO()
    sf.write(buffer, samples, rate, format="WAV", subtype="PCM_16")
    return "data:audio/wav;base64," + base64.b64encode(buffer.getvalue()).decode()


def photo_uri(path: Path, size: int = 720):
    import io

    from PIL import Image

    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def write_stl(path: Path, mesh, vertices):
    import trimesh

    path.parent.mkdir(parents=True, exist_ok=True)
    trimesh.Trimesh(vertices, mesh.faces, process=False).export(path)


# ---------------------------------------------------------------- study

def run(layout: Layout, drive: Path = DRIVE, livia: Path = ROOT.parent / "livia", pieces=None, sounds=None,
        output: Path | None = None, stl: bool = True, log=print):
    """Every piece × sound: safe gain, checks at 0.5×, 1× and 2× safe, the naive contrast, STLs and the viewer."""
    import numpy as np

    config = load_config()
    output = output or layout.output / "silver"
    output.mkdir(parents=True, exist_ok=True)
    piece_ids = list(pieces or config["pieces"])
    sound_specs = [s for s in config["sounds"] if not sounds or s["id"] in sounds]
    started = datetime.now(timezone.utc).isoformat()
    sound_records, sound_features = [], {}
    for spec in sound_specs:
        path = ROOT / spec["path"]
        feature = features(path, config)
        sound_features[spec["id"]] = feature
        sound_records.append({**spec, "audio": downsample_wav(path), **{k: feature[k] for k in
                              ("sha256", "sample_rate", "duration_s", "hop_s", "time_s", "pitch", "level", "slope", "hz", "summary")}})
        log(f"sound {spec['id']}: {feature['duration_s']:.2f} s, tonal {feature['summary']['tonal_fraction']:.0%}, clicks {feature['summary']['clicks']}")
    viewer_pieces, results = [], {}
    for piece_id in piece_ids:
        spec = config["pieces"][piece_id]
        source = drive / spec["source"]
        mesh, info = load_piece(source)
        frame = ring_frame(mesh, config)
        base = baseline(mesh, frame, config)
        summary = frame_summary(frame)
        finite_wall, finite_gap = base["wall"][np.isfinite(base["wall"])], base["gap"][np.isfinite(base["gap"])]
        original = {"min_wall_mm": float(finite_wall.min()), "wall_p1_mm": float(np.percentile(finite_wall, 1)),
                    "min_gap_mm": float(finite_gap.min()), "gap_p1_mm": float(np.percentile(finite_gap, 1)),
                    "mass_g": base["volume"] / 1000 * config["casting"]["density_g_cm3"],
                    "interpenetrating_vertices": base["inside"]}
        log(f"{piece_id}: {info['triangles']} triangles, bore Ø {summary['bore_diameter_median_mm']:.1f} mm, "
            f"opening {summary['opening_degrees']:.0f}°, wall ≥ {original['min_wall_mm']:.2f} mm, gap ≥ {original['min_gap_mm']:.2f} mm")
        small = decimate(mesh, config["viewer"]["triangles"])
        pairs = opposite_points(mesh, small)
        piece_results = {"source": str(source), "source_sha256": sha256(source), "mesh": info, "frame": summary,
                         "original": original, "sounds": {}}
        for spec_sound in sound_specs:
            feature = sound_features[spec_sound["id"]]
            profile = profiles(feature, frame, config)
            gain, unlimited = safe_gain(mesh, frame, profile, base, config)
            entry = {"safe_gain_mm": gain, "limited_by_search_range": unlimited, "checks": {}}
            for label, factor in (("half", 0.5), ("safe", 1.0), ("double", 2.0)):
                moved = deform(mesh.vertices, frame, profile, gain * factor, config)
                entry["checks"][label], _ = check(mesh, moved, frame, base, config)
                if label == "safe" and stl:
                    write_stl(output / "stl" / f"{piece_id}-{spec_sound['id']}-safe.stl", mesh, moved)
            pushed = naive(np.asarray(mesh.vertices), np.asarray(mesh.vertex_normals), frame, profile, gain, config)
            entry["naive_at_safe"], _ = check(mesh, pushed, frame, base, config)
            # How well the browser's live estimate (deformed opposite points) matches re-cast rays at the safe gain.
            moved_small = deform(np.asarray(small.vertices), frame, profile, gain, config)
            deformed_pairs = {k: deform(np.nan_to_num(v), frame, profile, gain, config) for k, v in pairs.items()}
            wall_live, gap_live = estimate(small, pairs, moved_small, deformed_pairs)
            import trimesh

            truth_wall, truth_gap = walls_and_gaps(trimesh.Trimesh(moved_small, small.faces, process=False))
            valid = np.isfinite(pairs["inner"]).all(axis=1) & np.isfinite(truth_wall)
            entry["live_wall_error_mm"] = {"median": float(np.median(np.abs(wall_live[valid] - truth_wall[valid]))),
                                           "p95": float(np.percentile(np.abs(wall_live[valid] - truth_wall[valid]), 95))}
            entry["reference_vertices"] = moved_small[:: max(1, len(moved_small) // 64)][:64].round(5).tolist()
            piece_results["sounds"][spec_sound["id"]] = entry
            safe = entry["checks"]["safe"]
            log(f"  {spec_sound['id']:5s} safe gain {gain:.2f} mm{' (top of range)' if unlimited else ''}; "
                f"max move {safe['displacement_max_mm']:.2f} mm; wall ≥ {safe['min_wall_mm']:.2f}; gap ≥ {safe['min_gap_mm']:.2f}; "
                f"bore Δ {safe['bore_change_mm']:.3f}; mass {safe['mass_change_percent']:+.1f}%; "
                f"2×: casts={entry['checks']['double']['casts']}; naive: casts={entry['naive_at_safe']['casts']} "
                f"(thin {entry['naive_at_safe']['thin_area_fraction']:.1%}, through-itself {entry['naive_at_safe']['interpenetrating_vertices']})")
        results[piece_id] = piece_results
        photo = livia / "assets" / "pieces" / spec["photo"]
        viewer_pieces.append(viewer_piece(mesh, small, frame, {
            "id": piece_id, "title": spec["title"], "year": spec["year"], "materials": spec["materials"], "note": spec["note"],
            "photo": photo_uri(photo) if photo.exists() else None, "original": original, "summary": summary,
            "results": piece_results["sounds"]}, pairs))
    record = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "started_at_utc": started, "config": config,
              "sounds": [{k: v for k, v in s.items() if k not in ("audio", "time_s", "pitch", "level", "slope", "hz")} for s in sound_records],
              "pieces": results}
    write_json(output / "results.json", record)
    data = {"config": {k: config[k] for k in ("interpretation", "features", "mapping", "casting")},
            "pieces": viewer_pieces, "sounds": sound_records, "created_at_utc": record["created_at_utc"]}
    page = PAGE.read_text().replace("/*SILVER_DATA*/null", json.dumps(data, separators=(",", ":")))
    (output / "index.html").write_text(page)
    log(f"viewer: {output / 'index.html'} ({(output / 'index.html').stat().st_size / 1e6:.1f} MB)")
    return output
