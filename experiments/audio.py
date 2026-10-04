"""CLAP descriptor ranking and shared-reference artistic controls."""

import gc
import math
from pathlib import Path

from .data import Layout, ROOT, digest, now, read_json, write_json

VOCABULARY = ROOT / "resources" / "material-vocabulary.json"
CLAP_MODEL = "laion/clap-htsat-unfused"


def device_name(requested: str):
    import torch

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is unavailable")
    if requested not in ("cpu", "cuda"):
        raise ValueError("Choose auto, cpu, or cuda for --device")
    return requested


def release_models():
    import torch

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def listening_copy(source: Path, destination: Path, gain: float | None = None):
    """Audible playback copy; raw audio and measurements remain separate."""
    import numpy as np
    import soundfile as sf

    audio, rate = sf.read(source, dtype="float32", always_2d=True)
    if not np.isfinite(audio).all():
        raise ValueError(f"Non-finite playback audio: {source}")
    peak = float(np.max(np.abs(audio)))
    gain = .8 / peak if gain is None and peak > 0 else gain or 1.0
    sf.write(destination, np.clip(audio * gain, -.999, .999), rate, subtype="PCM_16")
    return {"gain": gain, "source_peak": peak, "note": "Playback gain only; features and geometry use original amplitudes."}


def load_audio(path: Path, seconds: float = 10.0):
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly

    with sf.SoundFile(path) as stream:
        rate = stream.samplerate
        channels = stream.channels
        total_frames = stream.frames
        signal = stream.read(min(total_frames, round(seconds * rate)), dtype="float32", always_2d=True)
    mono = signal.mean(axis=1)
    if len(mono) < 2 or not np.isfinite(mono).all():
        raise ValueError(f"Empty, too short, or non-finite audio: {path}")
    divisor = math.gcd(rate, 48000)
    audio = resample_poly(mono, 48000 // divisor, rate // divisor).astype(np.float32)
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    if rms < 1e-12:
        raise ValueError(f"Silent audio cannot drive this experiment: {path}")
    return audio, {
        "source_sample_rate": rate, "source_channels": channels, "source_duration_s": total_frames / rate,
        "offset_s": 0, "analyzed_duration_s": len(audio) / 48000, "sample_rate": 48000,
        "channel_mapping": "Arithmetic mean to mono", "resampling": "scipy.signal.resample_poly (anti-aliasing)",
        "crop": "First up to ten seconds; CLAP processor repeat-pads short clips to its ten-second window.",
        "rms": rms, "rms_dbfs": 20 * math.log10(rms),
        "bandwidth_note": "No pitch shifting; resampling may remove energy above 24 kHz.",
    }


def reference_controls(values, low=0.30, high=0.55):
    """Scale all clips on a common dBFS reference, never each clip independently."""
    import numpy as np

    if not (0 < low <= high <= 1):
        raise ValueError("Edit bounds must satisfy 0 < low <= high <= 1")
    if not values or not all(math.isfinite(x) for x in values):
        raise ValueError("Reference values must be finite and nonempty")
    lower, upper = (float(x) for x in np.percentile(values, [10, 90]))
    controls = [0.5 if upper == lower else max(0.0, min(1.0, (x - lower) / (upper - lower))) for x in values]
    return [low + (high - low) * x for x in controls], {
        "feature": "rms_dbfs", "percentiles": [10, 90], "reference_range": [lower, upper],
        "edit_amount_range": [low, high], "formula": "low + (high-low)*clip((rms_dbfs-p10)/(p90-p10),0,1)",
        "constant_reference": "Midpoint when p10 == p90",
        "interpretation": "Recording amplitude is an artistic control; microphone gain and distance also affect it.",
    }


def analyze(layout: Layout, audio_dir: Path | None = None, vocabulary: Path = VOCABULARY,
            device: str = "auto", model_id: str = CLAP_MODEL, revision: str | None = None):
    import numpy as np
    import torch
    from huggingface_hub import HfApi
    from transformers import ClapModel, ClapProcessor

    layout.create()
    audio_dir = audio_dir or layout.input / "audio"
    paths = sorted(path for path in audio_dir.iterdir() if path.suffix.lower() in (".wav", ".flac", ".ogg", ".mp3", ".aif", ".aiff"))
    if not paths:
        raise ValueError(f"No audio found in {audio_dir}; run 'art fetch' or supply --audio-dir")
    vocab = read_json(vocabulary)
    descriptions = [item["text"] for item in vocab["descriptors"]]
    if not descriptions or len(set(item["id"] for item in vocab["descriptors"])) != len(descriptions):
        raise ValueError("Vocabulary must contain descriptors with unique IDs")
    source_path = audio_dir / "sources.json"
    sources = {item["id"]: item for item in read_json(source_path)["clips"]} if source_path.exists() else {}
    revision = HfApi().model_info(model_id, revision=revision, timeout=60).sha
    device = device_name(device)
    print(f"Loading CLAP {model_id}@{revision[:10]} on {device}", flush=True)
    processor = ClapProcessor.from_pretrained(model_id, revision=revision, cache_dir=layout.cache)
    # The official CLAP release provides pytorch_model.bin, not safetensors.
    model = ClapModel.from_pretrained(model_id, revision=revision, cache_dir=layout.cache, use_safetensors=False).to(device).eval()
    clips = []
    for path in paths:
        audio, preprocessing = load_audio(path)
        # The unfused checkpoint uses repeat-padding rather than random fusion crops.
        inputs = processor(text=descriptions, audio=audio, sampling_rate=48000, return_tensors="pt", padding=True)
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.inference_mode():
            result = model(**inputs)
            scores = (result.audio_embeds @ result.text_embeds.T).float().cpu().numpy()[0]
        selected = int(np.argmax(scores))
        source = sources.get(path.stem, {"note": "User-supplied audio; no dataset metadata provided."}).copy()
        sha = digest(path)
        if source.get("sha256", sha) != sha:
            raise ValueError(f"Source waveform changed since download: {path}")
        source.update(path=str(path.resolve()), sha256=sha)
        clips.append({
            "id": path.stem, "source": source, "preprocessing": preprocessing,
            "scores": {item["id"]: float(score) for item, score in zip(vocab["descriptors"], scores)},
            "selected_descriptor": vocab["descriptors"][selected],
        })
        print(f"{path.stem}: {descriptions[selected]} (cosine {scores[selected]:.3f})", flush=True)
    del model, processor, inputs, result
    release_models()
    amounts, controls = reference_controls([clip["preprocessing"]["rms_dbfs"] for clip in clips])
    for clip, amount in zip(clips, amounts):
        clip["edit_amount"] = amount
    report = {
        "created_at_utc": now(), "audio_model": {"id": model_id, "revision": revision, "device": device},
        "score_type": "Cosine similarity, not probabilities or biologically validated classifications",
        "vocabulary": vocab, "vocabulary_sha256": digest(vocabulary), "clips": clips,
        "controls": controls, "reference_clip_ids": [clip["id"] for clip in clips],
    }
    path = layout.interim / "analysis.json"
    write_json(path, report)
    return path
