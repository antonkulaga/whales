"""Hardata II pilot: which inscriptions keep a dolphin whistle type recognizable?

Input: OpenWhistle `balanced` whistle clips and their annotated F0 tracks.
Schema: explicit encodings with counted bits (F0 contour, spectrogram relief,
amplitude envelope, DAC codec tokens) and a simulated cast-silver contour groove.
Output: decoded audio, OpenWhistle-encoder probe predictions, a rate-distortion
chart, ring-band STL meshes and a playable input → schema → output gallery.

The probe measures whether one 2026 dolphin encoder still separates whistle
types after decoding. It is not evidence of what a dolphin would perceive.
"""

from dataclasses import asdict, dataclass
import io
import math
from pathlib import Path
import shutil
from typing import Annotated

import typer

from .data import DEFAULT_DATA, Layout, digest, get_json, now, read_json, write_json

app = typer.Typer(help="Hardata II pilot: inscribed bits, silver grooves and whistle-type retention.", no_args_is_help=True)

DATASET = "dolphinteam/OpenWhistle-Classification-Finetuning"
PARQUET_REVISION = "refs/convert/parquet"
ENCODER = "dolphinteam/OpenWhistle-Wav2Vec2.0"
CODEC = "descript/dac_44khz"
CLAP = "laion/clap-htsat-unfused"
RATE = 44_100
F_LOW, F_HIGH = 2_000.0, 22_050.0
PLACEMENT_BITS = 16  # whistle start/end inside the clip, 8 bits each at 10 ms resolution
MIN_CONFIDENCE = 0.3
SEED = 20261007
N_FFT, HOP = 1024, 256

# Written before the first evaluation run; the report compares results against these.
PREDICTIONS = {
    "registered_at_utc": "2026-10-07T16:05:00+00:00",  # before the dataset fetch; corrected from a local-time stamp
    "H1": "A 32-point, 8-bit F0 contour (272 bits) keeps at least 70% of the original-audio macro-F1 of the OpenWhistle probe.",
    "H2": "Near 0.5 kbit per whistle, contour inscriptions beat spectrogram relief and the 1-codebook DAC codec on macro-F1.",
    "H3": "The 2021 Hardata method (amplitude envelope only) stays within 10 points of chance macro-F1.",
    "H4": "Time-reversed contours and flat tones at the whistle's mean frequency lose most of the contour's advantage, showing the probe uses contour shape rather than frequency range or duration.",
    "H5": "The simulated contour groove keeps at least 90% of the digital contour's macro-F1 at 0.1 mm blur and degrades smoothly, not abruptly, with coarser casting.",
}


@dataclass(frozen=True)
class Band:
    """A plain ring band with one engraved contour groove; millimetres."""
    inner_diameter: float = 18.0
    wall: float = 1.6
    width: float = 6.0
    margin: float = 0.8
    lead: float = 2.0
    mm_per_second: float = 30.0
    groove_depth: float = 0.30  # Shapeways' minimum engraved detail for sterling silver
    groove_sigma: float = 0.15  # 0.35 mm full width at half depth
    grid: float = 0.02
    surface_noise: float = 0.005
    depth_step: float = 0.005

    @property
    def outer_radius(self):
        return self.inner_diameter / 2 + self.wall

    @property
    def circumference(self):
        return 2 * math.pi * self.outer_radius


BLURS_MM = (0.025, 0.05, 0.1, 0.2, 0.3, 0.45)


# ---------------------------------------------------------------- input data

def source_directory(layout: Layout, config: str):
    return layout.input / "openwhistle-classification" / config


def fetch(layout: Layout, config: str = "balanced", splits=("train", "validation", "test")):
    """Download pinned parquet shards with audio, labels and F0 annotations."""
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi()
    refs = api.list_repo_refs(DATASET, repo_type="dataset")
    revision = next(ref.target_commit for ref in refs.converts if ref.ref == PARQUET_REVISION)
    main = next(ref.target_commit for ref in refs.branches if ref.ref == "refs/heads/main")
    names = sorted(name for name in api.list_repo_files(DATASET, repo_type="dataset", revision=revision)
                   if name.split("/")[0] == config and name.split("/")[1] in splits)
    if not names:
        raise ValueError(f"No parquet shards for {config} {splits} at {revision}")
    directory = source_directory(layout, config)
    files = []
    for name in names:
        path = Path(hf_hub_download(DATASET, name, repo_type="dataset", revision=revision,
                                    local_dir=directory.parent, cache_dir=layout.cache))
        files.append({"name": name, "path": str(path.relative_to(layout.root)), "bytes": path.stat().st_size, "sha256": digest(path)})
        print(f"{name}: {path.stat().st_size:,} bytes", flush=True)
    info = get_json(f"https://datasets-server.huggingface.co/info?dataset={DATASET}&config={config}")["dataset_info"]
    manifest = {
        "dataset": DATASET, "config": config, "parquet_revision": revision, "main_revision": main,
        "label_names": info["features"]["label"]["names"], "files": files, "fetched_at_utc": now(),
        "license_note": "Hugging Face license field empty at inspection; the OpenWhistle paper states CC BY 4.0. Recorded, not resolved.",
        "splits_note": "Upstream splits are session-disjoint; this pilot keeps them unchanged.",
    }
    write_json(directory / "sources.json", manifest)
    return directory / "sources.json"


@dataclass
class Clip:
    id: str
    split: str
    label: int
    name: str
    session: str
    audio: object
    duration: float
    f0_time: object
    f0_hz: object
    f0_conf: object
    f0_ok: bool


