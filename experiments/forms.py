"""Measured audio → explicit silver/amber cocoon geometry, without a generator."""

import math
from pathlib import Path
import shutil

from .data import Layout, digest, now, read_json, write_json


def extract_features(path: Path):
    import numpy as np
    import soundfile as sf
    from scipy.signal import stft

    samples, rate = sf.read(path, dtype="float32", always_2d=True)
    waveform = samples.mean(axis=1)
    if len(waveform) < rate or not np.isfinite(waveform).all() or np.max(np.abs(waveform)) < 1e-12:
        raise ValueError(f"Need at least one second of finite, non-silent audio: {path}")
    window = round(.05 * rate)
    hop = round(.025 * rate)
    frequencies, time, spectrum = stft(waveform, rate, nperseg=window, noverlap=window-hop, boundary=None, padded=False)
    power = np.abs(spectrum).astype(np.float64) ** 2
    selected = (frequencies >= 2000) & (frequencies <= min(20000, rate / 2))
    energy = power[selected].sum(axis=0)
    if not selected.any() or np.max(energy) < 1e-20:
        raise ValueError("No usable energy in the selected 2–20 kHz spectral band")
    centroid = (frequencies[selected, None] * power[selected]).sum(axis=0) / np.maximum(energy, 1e-30)
    # RMS is measured on the original waveform, independently of spectral filtering.
    starts = np.arange(len(time)) * hop
    rms = np.array([np.sqrt(np.mean(waveform[start:start+window].astype(np.float64) ** 2)) for start in starts])
    db = 20 * np.log10(np.maximum(rms, 1e-12))
    return {"time_s": time, "centroid_hz": centroid, "rms_dbfs": db,
            "sample_rate": rate, "source_channels": samples.shape[1], "duration_s": len(waveform) / rate}, waveform


def scale(values, bounds):
    import numpy as np

    low, high = bounds
    return np.full_like(values, .5, dtype=float) if low == high else np.clip((values-low)/(high-low), 0, 1)


def parameters(features, duration, reference):
    import numpy as np

    duration = min(float(duration), features["duration_s"])
    if duration <= 0:
        raise ValueError("Duration must be positive")
    count = min(120, max(3, math.ceil(duration / .75)))
    times = (np.arange(count) + .5) * duration / count
    centroid = np.interp(times, features["time_s"], features["centroid_hz"])
    rms = np.interp(times, features["time_s"], features["rms_dbfs"])
    return {"duration_s": duration, "rib_count": count, "sample_time_s": times.tolist(),
            "centroid_hz": centroid.tolist(), "rms_dbfs": rms.tolist(),
            "mid_radius_mm": (12 + 8 * scale(centroid, reference["centroid_hz"])).tolist(),
            "rib_diameter_mm": (.55 + 1.65 * scale(rms, reference["rms_dbfs"])).tolist()}


