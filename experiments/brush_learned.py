"""Optional learned layer: frozen 2026 OpenWhistle embeddings choose brush commands.

The encoder is not a command recognizer. A few labelled examples of our designed
contours enroll one centroid per command; a sound is assigned to the nearest centroid
or rejected. The measured contour/DTW layer is evaluated on exactly the same audio.
"""

from dataclasses import dataclass
import math
from pathlib import Path

from .brush import measure, read_audio, recognize, synthesize_note
from .data import Layout, digest, now, read_json, write_json

MODEL_ID = "dolphinteam/OpenWhistle-Wav2Vec2.0"
# Card update of 2026-09-29; the weights were committed in 1b92224 on 2026-05-04.
REVISION = "985ac11bc6939af5e41383143aad5a0ae6993f68"
LAYERS = (3, 6, 9, 12)
PAD_S = 0.15


@dataclass
class Encoder:
    extractor: object
    model: object
    device: str
    info: dict


def load_encoder(layout: Layout, device: str = "auto", revision: str = REVISION):
    import torch
    from transformers import AutoFeatureExtractor, AutoModel

    from .audio import device_name

    device = device_name(device)
    extractor = AutoFeatureExtractor.from_pretrained(MODEL_ID, revision=revision, cache_dir=layout.cache)
    model, loading = AutoModel.from_pretrained(MODEL_ID, revision=revision, cache_dir=layout.cache, output_loading_info=True)
    if loading["missing_keys"]:
        raise ValueError(f"OpenWhistle encoder weights missing: {sorted(loading['missing_keys'])[:5]}")
    model = model.to(device).eval()
    info = {"id": MODEL_ID, "revision": revision, "class": type(model).__name__, "device": device, "dtype": str(model.dtype),
            "sampling_rate": extractor.sampling_rate, "do_normalize": extractor.do_normalize,
            "missing_keys": sorted(loading["missing_keys"]), "unused_pretraining_keys": sorted(loading["unexpected_keys"]),
            "license": "Not specified on the model card (checked 2026-10-07)",
            "training_population": "Bottlenose dolphins at Dolphin Reef, Eilat (arXiv:2609.34839); not WDP spotted dolphins or synthetic CHAT-style whistles",
            "torch": torch.__version__}
    return Encoder(extractor, model, device, info)


POOLINGS = ("mean", "chunks", "chunk-deltas")
CHUNKS = 4


def pool(hidden, pooling: str):
    """Mean pooling discards temporal order; chunks keep coarse order; deltas also remove the clip mean."""
    import numpy as np

    if pooling == "mean":
        return hidden.mean(axis=0)
    edges = np.linspace(0, len(hidden), CHUNKS + 1).round().astype(int)
    parts = np.stack([hidden[a:max(b, a + 1)].mean(axis=0) for a, b in zip(edges[:-1], edges[1:])])
    if pooling == "chunk-deltas":
        parts = parts - parts.mean(axis=0)
    return parts.reshape(-1)