def load_clips(layout: Layout, config: str, split: str):
    import numpy as np
    import polars as pl
    import soundfile as sf
    from scipy.signal import resample_poly

    directory = source_directory(layout, config)
    manifest = read_json(directory / "sources.json")
    names = manifest["label_names"]
    expected = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
    clips = []
    for path in sorted((directory / split).glob("*.parquet")):
        relative = str(path.relative_to(layout.root))
        if expected.get(relative) != digest(path):
            raise ValueError(f"Parquet shard changed or is not in the manifest: {path}")
        frame = pl.read_parquet(path, columns=["audio", "label", "name", "duration", "f0_time", "f0_hz", "f0_conf", "f0_ok"])
        for index, row in enumerate(frame.iter_rows(named=True)):
            audio, rate = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32", always_2d=True)
            audio = audio.mean(axis=1)
            if rate != RATE:
                divisor = math.gcd(rate, RATE)
                audio = resample_poly(audio, RATE // divisor, rate // divisor).astype(np.float32)
            clips.append(Clip(
                id=f"{split}-{path.stem}-{index:04d}", split=split, label=row["label"], name=names[row["label"]],
                session=row["name"], audio=audio, duration=len(audio) / RATE,
                f0_time=np.asarray(row["f0_time"], dtype=np.float64), f0_hz=np.asarray(row["f0_hz"], dtype=np.float64),
                f0_conf=np.asarray(row["f0_conf"], dtype=np.float64), f0_ok=bool(row["f0_ok"]),
            ))
    if not clips:
        raise ValueError(f"No clips for {config}/{split}; run 'inscription fetch' first")
    return clips


# ---------------------------------------------------------------- encodings

def log_axis(freq):
    import numpy as np

    return (np.log2(freq) - math.log2(F_LOW)) / (math.log2(F_HIGH) - math.log2(F_LOW))


def from_log_axis(position):
    import numpy as np

    return 2 ** (math.log2(F_LOW) + np.asarray(position) * (math.log2(F_HIGH) - math.log2(F_LOW)))


def contour(clip: Clip):
    """Confident F0 points (time from clip start, Hz), or None."""
    keep = (clip.f0_conf >= MIN_CONFIDENCE) & (clip.f0_hz > F_LOW) & (clip.f0_hz < F_HIGH)
    if keep.sum() < 4 or not clip.f0_ok:
        return None
    return clip.f0_time[keep], clip.f0_hz[keep]


def quantize_time(seconds):
    return min(255, max(0, round(seconds / 0.01))) * 0.01


def tone(times, freqs, duration, ramp=0.005):
    """Constant-amplitude sinusoid following a contour; silence outside it."""
    import numpy as np

    samples = max(1, round(duration * RATE))
    t = np.arange(samples) / RATE
    inside = (t >= times[0]) & (t <= times[-1])
    freq = 2 ** np.interp(t, times, np.log2(freqs))
    phase = 2 * np.pi * np.cumsum(np.where(inside, freq, 0)) / RATE
    envelope = inside.astype(np.float64)
    if inside.any():
        start, end = times[0], times[-1]
        envelope *= np.clip((t - start) / ramp, 0, 1) * np.clip((end - t) / ramp, 0, 1)
    return (0.5 * envelope * np.sin(phase)).astype(np.float32)


def encode_contour(clip, points: int, bits: int):
    import numpy as np

    track = contour(clip)
    start, end = quantize_time(track[0][0]), quantize_time(track[0][-1])
    end = max(end, start + 0.01)
    grid = np.linspace(track[0][0], track[0][-1], points)
    levels = 2 ** bits - 1
    code = np.round(np.clip(log_axis(np.interp(grid, track[0], track[1])), 0, 1) * levels)
    return {"start": start, "end": end, "code": code, "levels": levels, "bits": points * bits + PLACEMENT_BITS}


def decode_contour(payload, duration, reverse=False):
    import numpy as np

    code = payload["code"][::-1] if reverse else payload["code"]
    freqs = from_log_axis(code / payload["levels"])
    times = np.linspace(payload["start"], payload["end"], len(code))
    return tone(times, freqs, duration)


def flat_tone(clip, duration):
    """Range-only control: whistle span at its mean log frequency."""
    import numpy as np

    track = contour(clip)
    mean = 2 ** np.mean(np.log2(track[1]))
    start, end = quantize_time(track[0][0]), max(quantize_time(track[0][-1]), quantize_time(track[0][0]) + 0.01)
    return tone(np.array([start, end]), np.array([mean, mean]), duration), PLACEMENT_BITS + 8


def stft(audio):
    import torch

    window = torch.hann_window(N_FFT, dtype=torch.float64)
    return torch.stft(torch.as_tensor(audio, dtype=torch.float64), N_FFT, HOP, window=window, return_complex=True)


def griffin_lim(magnitude, samples, iterations=48, seed=SEED):
    import numpy as np
    import torch

    window = torch.hann_window(N_FFT, dtype=torch.float64)
    generator = np.random.default_rng(seed)
    phase = torch.as_tensor(np.exp(2j * np.pi * generator.random(magnitude.shape)))
    spec = magnitude * phase
    for _ in range(iterations):
        audio = torch.istft(spec, N_FFT, HOP, window=window, length=samples)
        rebuilt = torch.stft(audio, N_FFT, HOP, window=window, return_complex=True)
        spec = magnitude * torch.exp(1j * torch.angle(rebuilt))
    return torch.istft(spec, N_FFT, HOP, window=window, length=samples).numpy().astype(np.float32)


def band_edges(bands):
    import numpy as np

    return from_log_axis(np.linspace(0, 1, bands + 1))


def relief(clip, frames: int, bands: int, depth_bits: int, dynamic_db=40.0):
    """Spectrogram relief: log-power cells, quantized depth, Griffin-Lim decode."""
    import numpy as np
    import torch

    spec = stft(clip.audio)
    power = (spec.abs() ** 2).numpy()
    freqs = np.fft.rfftfreq(N_FFT, 1 / RATE)
    edges = band_edges(bands)
    band_of_bin = np.searchsorted(edges, freqs, side="right") - 1
    time_of_frame = np.minimum((np.arange(power.shape[1]) * frames) // power.shape[1], frames - 1)
    # Mean power per (band, time cell) via normalized one-hot pooling matrices.
    pool_f = (band_of_bin[None, :] == np.arange(bands)[:, None]).astype(np.float64)
    pool_t = (time_of_frame[:, None] == np.arange(frames)[None, :]).astype(np.float64)
    pool_f /= np.maximum(pool_f.sum(axis=1, keepdims=True), 1)
    pool_t /= np.maximum(pool_t.sum(axis=0, keepdims=True), 1)
    cells = np.maximum(pool_f @ power @ pool_t, 1e-12)
    db = 10 * np.log10(cells)
    db = np.clip(db - db.max(), -dynamic_db, 0)
    levels = 2 ** depth_bits - 1
    code = np.round((db + dynamic_db) / dynamic_db * levels)
    decoded_db = code / levels * dynamic_db - dynamic_db
    amplitude = np.where(code > 0, 10 ** (decoded_db / 20), 0.0)
    magnitude = np.zeros_like(power)
    valid = (band_of_bin >= 0) & (band_of_bin < bands)
    magnitude[valid] = amplitude[band_of_bin[valid]][:, time_of_frame]
    audio = griffin_lim(torch.as_tensor(magnitude), len(clip.audio))
    return audio, frames * bands * depth_bits + 16


def amplitude_only(clip, segments: int, bits: int = 3, dynamic_db=40.0, seed=SEED):
    """The 2021 Hardata mapping: amplitude rectangles, no frequency information."""
    import numpy as np

    audio = clip.audio.astype(np.float64)
    parts = np.array_split(audio, segments)
    db = np.array([10 * np.log10(max(np.mean(p ** 2), 1e-12)) for p in parts])
    db = np.clip(db - db.max(), -dynamic_db, 0)
    levels = 2 ** bits - 1
    gains = 10 ** ((np.round((db + dynamic_db) / dynamic_db * levels) / levels * dynamic_db - dynamic_db) / 20)
    noise = np.random.default_rng(seed).standard_normal(len(audio))
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(len(audio), 1 / RATE)
    spectrum[(freqs < F_LOW) | (freqs > 20_000)] = 0
    noise = np.fft.irfft(spectrum, len(audio))
    envelope = np.concatenate([np.full(len(p), g) for p, g in zip(parts, gains)])
    return (0.3 * noise / (noise.std() + 1e-12) * envelope).astype(np.float32), segments * bits + 16


def noise_bed(train, count=300):
    """Average background spectrum of training clips with the annotated whistle masked."""
    import numpy as np

    freqs = np.fft.rfftfreq(N_FFT, 1 / RATE)
    total, weight = np.zeros(len(freqs)), np.zeros(len(freqs))
    for clip in train[:count]:
        power = (stft(clip.audio).abs() ** 2).numpy()
        frame_times = np.arange(power.shape[1]) * HOP / RATE
        f0 = np.interp(frame_times, clip.f0_time, clip.f0_hz, left=np.nan, right=np.nan)
        mask = np.ones_like(power, dtype=bool)
        for k, f in enumerate(f0):
            if np.isfinite(f):
                for harmonic in (f, 2 * f, 3 * f):
                    mask[np.abs(freqs - harmonic) < 700, k] = False
        total += (power * mask).sum(axis=1)
        weight += mask.sum(axis=1)
    return (total / np.maximum(weight, 1)).tolist()


def add_noise_bed(audio, bed, snr_db=10.0, seed=SEED):
    import numpy as np
    import torch

    spec = stft(np.zeros_like(audio))
    magnitude = torch.as_tensor(np.sqrt(np.asarray(bed)))[:, None].expand(-1, spec.shape[1])
    phase = torch.as_tensor(np.exp(2j * np.pi * np.random.default_rng(seed).random(spec.shape)))
    window = torch.hann_window(N_FFT, dtype=torch.float64)
    noise = torch.istft(magnitude * phase, N_FFT, HOP, window=window, length=len(audio)).numpy()
    active = np.abs(audio) > 0
    signal_rms = np.sqrt(np.mean(audio[active] ** 2)) if active.any() else 1.0
    noise *= signal_rms / (np.sqrt(np.mean(noise ** 2)) + 1e-12) / 10 ** (snr_db / 20)
    return (audio + noise).astype(np.float32)


class Codec:
    """DAC 44.1 kHz with a chosen number of residual codebooks."""

    def __init__(self, layout: Layout, device: str):
        from huggingface_hub import HfApi
        from transformers import DacModel

        self.revision = HfApi().model_info(CODEC, timeout=60).sha
        self.model = DacModel.from_pretrained(CODEC, revision=self.revision, cache_dir=layout.cache).to(device).eval()
        self.device = device
        self.hop = int(self.model.config.hop_length)
        self.bits_per_code = int(math.log2(self.model.config.codebook_size))

    def __call__(self, audio, codebooks: int):
        import numpy as np
        import torch

        samples = len(audio)
        # DAC is not level-invariant and these recordings sit near -70 dBFS; send one 8-bit gain.
        gain = 0.1 / (float(np.sqrt(np.mean(np.square(audio)))) + 1e-12)
        padded = np.pad(audio * gain, (0, (-samples) % self.hop)).astype(np.float32)
        with torch.inference_mode():
            tensor = torch.as_tensor(padded, device=self.device)[None, None]
            encoded = self.model.encode(tensor, n_quantizers=codebooks)
            decoded = self.model.decode(quantized_representation=encoded.quantized_representation).audio_values
        frames = encoded.audio_codes.shape[-1]
        return decoded.squeeze().float().cpu().numpy()[:samples] / gain, frames * codebooks * self.bits_per_code + 8


# ---------------------------------------------------------------- the silver groove

def engrave(times, freqs, band: Band):
    """Unrolled heightmap (mm depth below the outer surface) of one contour groove."""
    import numpy as np

    length = band.lead * 2 + (times[-1] - times[0]) * band.mm_per_second
    x = np.arange(0, length, band.grid)
    z = np.arange(0, band.width, band.grid)
    usable = band.width - 2 * band.margin
    x_path = band.lead + (times - times[0]) * band.mm_per_second
    z_path = band.margin + np.clip(log_axis(freqs), 0, 1) * usable
    inside = (x >= x_path[0]) & (x <= x_path[-1])
    centre = np.interp(x, x_path, z_path)
    depth = band.groove_depth * np.exp(-0.5 * ((z[:, None] - centre[None, :]) / band.groove_sigma) ** 2)
    return depth * inside[None, :], {"x0_mm": float(x_path[0]), "length_mm": float(length), "start_s": float(times[0])}


def cast_and_scan(depth, blur_mm: float, band: Band, seed=SEED):
    import numpy as np
    from scipy.ndimage import gaussian_filter

    blurred = gaussian_filter(depth, blur_mm / band.grid, mode="nearest")
    noisy = blurred + np.random.default_rng(seed).normal(0, band.surface_noise, depth.shape)
    return np.round(noisy / band.depth_step) * band.depth_step


def read_groove(depth, geometry, band: Band, duration):
    """Recover a contour from a scanned groove: deepest point per column, subpixel."""
    import numpy as np

    deepest = depth.argmax(axis=0)
    peak = depth[deepest, np.arange(depth.shape[1])]
    valid = peak > 3 * band.surface_noise + band.depth_step
    lower = depth[np.clip(deepest - 1, 0, depth.shape[0] - 1), np.arange(depth.shape[1])]
    upper = depth[np.clip(deepest + 1, 0, depth.shape[0] - 1), np.arange(depth.shape[1])]
    curvature = lower - 2 * peak + upper
    offset = np.where(np.abs(curvature) > 1e-9, 0.5 * (lower - upper) / np.where(np.abs(curvature) > 1e-9, curvature, 1), 0)
    z = (deepest + np.clip(offset, -0.5, 0.5)) * band.grid
    position = np.clip((z - band.margin) / (band.width - 2 * band.margin), 0, 1)
    x = np.arange(depth.shape[1]) * band.grid
    times = geometry["start_s"] + (x - geometry["x0_mm"]) / band.mm_per_second
    times, freqs = times[valid], from_log_axis(position[valid])
    if len(times) < 4:
        return np.zeros(round(duration * RATE), dtype=np.float32), times, freqs
    # Keep the longest run of readable columns; isolated noise picks are not groove.
    breaks = np.where(np.diff(times) > 3 * band.grid / band.mm_per_second)[0]
    runs = np.split(np.arange(len(times)), breaks + 1)
    run = max(runs, key=len)
    return tone(times[run], freqs[run], duration), times[run], freqs[run]


def digital_capacity(blur_mm: float, band: Band):
    """Binary pits that fit on the band's outer surface, with half spent on error correction."""
    pitch = max(0.35, 4 * blur_mm)  # 0.35 mm: Materialise minimum detail for cast silver
    cells = math.floor((band.circumference - 4) / pitch) * math.floor((band.width - 2 * band.margin) / pitch)
    return {"pitch_mm": pitch, "cells": cells, "payload_bits": cells // 2}


def ring_mesh(depth, band: Band, step=0.08):
    """Watertight band with the groove cut into the outer surface; returns (vertices, faces)."""
    import numpy as np
    from scipy.ndimage import zoom

    columns = round(band.circumference / step)
    rows = round(band.width / step) + 1
    surface = np.zeros((rows, columns))
    resampled = zoom(depth, (rows / depth.shape[0], band.grid / step), order=1)
    width = min(resampled.shape[1], columns)
    surface[:, :width] = resampled[:rows, :width]
    theta = np.arange(columns) / columns * 2 * np.pi
    z = np.linspace(0, band.width, rows)
    radius = band.outer_radius - surface
    outer = np.stack([radius * np.cos(theta)[None, :], radius * np.sin(theta)[None, :], np.repeat(z[:, None], columns, 1)], -1).reshape(-1, 3)
    inner = np.stack([np.full((2, columns), band.inner_diameter / 2) * np.cos(theta), np.full((2, columns), band.inner_diameter / 2) * np.sin(theta),
                      np.repeat(np.array([[0.0], [band.width]]), columns, 1)], -1).reshape(-1, 3)
    vertices = np.concatenate([outer, inner])
    o = lambda r, c: r * columns + c % columns
    n = len(outer)
    i = lambda r, c: n + r * columns + c % columns
    faces = []
    for r in range(rows - 1):
        for c in range(columns):
            faces += [(o(r, c), o(r, c + 1), o(r + 1, c + 1)), (o(r, c), o(r + 1, c + 1), o(r + 1, c))]
    for c in range(columns):
        faces += [(i(0, c), i(1, c + 1), i(0, c + 1)), (i(0, c), i(1, c), i(1, c + 1))]
        faces += [(o(0, c), i(0, c), i(0, c + 1)), (o(0, c), i(0, c + 1), o(0, c + 1))]
        faces += [(o(rows - 1, c), o(rows - 1, c + 1), i(1, c + 1)), (o(rows - 1, c), i(1, c + 1), i(1, c))]
    faces = np.asarray(faces)
    # Orient every face away from the solid: radial out, radial in, or along ±z.
    a, b, cc = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    normal = np.cross(b - a, cc - a)
    centre = (a + b + cc) / 3
    radial = centre[:, :2] / np.linalg.norm(centre[:, :2], axis=1, keepdims=True)
    mid = (band.inner_diameter / 2 + band.outer_radius) / 2
    expected = np.zeros_like(normal)
    is_rim = np.isin(centre[:, 2], [0.0, band.width]) & (np.abs(normal[:, 2]) > np.linalg.norm(normal[:, :2], axis=1))
    expected[:, :2] = np.where((np.linalg.norm(centre[:, :2], axis=1) > mid)[:, None], radial, -radial)
    expected[is_rim] = 0
    expected[is_rim, 2] = np.where(centre[is_rim, 2] > band.width / 2, 1, -1)
    flip = (normal * expected).sum(axis=1) < 0
    faces[flip] = faces[flip][:, ::-1]
    return vertices, faces


def write_stl(path: Path, vertices, faces):
    import numpy as np

    triangles = vertices[faces].astype(np.float32)
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    record = np.zeros(len(faces), dtype=[("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])
    record["normal"], record["vertices"] = normals, triangles
    with path.open("wb") as stream:
        stream.write(b"Hardata II contour band, millimetres".ljust(80, b" "))
        stream.write(np.uint32(len(faces)).tobytes())
        stream.write(record.tobytes())


# ---------------------------------------------------------------- listeners

class OpenWhistleListener:
    """Mean-pooled hidden states of all 13 layers; batch size 1, so no padding enters group norm."""
    name = "OpenWhistle Wav2Vec2"
    model_id = ENCODER

    def __init__(self, layout: Layout, device: str):
        from huggingface_hub import HfApi
        from transformers import Wav2Vec2Model

        self.revision = HfApi().model_info(ENCODER, timeout=60).sha
        self.model = Wav2Vec2Model.from_pretrained(ENCODER, revision=self.revision, cache_dir=layout.cache).to(device).eval()
        self.device = device

    def __call__(self, waves):
        import numpy as np
        import torch

        config = self.model.config
        result = np.zeros((len(waves), config.num_hidden_layers + 1, config.hidden_size), dtype=np.float32)
        for k, audio in enumerate(waves):
            audio = np.asarray(audio, dtype=np.float32)
            audio = (audio - audio.mean()) / (audio.std() + 1e-7)
            with torch.inference_mode():
                states = self.model(torch.as_tensor(audio, device=self.device)[None], output_hidden_states=True).hidden_states
            result[k] = torch.stack([state[0].mean(0) for state in states]).float().cpu().numpy()
        return result


class ClapListener:
    """General-audio comparison: 48 kHz, 50 Hz–14 kHz mel frontend, projected embedding."""
    name = "CLAP (general audio)"
    model_id = CLAP

    def __init__(self, layout: Layout, device: str):
        from huggingface_hub import HfApi
        from transformers import ClapModel, ClapProcessor

        self.revision = HfApi().model_info(CLAP, timeout=60).sha
        self.processor = ClapProcessor.from_pretrained(CLAP, revision=self.revision, cache_dir=layout.cache)
        self.model = ClapModel.from_pretrained(CLAP, revision=self.revision, cache_dir=layout.cache, use_safetensors=False).to(device).eval()
        self.device = device

    def __call__(self, waves):
        import numpy as np
        import torch
        from scipy.signal import resample_poly

        divisor = math.gcd(RATE, 48_000)
        result = []
        for audio in waves:
            audio = resample_poly(np.asarray(audio, dtype=np.float32), 48_000 // divisor, RATE // divisor).astype(np.float32)
            inputs = self.processor(audio=audio, sampling_rate=48_000, return_tensors="pt")
            with torch.inference_mode():
                features = self.model.get_audio_features(**{key: value.to(self.device) for key, value in inputs.items()})
            features = getattr(features, "pooler_output", features)
            result.append(features[0].float().cpu().numpy())
        return np.stack(result)[:, None, :]


def fit_probe(train_x, train_y, valid_x, valid_y):
    """Choose layer and regularization on original validation audio only."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    best = None
    for layer in range(train_x.shape[1]):
        for c in (0.01, 0.1, 1.0):
            probe = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=3000))
            probe.fit(train_x[:, layer], train_y)
            score = f1_score(valid_y, probe.predict(valid_x[:, layer]), average="macro")
            if best is None or score > best[0]:
                best = (score, layer, c, probe)
    return {"validation_macro_f1": float(best[0]), "layer": int(best[1]), "C": best[2]}, best[3]


def scores(y_true, y_pred, classes, resamples=1000, seed=SEED):
    import numpy as np
    from sklearn.metrics import confusion_matrix, f1_score

    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    rng = np.random.default_rng(seed)
    boot = [f1_score(y_true[idx], y_pred[idx], average="macro", labels=classes, zero_division=0)
            for idx in (rng.integers(0, len(y_true), len(y_true)) for _ in range(resamples))]
    return {"accuracy": float((y_true == y_pred).mean()), "macro_f1": float(f1_score(y_true, y_pred, average="macro", labels=classes, zero_division=0)),
            "macro_f1_ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "confusion": confusion_matrix(y_true, y_pred, labels=classes).tolist()}


def paired_difference(y_true, a, b, resamples=2000, seed=SEED):
    import numpy as np
    from sklearn.metrics import f1_score

    y_true, a, b = map(np.asarray, (y_true, a, b))
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(resamples):
        idx = rng.integers(0, len(y_true), len(y_true))
        diffs.append(f1_score(y_true[idx], a[idx], average="macro", zero_division=0) - f1_score(y_true[idx], b[idx], average="macro", zero_division=0))
    return {"difference": float(f1_score(y_true, a, average="macro") - f1_score(y_true, b, average="macro")),
            "ci95": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]}


# ---------------------------------------------------------------- experiment

CONDITIONS = [
    # family, key, parameters
    ("original", "original", {}),
    ("contour", "contour-8x8", {"points": 8, "bits": 8}),
    ("contour", "contour-16x8", {"points": 16, "bits": 8}),
    ("contour", "contour-32x4", {"points": 32, "bits": 4}),
    ("contour", "contour-32x8", {"points": 32, "bits": 8}),
    ("contour", "contour-64x8", {"points": 64, "bits": 8}),
    ("contour", "contour-128x10", {"points": 128, "bits": 10}),
    ("contour + sea", "contour-32x8-sea", {"points": 32, "bits": 8, "noise_bed": True}),
    ("contour + sea", "contour-128x10-sea", {"points": 128, "bits": 10, "noise_bed": True}),
    ("control", "reversed-32x8", {"points": 32, "bits": 8, "reverse": True}),
    ("control", "flat-tone", {}),
    ("relief", "relief-8x8x2", {"frames": 8, "bands": 8, "depth": 2}),
    ("relief", "relief-16x16x2", {"frames": 16, "bands": 16, "depth": 2}),
    ("relief", "relief-32x24x3", {"frames": 32, "bands": 24, "depth": 3}),
    ("relief", "relief-64x48x4", {"frames": 64, "bands": 48, "depth": 4}),
    ("amplitude (Hardata 2021)", "amplitude-32x3", {"segments": 32}),
    ("DAC codec", "dac-1", {"codebooks": 1}),
    ("DAC codec", "dac-2", {"codebooks": 2}),
    ("DAC codec", "dac-4", {"codebooks": 4}),
    ("DAC codec", "dac-9", {"codebooks": 9}),
]


def render(clip: Clip, key: str, params: dict, codec, bed):
    """Decoded waveform and inscribed bits for one condition."""
    if key == "original":
        return clip.audio, 16 * len(clip.audio)
    if key.startswith("contour") or key.startswith("reversed"):
        payload = encode_contour(clip, params["points"], params["bits"])
        audio = decode_contour(payload, clip.duration, reverse=params.get("reverse", False))
        if params.get("noise_bed"):
            audio = add_noise_bed(audio, bed)
        return audio, payload["bits"]
    if key == "flat-tone":
        return flat_tone(clip, clip.duration)
    if key.startswith("relief"):
        return relief(clip, params["frames"], params["bands"], params["depth"])
    if key.startswith("amplitude"):
        return amplitude_only(clip, params["segments"])
    if key.startswith("dac"):
        return codec(clip.audio, params["codebooks"])
    raise ValueError(key)


def example_selection(test, label_names):
    """One clip per type: the whistle closest to its type's median duration (no look at predictions)."""
    import numpy as np

    chosen = []
    for label in range(len(label_names)):
        group = [clip for clip in test if clip.label == label]
        median = float(np.median([clip.duration for clip in group]))
        chosen.append(min(group, key=lambda clip: (abs(clip.duration - median), clip.id)).id)
    return chosen


def run(layout: Layout, config: str = "balanced", device: str = "auto", clap: bool = True, limit: int | None = None):
    import numpy as np
    import soundfile as sf

    from .audio import device_name, listening_copy, release_models

    device = device_name(device)
    started = now()
    manifest = read_json(source_directory(layout, config) / "sources.json")
    names = manifest["label_names"]
    classes = list(range(len(names)))
    train = [c for c in load_clips(layout, config, "train") if contour(c) is not None]
    valid = [c for c in load_clips(layout, config, "validation") if contour(c) is not None]
    test_all = load_clips(layout, config, "test")
    test = [c for c in test_all if contour(c) is not None]
    excluded = len(test_all) - len(test)
    if limit:
        per_class = lambda clips, n: [c for label in classes for c in [c for c in clips if c.label == label][:n]]
        train, valid, test = per_class(train, limit), per_class(valid, max(2, limit // 2)), per_class(test, max(2, limit // 2))
    print(f"Clips with usable contours · train {len(train)} · validation {len(valid)} · test {len(test)}", flush=True)

    out = layout.output / "inscription"
    interim = layout.interim / "inscription"
    for directory in (out / "audio", out / "bands", interim):
        directory.mkdir(parents=True, exist_ok=True)
    bed = noise_bed(train)
    codec = Codec(layout, device)
    band = Band()
    examples = example_selection(test, names)

    waves, keys, bits = {}, {}, {}
    for family, key, params in CONDITIONS:
        rendered = [render(clip, key, params, codec, bed) for clip in test]
        waves[key] = [np.asarray(audio, dtype=np.float32) for audio, _ in rendered]
        bits[key] = [int(b) for _, b in rendered]
        print(f"{key}: median {np.median(bits[key]):.0f} bits", flush=True)
    grooves = {}
    for blur in BLURS_MM:
        key = f"groove-{blur:g}mm"
        rendered = []
        for clip in test:
            times, freqs = contour(clip)
            depth, geometry = engrave(times, freqs, band)
            audio, *_ = read_groove(cast_and_scan(depth, blur, band), geometry, band, clip.duration)
            rendered.append(audio)
        waves[key] = rendered
        bits[key] = [digital_capacity(blur, band)["payload_bits"]] * len(test)
        grooves[key] = {"blur_mm": blur, **digital_capacity(blur, band)}
        print(f"{key}: decoded", flush=True)
    codec_revision = codec.revision
    del codec
    release_models()

    listeners = {}
    for listener_class in [OpenWhistleListener] + ([ClapListener] if clap else []):
        function = listener_class(layout, device)
        listener, revision = function.name, function.revision
        train_x, valid_x = function([c.audio for c in train]), function([c.audio for c in valid])
        selection, probe = fit_probe(train_x, [c.label for c in train], valid_x, [c.label for c in valid])
        layer = selection["layer"]
        results, predictions, probabilities = {}, {}, {}
        for key in waves:
            x = function(waves[key])
            pred = probe.predict(x[:, layer])
            prob = probe.predict_proba(x[:, layer])
            predictions[key] = pred.tolist()
            probabilities[key] = prob
            results[key] = scores([c.label for c in test], pred, classes)
            print(f"{listener} · {key}: macro-F1 {results[key]['macro_f1']:.3f}", flush=True)
        del function
        y = [c.label for c in test]
        comparisons = {
            "contour-32x8 vs relief-16x16x2": paired_difference(y, predictions["contour-32x8"], predictions["relief-16x16x2"]),
            "contour-32x8 vs dac-1": paired_difference(y, predictions["contour-32x8"], predictions["dac-1"]),
            "contour-32x8 vs reversed-32x8": paired_difference(y, predictions["contour-32x8"], predictions["reversed-32x8"]),
            "contour-32x8 vs flat-tone": paired_difference(y, predictions["contour-32x8"], predictions["flat-tone"]),
            "groove-0.1mm vs contour-128x10": paired_difference(y, predictions["groove-0.1mm"], predictions["contour-128x10"]),
        }
        listeners[listener] = {"model_id": listener_class.model_id, "model_revision": revision, "probe": selection, "results": results, "comparisons": comparisons,
                               "predictions": predictions,
                               "example_probabilities": {key: {cid: probabilities[key][i].round(4).tolist() for i, cid in enumerate(c.id for c in test) if cid in examples} for key in waves}}
        release_models()

    # Playable examples, band geometry and mesh files for one whistle per type.
    rows = []
    index = {clip.id: i for i, clip in enumerate(test)}
    for clip_id in examples:
        clip, i = test[index[clip_id]], index[clip_id]
        stem = clip_id
        original = out / "audio" / f"{stem}-original.wav"
        sf.write(original, clip.audio, RATE, subtype="PCM_16")
        files = {"original": original.name, "original_playback": f"{stem}-original-listen.wav"}
        playback = {"original": listening_copy(original, out / "audio" / files["original_playback"])}
        for key in waves:
            if key == "original":
                continue
            path = out / "audio" / f"{stem}-{key}.wav"
            sf.write(path, np.clip(waves[key][i], -1, 1), RATE, subtype="PCM_16")
            listen = out / "audio" / f"{stem}-{key}-listen.wav"
            playback[key] = listening_copy(path, listen)
            files[key] = listen.name
        times, freqs = contour(clip)
        depth, geometry = engrave(times, freqs, band)
        scanned = cast_and_scan(depth, 0.1, band)
        _, read_t, read_f = read_groove(scanned, geometry, band, clip.duration)
        vertices, faces = ring_mesh(scanned, band)
        mesh = out / "bands" / f"{stem}.stl"
        write_stl(mesh, vertices, faces)
        np.savez_compressed(interim / f"{stem}-groove.npz", depth=depth.astype(np.float32), scanned=scanned.astype(np.float32))
        rows.append({"id": clip_id, "label": clip.name, "session": clip.session, "duration_s": clip.duration,
                     "f0_time": times.tolist(), "f0_hz": freqs.tolist(), "groove_read_time": read_t[::10].tolist(), "groove_read_hz": read_f[::10].tolist(),
                     "audio": files, "playback": playback, "mesh": f"bands/{mesh.name}", "mesh_triangles": int(len(faces)),
                     "groove_geometry": geometry, "bits": {key: bits[key][i] for key in bits}})
    report = {
        "created_at_utc": now(), "started_at_utc": started, "predictions": PREDICTIONS,
        "dataset": {key: manifest[key] for key in ("dataset", "config", "parquet_revision", "main_revision", "label_names", "license_note", "splits_note")},
        "dataset_files": manifest["files"],
        "counts": {"train": len(train), "validation": len(valid), "test": len(test), "test_excluded_without_contour": excluded},
        "inclusion": f"Clips with upstream f0_ok and at least four F0 points with confidence ≥ {MIN_CONFIDENCE} between {F_LOW:.0f} Hz and {F_HIGH:.0f} Hz; identical clips in every condition.",
        "codec": {"id": CODEC, "revision": codec_revision, "note": "Generic 44.1 kHz neural codec (the DoLittle tokenizer family); not trained on cetaceans. Input normalized to -20 dBFS RMS and restored with one 8-bit gain, counted in its bits."},
        "device": device, "chance_macro_f1_note": "Uniform guessing gives about 1/6 accuracy; macro-F1 of a constant guess is lower.",
        "band": asdict(band), "blurs_mm": list(BLURS_MM), "grooves": grooves,
        "conditions": [{"family": family, "key": key, "parameters": params, "median_bits": float(np.median(bits[key]))} for family, key, params in CONDITIONS]
        + [{"family": "silver groove (simulated)", "key": key, "parameters": grooves[key], "median_bits": float(np.median(bits[key]))} for key in grooves],
        "bits": {key: bits[key] for key in bits}, "test_ids": [c.id for c in test], "test_labels": [c.label for c in test],
        "listeners": listeners, "examples": rows,
        "noise_bed": {"description": "Mean training-clip power spectrum with ±700 Hz around F0, 2F0 and 3F0 masked; shared by all clips, so it carries no per-whistle bits.", "snr_db": 10},
        "notes": [
            "Bits count only the per-whistle inscription. Decoder knowledge (frequency axis, synthesis rule, noise bed, codec weights) is shared and not counted.",
            "Groove conditions decode an analog contour; their 'bits' column is the binary-pit capacity at the same casting resolution, for comparison only.",
            "Probe accuracy measures acoustic type separation by one encoder. It does not establish what dolphins perceive; playback studies would.",
            "SW labels are whistle types associated with named dolphins, not verified callers.",
        ],
    }
    write_json(out / "results.json", report)
    return out / "results.json"


MATCHED = ("contour-8x8", "contour-32x8", "contour-128x10", "dac-4")


def matched(layout: Layout, config: str = "balanced", device: str = "auto", keys=MATCHED):
    """Post-hoc check, not a registered prediction: train and test the probe on decoded audio.

    If a probe trained on decoded whistles recovers most of the original score, the
    gap in the main run is domain shift (tones are not recordings), not lost type information.
    """
    import numpy as np

    from .audio import device_name, release_models

    device = device_name(device)
    names = read_json(source_directory(layout, config) / "sources.json")["label_names"]
    classes = list(range(len(names)))
    splits = {split: [c for c in load_clips(layout, config, split) if contour(c) is not None] for split in ("train", "validation", "test")}
    params = {key: p for _, key, p in CONDITIONS}
    codec = Codec(layout, device) if any(key.startswith("dac") for key in keys) else None
    decoded = {key: {split: [np.asarray(render(c, key, params[key], codec, None)[0], dtype=np.float32) for c in clips]
                     for split, clips in splits.items()} for key in keys}
    del codec
    release_models()
    listener = OpenWhistleListener(layout, device)
    report = {"created_at_utc": now(), "listener": listener.name, "model_revision": listener.revision,
              "note": "Exploratory, added after the registered predictions; probe trained, tuned and tested on decoded audio of the same condition.",
              "results": {}}
    for key in keys:
        x = {split: listener(decoded[key][split]) for split in splits}
        y = {split: [c.label for c in clips] for split, clips in splits.items()}
        selection, probe = fit_probe(x["train"], y["train"], x["validation"], y["validation"])
        prediction = probe.predict(x["test"][:, selection["layer"]])
        report["results"][key] = {"probe": selection, **scores(y["test"], prediction, classes)}
        print(f"matched {key}: macro-F1 {report['results'][key]['macro_f1']:.3f}", flush=True)
    write_json(layout.output / "inscription" / "matched.json", report)
    return layout.output / "inscription" / "matched.json"


# ---------------------------------------------------------------- commands

DataOption = Annotated[Path, typer.Option(help="Root containing input/, interim/, output/.")]


@app.command("fetch")
def fetch_command(data_dir: DataOption = DEFAULT_DATA, config: str = "balanced"):
    """Download pinned OpenWhistle parquet shards (audio, labels, F0) for train/validation/test."""
    print(fetch(Layout(data_dir), config))


@app.command("run")
def run_command(
    data_dir: DataOption = DEFAULT_DATA,
    config: str = "balanced",
    device: Annotated[str, typer.Option(help="auto, cuda, or cpu.")] = "auto",
    clap: Annotated[bool, typer.Option(help="Also evaluate a general-audio CLAP probe.")] = True,
    limit: Annotated[int | None, typer.Option(min=6, help="Smoke test on a few clips.")] = None,
):
    """Encode, decode, engrave, probe; write results.json, audio, STL bands and the gallery."""
    path = run(Layout(data_dir), config, device, clap, limit)
    from .inscription_gallery import write_gallery

    write_gallery(path)


@app.command("matched")
def matched_command(
    data_dir: DataOption = DEFAULT_DATA,
    config: str = "balanced",
    device: Annotated[str, typer.Option(help="auto, cuda, or cpu.")] = "auto",
):
    """Exploratory: probe trained on decoded audio, separating domain shift from lost information."""
    print(matched(Layout(data_dir), config, device))
    from .inscription_gallery import write_gallery

    write_gallery(Layout(data_dir).output / "inscription" / "results.json")


@app.command("gallery")
def gallery_command(data_dir: DataOption = DEFAULT_DATA):
    """Rebuild the input → schema → output gallery from results.json."""
    from .inscription_gallery import write_gallery

    write_gallery(Layout(data_dir).output / "inscription" / "results.json")