def tube(curve, diameter, sides=8):
    import numpy as np

    tangent = np.gradient(curve, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    helper = np.tile([0., 0., 1.], (len(curve), 1))
    helper[np.abs(tangent[:, 2]) > .95] = [1., 0., 0.]
    normal = np.cross(tangent, helper)
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    binormal = np.cross(tangent, normal)
    angles = np.arange(sides) * 2 * np.pi / sides
    vertices = (curve[:, None] + diameter / 2 * (normal[:, None] * np.cos(angles)[None, :, None] +
                                                binormal[:, None] * np.sin(angles)[None, :, None])).reshape(-1, 3)
    faces = []
    for i in range(len(curve)-1):
        for j in range(sides):
            a, b = i*sides+j, i*sides+(j+1) % sides
            c, d = a+sides, b+sides
            faces.extend([[a, b, c], [b, d, c]])
    return vertices, np.asarray(faces, dtype=int)


def mesh(params):
    import numpy as np

    vertices, faces, offset = [], [], 0
    s = np.linspace(0, 1, 32)
    curves = []
    for i, (radius, diameter) in enumerate(zip(params["mid_radius_mm"], params["rib_diameter_mm"])):
        theta = 2 * np.pi * i / params["rib_count"]
        # r(0.5) equals the controlled radius exactly. Fixed 22 mm height and 12 mm foot radius.
        r = 12 * (1-s) + (radius-6) * np.sin(np.pi*s)
        curves.append((np.column_stack([r*np.cos(theta), r*np.sin(theta), 22*s]), diameter))
    theta = np.linspace(0, 2*np.pi, 121)
    curves.append((np.column_stack([12*np.cos(theta), 12*np.sin(theta), np.zeros_like(theta)]), .9))
    for curve, diameter in curves:
        v, f = tube(curve, diameter)
        vertices.append(v)
        faces.append(f+offset)
        offset += len(v)
    return np.concatenate(vertices), np.concatenate(faces)


def render(output: Path, name: str, params, source_id):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np

    vertices, faces = mesh(params)
    figure = plt.figure(figsize=(5.5, 5.5), facecolor="#f4f0e5")
    axes = figure.add_axes([.02, .09, .96, .82], projection="3d", facecolor="#f4f0e5")
    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
    light = np.array([.4, -.6, .7]); light /= np.linalg.norm(light)
    shades = .47 + .45 * np.abs(normals @ light)
    colors = np.column_stack([shades*.96, shades*.98, shades, np.ones(len(shades))])
    axes.add_collection3d(Poly3DCollection(triangles, facecolors=colors, edgecolors="none", zsort="average"))
    u, v = np.meshgrid(np.linspace(0, 2*np.pi, 40), np.linspace(0, np.pi, 25))
    axes.plot_surface(8*np.cos(u)*np.sin(v), 6.5*np.sin(u)*np.sin(v), 11+9*np.cos(v),
                      color="#b66d12", alpha=.83, linewidth=0, shade=True)
    axes.set(xlim=(-23, 23), ylim=(-23, 23), zlim=(-2, 26))
    axes.set_box_aspect([46, 46, 28])
    axes.set_proj_type("ortho")
    axes.view_init(elev=23, azim=-55)
    axes.set_axis_off()
    figure.text(.05, .95, f"{params['duration_s']:.1f} s → {params['rib_count']} silver ribs", size=16, weight="bold", color="#39352f")
    figure.text(.05, .055, f"Radius {min(params['mid_radius_mm']):.1f}–{max(params['mid_radius_mm']):.1f} mm  |  diameter {min(params['rib_diameter_mm']):.2f}–{max(params['rib_diameter_mm']):.2f} mm", size=10, color="#39352f")
    figure.text(.05, .023, f"{source_id} · explicit procedural geometry", size=9, color="#39352f")
    figure.savefig(output / f"{name}.png", dpi=130)
    plt.close(figure)
    # The mesh exposes the exact controlled silver geometry; intersections/open tube ends are not fabrication-ready.
    with (output / f"{name}.obj").open("w") as stream:
        stream.write("# Sound-controlled silver cocoon; coordinates in millimeters; concept mesh, not fabrication validated\n")
        for x, y, z in vertices:
            stream.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for a, b, c in faces+1:
            stream.write(f"f {a} {b} {c}\n")
    return {"image": f"{name}.png", "mesh": f"{name}.obj", "image_sha256": digest(output / f"{name}.png"),
            "mesh_sha256": digest(output / f"{name}.obj"), "parameters": params}


def control_diagram(output: Path, clip, reference):
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(16, 10), facecolor="#f4f0e5")
    figure.text(.035, .965, "Sound controls actual silver geometry", size=26, weight="bold", color="#39352f")
    figure.text(.035, .927, f"{clip['source']['id']} · {clip['features']['duration_s']:.1f} s real recording · three prefixes of the same waveform", size=13)
    axes = figure.add_axes([.025, .535, .47, .35]); axes.imshow(plt.imread(output / clip["features_image"])); axes.set_axis_off()
    for y, heading, description in [
        (.865, "Duration → number of ribs", ", ".join(f"{v['parameters']['duration_s']:.1f} s = {v['parameters']['rib_count']} ribs" for v in clip["variants"])),
        (.75, "Spectral centroid → mid-height radius", f"2–20 kHz energy centroid; shared reference {reference['centroid_hz'][0]/1000:.2f}–{reference['centroid_hz'][1]/1000:.2f} kHz.\nLinear, clipped mapping to 12–20 mm for each rib."),
        (.615, "Local RMS → rib diameter", f"Shared reference {reference['rms_dbfs'][0]:.1f}–{reference['rms_dbfs'][1]:.1f} dBFS.\nLinear, clipped mapping to 0.55–2.20 mm for each rib."),
    ]:
        figure.text(.52, y, heading, size=16, weight="bold", color="#916428")
        figure.text(.52, y-.035, description, size=12, color="#39352f", va="top", linespacing=1.6)
    for i, variant in enumerate(clip["variants"]):
        axes = figure.add_axes([.025+i*.325, .065, .31, .445])
        axes.imshow(plt.imread(output / variant["image"])); axes.set_axis_off()
    figure.text(.035, .038, "Fixed amber core, camera, height and foot radius. The numeric controls create the mesh directly; no diffusion randomness.", size=12, color="#39352f")
    figure.text(.035, .016, "Artistic acoustic mappings, not animal meanings or verified manufacturing constraints. Full time series and per-rib dimensions are in studies.json.", size=10, color="#39352f")
    figure.savefig(output / "controls.png", dpi=150)
    figure.savefig(output / "controls.svg")
    plt.close(figure)