def embed(encoder: Encoder, clips, rate: int):
    """Hidden states for each clip, pooled in each tested way, for each selected layer."""
    import numpy as np
    import torch
    from scipy.signal import resample_poly

    target = encoder.extractor.sampling_rate
    vectors = {(layer, pooling): [] for layer in LAYERS for pooling in POOLINGS}
    for clip in clips:
        audio = np.asarray(clip, dtype=np.float64)
        if rate != target:
            divisor = math.gcd(rate, target)
            audio = resample_poly(audio, target // divisor, rate // divisor)
        inputs = encoder.extractor(audio.astype(np.float32), sampling_rate=target, return_tensors="pt")
        with torch.inference_mode():
            hidden = encoder.model(inputs["input_values"].to(encoder.device), output_hidden_states=True).hidden_states
        for layer in LAYERS:
            states = hidden[layer][0].float().cpu().numpy()
            for pooling in POOLINGS:
                vectors[(layer, pooling)].append(pool(states, pooling))
    return {key: np.stack(values) for key, values in vectors.items()}


def normalize(vectors, centre):
    import numpy as np

    shifted = vectors - centre
    return shifted / np.maximum(np.linalg.norm(shifted, axis=1, keepdims=True), 1e-12)


def contour_clip(config: dict, family: str, duration: float, register: float = 0.0, velocity: int = 100, bend: float = 0.0):
    import numpy as np

    event = {"note": 60, "duration_s": duration, "velocity": velocity, "bend": [[0.0, 0.0], [1.0, bend]],
             "source": {"family": family}, "register_octaves": register}
    pad = np.zeros(round(PAD_S * config["sample_rate"]))
    return np.concatenate([pad, synthesize_note(event, config, {}), pad])


def background(layout: Layout, rate: int):
    """Real pool background from a local OpenWhistle pretraining sequence (may contain animal sounds)."""
    import numpy as np
    from scipy.signal import resample_poly
    import soundfile as sf

    manifest = layout.input / "long-audio" / "sources.json"
    if not manifest.exists():
        raise ValueError("Noise tests need: uv run --group art --group viz main.py art long-forms")
    source = read_json(manifest)["clips"][0]
    path = Path(source["path"])
    if digest(path) != source["sha256"]:
        raise ValueError(f"Background source changed: {path}")
    audio, source_rate = sf.read(path, dtype="float64", always_2d=True)
    audio = audio.mean(axis=1)
    divisor = math.gcd(source_rate, rate)
    audio = resample_poly(audio, rate // divisor, source_rate // divisor)
    return audio / np.sqrt(np.mean(audio ** 2)), {"id": source["id"], "sha256": source["sha256"], "source_sample_rate": source_rate}


def with_noise(clip, noise, snr_db: float, offset: int):
    import numpy as np

    signal = clip[np.abs(clip) > 0]
    level = np.sqrt(np.mean(signal ** 2)) / 10 ** (snr_db / 20)
    return clip + level * noise[offset:offset + len(clip)]


def natural_whistles(layout: Layout, config: dict, limit: int = 6):
    """Longest measured tonal segments in local recordings: natural sounds outside the vocabulary."""
    import numpy as np
    from scipy.signal import butter, sosfiltfilt

    items, rate = [], config["sample_rate"]
    sources = sorted((layout.input / "audio").glob("openwhistle-*.wav")) + sorted((layout.input / "long-audio").glob("*.wav"))
    sos = butter(4, config["keyboard"]["recording_highpass_hz"], "highpass", fs=rate, output="sos")
    for path in sources:
        audio, source_rate = read_audio(path)
        if source_rate != rate:
            from scipy.signal import resample_poly

            divisor = math.gcd(source_rate, rate)
            audio = resample_poly(audio, rate // divisor, source_rate // divisor)
        audio = sosfiltfilt(sos, audio)
        audio = audio / np.max(np.abs(audio)) * 10 ** (-12 / 20)
        segments = [s for s in measure(audio, rate, config)["segments"] if s["kind"] == "tonal" and s["duration_s"] >= .15]
        for segment in sorted(segments, key=lambda s: -s["duration_s"])[:limit if "long" in path.stem else 1]:
            start = max(0, round((segment["start_s"] - .1) * rate))
            stop = min(len(audio), round((segment["end_s"] + .1) * rate))
            items.append({"condition": "natural whistles", "label": f"{path.stem}@{segment['start_s']:.2f}s",
                          "expected": "none", "audio": audio[start:stop], "source": path.stem})
    return items


def test_items(layout: Layout, config: dict):
    commands = list(config["commands"])
    items = []
    for family in commands + ["fall", "flat"]:
        expected = config["commands"].get(family, "none")
        for duration in (.35, .6, .85, 1.2):
            items.append({"condition": "clean", "label": family, "expected": expected, "audio": contour_clip(config, family, duration, .1)})
        for register in (-.75, -.25, .25, .75):
            items.append({"condition": "transposed", "label": family, "expected": expected, "audio": contour_clip(config, family, .7, register)})
        for bend in (-.5, .5):
            items.append({"condition": "pitch bend ±0.5", "label": family, "expected": expected, "audio": contour_clip(config, family, .7, 0, bend=bend)})
    noise, noise_source = background(layout, config["sample_rate"])
    for snr in (20, 10, 0):
        for index, family in enumerate(commands + ["fall", "flat"]):
            for repeat, duration in enumerate((.5, .9)):
                clip = contour_clip(config, family, duration, .1)
                offset = (index * 2 + repeat) * 61_000 + snr * 997
                items.append({"condition": f"pool noise {snr} dB SNR", "label": family, "expected": config["commands"].get(family, "none"),
                              "audio": with_noise(clip, noise, snr, offset)})
    return items + natural_whistles(layout, config), noise_source


def enrollment(config: dict):
    items = []
    for family in config["commands"]:
        for duration in (.45, .7, 1.0):
            for register in (-.5, 0, .5):
                items.append({"label": family, "command": config["commands"][family], "audio": contour_clip(config, family, duration, register)})
    return items


def centroids(vectors, labels):
    import numpy as np

    names = sorted(set(labels))
    return names, np.stack([vectors[[label == name for label in labels]].mean(axis=0) for name in names])


def leave_one_out(vectors, labels):
    import numpy as np

    rows = []
    for i in range(len(labels)):
        keep = np.arange(len(labels)) != i
        names, centres = centroids(vectors[keep], [label for j, label in enumerate(labels) if keep[j]])
        centres = centres / np.linalg.norm(centres, axis=1, keepdims=True)
        scores = centres @ vectors[i]
        order = np.argsort(-scores)
        own = scores[names.index(labels[i])]
        other = max(score for name, score in zip(names, scores) if name != labels[i])
        rows.append({"correct": names[order[0]] == labels[i], "own": float(own), "other": float(other)})
    return rows


class LearnedLayer:
    """Nearest enrolled centroid with a rejection threshold calibrated on the enrollment set."""

    def __init__(self, encoder: Encoder, config: dict):
        import numpy as np

        self.encoder, self.config, rate = encoder, config, config["sample_rate"]
        items = enrollment(config)
        labels = [item["label"] for item in items]
        raw = embed(encoder, [item["audio"] for item in items], rate)
        selection = {}
        for key, values in raw.items():
            rows = leave_one_out(normalize(values, values.mean(axis=0)), labels)
            selection[key] = {"layer": key[0], "pooling": key[1], "loo_accuracy": float(np.mean([row["correct"] for row in rows])),
                              "mean_margin": float(np.mean([row["own"] - row["other"] for row in rows])),
                              "min_own_cosine": float(min(row["own"] for row in rows))}
        self.key = max(selection, key=lambda key: (selection[key]["loo_accuracy"], selection[key]["mean_margin"]))
        self.layer, self.pooling = self.key
        self.centre = raw[self.key].mean(axis=0)
        vectors = normalize(raw[self.key], self.centre)
        self.names, centres = centroids(vectors, labels)
        self.centres = centres / np.linalg.norm(centres, axis=1, keepdims=True)
        rows = leave_one_out(vectors, labels)
        self.threshold = min(row["own"] for row in rows)
        self.margin = .02
        self.enrolled = {"vectors": vectors, "labels": labels}
        self.report = {"model": encoder.info, "representations_compared": list(selection.values()),
                       "selected": {"layer": self.layer, "pooling": self.pooling, "chunks": CHUNKS if self.pooling != "mean" else 1},
                       "enrollment": {"families": list(config["commands"]), "durations_s": [.45, .7, 1.0], "register_octaves": [-.5, 0, .5],
                                      "examples": len(items), "velocity": 100},
                       "rule": f"Hidden layer {self.layer}, {self.pooling} pooling; subtract the enrollment mean; cosine to class centroids; accept if best ≥ threshold and best − second ≥ margin.",
                       "threshold_cosine": self.threshold, "margin_cosine": self.margin,
                       "calibration": "Layer/pooling chosen by leave-one-out accuracy on enrollment only. Threshold = lowest leave-one-out own-class cosine in enrollment; fixed before any test item is seen."}

    def classify(self, clips):
        import numpy as np

        vectors = normalize(embed(self.encoder, clips, self.config["sample_rate"])[self.key], self.centre)
        results = []
        for vector in vectors:
            scores = self.centres @ vector
            order = np.argsort(-scores)
            best, second = self.names[order[0]], self.names[order[1]]
            margin = float(scores[order[0]] - scores[order[1]])
            accepted = scores[order[0]] >= self.threshold and margin >= self.margin
            reason = f"{best} cosine {scores[order[0]]:.3f}, margin {margin:.3f}"
            if not accepted:
                reason = ("below threshold: " if scores[order[0]] < self.threshold else "ambiguous: ") + reason
            results.append({"method": "openwhistle-centroid", "command": self.config["commands"][best] if accepted else "none",
                            "accepted": bool(accepted), "nearest": best, "cosines": dict(zip(self.names, map(float, scores))),
                            "margin": margin, "reason": reason, "vector": vector})
        return results

    def recognizer(self, waveform, rate, measured, recognitions):
        """Replace contour commands for tonal segments; continuous controls stay measured."""
        tonal = [(i, s) for i, s in enumerate(measured["segments"]) if s["kind"] == "tonal"]
        clips = [waveform[max(0, round((s["start_s"] - .05) * rate)):round((s["end_s"] + .05) * rate)] for _, s in tonal]
        results = list(recognitions)
        for (index, segment), learned in zip(tonal, self.classify(clips) if clips else []):
            learned.pop("vector")
            if segment["duration_s"] < self.config["recognition"]["min_duration_s"]:
                learned |= {"command": "none", "accepted": False, "reason": f"too short ({segment['duration_s']:.2f} s); " + learned["reason"]}
            results[index] = learned
        return results


def contour_command(audio, config: dict):
    tonal = [s for s in measure(audio, config["sample_rate"], config)["segments"] if s["kind"] == "tonal"]
    if not tonal:
        return {"command": "none", "accepted": False, "reason": "no tonal segment measured"}, None
    segment = max(tonal, key=lambda s: s["duration_s"])
    return recognize(segment, config), segment


def evaluate(layout: Layout, config: dict, layer: LearnedLayer):
    """Same audio through both layers; crops for the encoder follow the measured tonal segment."""
    import numpy as np

    items, noise_source = test_items(layout, config)
    rate = config["sample_rate"]
    rows, clips = [], []
    for item in items:
        contour, segment = contour_command(item["audio"], config)
        if segment is None:
            clips.append(item["audio"])
        else:
            clips.append(item["audio"][max(0, round((segment["start_s"] - .05) * rate)):round((segment["end_s"] + .05) * rate)])
        rows.append({"condition": item["condition"], "label": item["label"], "expected": item["expected"], "contour": contour})
    for row, learned in zip(rows, layer.classify(clips)):
        row["learned_vector"] = learned.pop("vector")
        row["learned"] = learned
    summary = {}
    for condition in dict.fromkeys(row["condition"] for row in rows):
        group = [row for row in rows if row["condition"] == condition]
        entry = {"items": len(group)}
        for method in ("contour", "learned"):
            commands = [row for row in group if row["expected"] != "none"]
            others = [row for row in group if row["expected"] == "none"]
            entry[method] = {"command_items": len(commands),
                             "correct": sum(row[method]["command"] == row["expected"] for row in commands),
                             "wrong_command": sum(row[method]["accepted"] and row[method]["command"] != row["expected"] for row in commands),
                             "rejected": sum(not row[method]["accepted"] for row in commands),
                             "non_command_items": len(others),
                             "false_accepts": sum(row[method]["accepted"] for row in others)}
        summary[condition] = entry
    return rows, summary, noise_source


def figure(path: Path, rows: list[dict], summary: dict, layer: LearnedLayer):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from .brush import PALETTE

    conditions = list(summary)
    fig = plt.figure(figsize=(16, 7.5), facecolor="#f4f0e5")
    fig.text(.02, .95, "Measured contour vs OpenWhistle embeddings · same audio, same command vocabulary", size=16, weight="bold", color="#39352f")
    axes = fig.add_axes([.05, .14, .5, .7])
    x = np.arange(len(conditions))
    for shift, method, colour, marker, name in ((-.2, "contour", "#2f6f8f", "x", "measured contour + DTW"), (.2, "learned", "#b0703a", "P", "OpenWhistle + centroids")):
        correct = [summary[c][method]["correct"] / max(1, summary[c][method]["command_items"]) for c in conditions]
        false = [summary[c][method]["false_accepts"] / max(1, summary[c][method]["non_command_items"]) for c in conditions]
        axes.bar(x + shift, correct, .38, color=colour, label=f"{name}: commands correct")
        axes.scatter(x + shift, false, marker=marker, color="#9c392d", zorder=3, s=70, label=f"{name}: non-commands accepted")
    axes.set_xticks(x, [c.replace(" SNR", "") for c in conditions], rotation=25, ha="right", fontsize=9)
    axes.set_ylim(0, 1.05)
    axes.set_ylabel("Fraction of items")
    axes.legend(fontsize=8, frameon=False, loc="lower left")
    axes.set_title("Bars: designed commands recognized · red marks: falls, flats and natural whistles wrongly accepted", loc="left", size=10)
    pca_axes = fig.add_axes([.6, .1, .38, .75])
    vectors = np.vstack([layer.enrolled["vectors"]] + [row["learned_vector"][None] for row in rows])
    mean = vectors.mean(axis=0)
    _, _, components = np.linalg.svd(vectors - mean, full_matrices=False)
    project = lambda v: (v - mean) @ components[:2].T
    enrolled = project(layer.enrolled["vectors"])
    families = {family: PALETTE[layer.config["commands"][family]] for family in layer.config["commands"]}
    for family, colour in families.items():
        mask = np.array([label == family for label in layer.enrolled["labels"]])
        pca_axes.scatter(*enrolled[mask].T, s=60, color=colour, edgecolor="black", label=f"enrolled {family} → {layer.config['commands'][family]}")
    for row in rows:
        point = project(row["learned_vector"])
        if row["condition"] == "natural whistles":
            pca_axes.scatter(*point, marker="*", s=90, color="#555555")
        elif row["label"] in families:
            pca_axes.scatter(*point, marker=".", s=30, color=families[row["label"]], alpha=.7)
        else:
            pca_axes.scatter(*point, marker="x", s=25, color="#999999")
    pca_axes.scatter([], [], marker="*", color="#555555", label="natural whistles (should be rejected)")
    pca_axes.scatter([], [], marker="x", color="#999999", label="synthetic fall / flat")
    pca_axes.legend(fontsize=7.5, frameon=False, loc="best")
    pca_axes.set_title(f"OpenWhistle layer {layer.layer}, {layer.pooling} pooling, first two principal components", size=10)
    pca_axes.set_xticks([]); pca_axes.set_yticks([])
    fig.text(.02, .02, "Synthetic contours are outside the encoder's training domain (Eilat bottlenose recordings). Enrollment and test items do not overlap; noise is a real pool recording that may contain animal sounds.", size=9)
    fig.savefig(path, dpi=110)
    plt.close(fig)


def run(layout: Layout, config: dict, output: Path, device: str = "auto"):
    import time

    started = time.perf_counter()
    encoder = load_encoder(layout, device)
    layer = LearnedLayer(encoder, config)
    rows, summary, noise_source = evaluate(layout, config, layer)
    figure(output / "learned.png", rows, summary, layer)
    report = layer.report | {"created_at_utc": now(), "summary": summary, "noise_source": noise_source,
                             "runtime_s": round(time.perf_counter() - started, 1),
                             "items": [{key: value for key, value in row.items() if key != "learned_vector"} for row in rows]}
    for item in report["items"]:
        item["contour"] = {key: value for key, value in item["contour"].items() if key != "distances_semitones"} | {"distances_semitones": item["contour"].get("distances_semitones")}
    write_json(output / "learned.json", report)
    return layer, report