def generate_forms(layout: Layout, source_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import soundfile as sf
    from .audio import listening_copy

    sources = read_json(source_path)
    features, waveforms = [], []
    for source in sources["clips"]:
        path = Path(source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError(f"Source audio changed: {path}")
        feature, waveform = extract_features(path)
        features.append(feature); waveforms.append(waveform)
    reference = {key: np.percentile(np.concatenate([feature[key] for feature in features]), [10, 90]).tolist()
                 for key in ("centroid_hz", "rms_dbfs")}
    output = layout.output / "long-forms"
    (output / "audio").mkdir(parents=True, exist_ok=True)
    clips = []
    for source, feature, waveform in zip(sources["clips"], features, waveforms):
        filename = Path(source["path"]).name
        shutil.copy2(source["path"], output / "audio" / filename)
        figure, axes = plt.subplots(3, 1, figsize=(8, 6), sharex=True, facecolor="#f4f0e5")
        stride = max(1, len(waveform)//7000)
        axes[0].plot(np.arange(len(waveform))[::stride]/feature["sample_rate"], waveform[::stride], color="#916428", linewidth=.6)
        axes[0].set_ylabel("Waveform")
        axes[1].plot(feature["time_s"], feature["centroid_hz"]/1000, color="#916428", linewidth=1)
        axes[1].set_ylabel("Centroid (kHz)")
        axes[2].plot(feature["time_s"], feature["rms_dbfs"], color="#916428", linewidth=1)
        axes[2].set_ylabel("RMS (dBFS)"); axes[2].set_xlabel("Time (seconds); entire recording")
        for axis in axes:
            axis.spines[["top", "right"]].set_visible(False)
            axis.set_facecolor("white")
        figure.suptitle(f"{source['id']} · measured time series", color="#39352f")
        figure.tight_layout()
        plot = f"{source['id']}-features.png"
        figure.savefig(output / plot, dpi=130); plt.close(figure)
        variants = []
        playback_gain = .8 / float(np.max(np.abs(waveform)))
        for label, duration in [("5s", 5), ("15s", 15), ("full", feature["duration_s"])]:
            params = parameters(feature, duration, reference)
            variant = render(output, f"{source['id']}-{label}", params, source["id"])
            if label == "full":
                variant["audio"] = f"audio/{filename}"
            else:
                variant["audio"] = f"audio/{source['id']}-{label}.wav"
                sf.write(output / variant["audio"], waveform[:round(params["duration_s"] * feature["sample_rate"])],
                         feature["sample_rate"], subtype="PCM_16")
            variant["audio_sha256"] = digest(output / variant["audio"])
            variant["playback_audio"] = f"audio/{source['id']}-{label}-listen.wav"
            variant["playback"] = listening_copy(output / variant["audio"], output / variant["playback_audio"], playback_gain)
            variant["playback_sha256"] = digest(output / variant["playback_audio"])
            variants.append(variant)
        exported = {key: value.tolist() if isinstance(value, np.ndarray) else value for key, value in feature.items()}
        clips.append({"source": source, "audio": f"audio/{filename}", "features_image": plot,
                      "features": exported, "variants": variants})
        print(f"Rendered {source['id']}: whole {feature['duration_s']:.1f}s, {feature['sample_rate']} Hz; 5s/15s/full geometry", flush=True)
    control_diagram(output, clips[0], reference)
    write_json(output / "studies.json", {"created_at_utc": now(), "reference": reference, "source_selection": sources["selection"],
        "mapping": {"time": "Prefix duration → ceil(seconds / 0.75) ribs, clamped to 3–120; time advances around the cocoon.",
                    "spectral_centroid": "2–20 kHz power-weighted centroid → mid-height radius 12–20 mm using shared p10/p90.",
                    "amplitude": "Original-waveform frame RMS dBFS → rib diameter 0.55–2.20 mm using shared p10/p90.",
                    "fixed": "22 mm crown height, 12 mm base radius, amber ellipsoid and view. Same full-source reference ranges for all prefixes.",
                    "interpretation": "Artistic mappings from all recorded acoustic energy; no whale call isolation or pitch estimator. Mesh intersections and open ends require fabrication work."},
        "clips": clips})
    return output / "studies.json"
