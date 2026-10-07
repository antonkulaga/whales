"""Music that follows the animal phrase (docs/2026-art-ideas.md, section 1).

Input: real recordings, one species at a time: humpback song with annotated
units, dolphin whistle sequences, sperm-whale codas.
Schema: measured events and contours, rendered as a guide in a declared
register and instrument, plus a perturbed twin that mirrors event order and
inverts each contour with every other setting fixed.
Output: a deterministic response (no model) and ACE-Step 1.5 generations under
one caption and seed: prompt only, raw recording, guide and perturbed guide.

Following is judged by event timing and pitch-class agreement with the
output's own guide against swapped and perturbed guides, never by a global
style score. Pleasing music is not evidence of what a whale would prefer.
"""

import math
from pathlib import Path
import shutil
import subprocess
import time
from typing import Annotated
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

import typer

from .data import DEFAULT_DATA, Layout, ROOT, digest, get_json, now, read_json, write_json

CONFIG = ROOT / "resources" / "follow-music.json"
RUNNER = Path(__file__).with_name("follow_ace.py")
ACE_DIR = Path("tools") / "ACE-Step-1.5"  # under data/interim; it keeps its own uv environment
CONDITIONS = ("prompt", "raw", "guide", "perturbed", "cover-raw", "cover-guide", "cover-perturbed")

# Written before the first evaluation run; the page compares results against these.
PREDICTIONS = {
    "registered_at_utc": "2026-10-07T16:19:55+00:00",
    "P1": "The deterministic response follows its guide: timing z ≥ 3 against its own guide for every source, and it scores higher against the perturbed guide when rendered from it.",
    "P2": "Prompt-only ACE-Step output does not follow any guide: timing |z| < 2 against its species' guides.",
    "P3": "ACE-Step lego conditioned on the measured guide follows event timing better than lego on the raw recording (higher timing z) for at least two of three species.",
    "P4": "Guide-conditioned output ranks its own guide first among same-species guides and perturbed twins for at least half of the sources.",
    "P5": "Output conditioned on the perturbed guide scores higher against the perturbed guide than against the original for at least half of the sources.",
    "amended_at_utc": "2026-10-07T16:32:00+00:00",
    "amendment": "P6 and P7 were added after one lego trial on humpback-a (guide timing z +0.2, prompt-only +1.1) and before any cover output existed.",
    "P6": "ACE-Step cover of the measured guide follows event timing (timing z ≥ 3) for at least four of six sources.",
    "P7": "Cover of the perturbed guide scores higher against the perturbed guide than against the original for at least four of six sources.",
}


def load_config(path: Path = CONFIG):
    config = read_json(path)
    config["config_sha256"] = digest(path)
    return config


def directories(layout: Layout):
    return layout.interim / "follow", layout.output / "follow"


# --- Sources --------------------------------------------------------------------------------

def download(url: str, path: Path, sha256: str | None = None):
    if path.exists() and (sha256 is None or digest(path) == sha256):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    try:
        with urlopen(url, timeout=300) as response, partial.open("wb") as stream:
            shutil.copyfileobj(response, stream)
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)
    if sha256 and digest(path) != sha256:
        raise ValueError(f"{path} does not match the recorded sha256; the remote file changed")
    print(f"Downloaded {path.name}: {path.stat().st_size:,} bytes", flush=True)
    return path


def study_ids(config: dict):
    """Sources in the registered study; the others serve the sound map only."""
    return {s["id"] for s in config["sources"] if s.get("study", True)}


def fetch(layout: Layout, config: dict):
    """Recordings named in the config: the humpback file, DSWP coda rows and DCLDE windows."""
    from huggingface_hub import HfApi

    from .follow_dclde import fetch_dclde
    from .follow_pangaea import fetch_pangaea

    fetch_dclde(layout, config)
    fetch_pangaea(layout, config)

    for relative, item in config["downloads"].items():
        download(item["url"], layout.input / relative, item.get("sha256"))
    for dataset in sorted({s["dataset"] for s in config["sources"] if s["kind"] == "assembled"}):
        rows = sorted({row for s in config["sources"] if s.get("dataset") == dataset for row in s["rows"]})
        directory = layout.input / "dswp"
        manifest = directory / "sources.json"
        known = {item["row_index"]: item for item in read_json(manifest)["clips"]} if manifest.exists() else {}
        info = HfApi().dataset_info(dataset, timeout=60)
        url = "https://datasets-server.huggingface.co/rows?" + urlencode(
            dict(dataset=dataset, config="default", split="train", offset=rows[0], length=rows[-1] - rows[0] + 1))
        items = {item["row_idx"]: item for item in get_json(url)["rows"]}
        clips = []
        for row in rows:
            path = directory / f"dswp-{row:04d}.wav"
            if row in known and path.exists() and digest(path) == known[row]["sha256"]:
                clips.append(known[row])
                continue
            audio_url = items[row]["row"]["audio"][0]["src"]
            download(audio_url, path)
            clips.append({"row_index": row, "path": str(path.resolve()), "sha256": digest(path), "dataset": dataset,
                          "split": "train", "hub_revision_at_inspection": info.sha,
                          "declared_license": (info.card_data or {}).get("license"), "viewer_rows_url": url,
                          "viewer_asset_url": urlsplit(audio_url)._replace(query="").geturl(), "fetched_at_utc": now()})
        write_json(manifest, {"clips": clips, "note": "Live Viewer waveforms; the hash identifies the analyzed bytes."})


def read_excerpt(path: Path, start_s: float, duration_s: float):
    import soundfile as sf

    with sf.SoundFile(path) as stream:
        rate = stream.samplerate
        stream.seek(round(start_s * rate))
        samples = stream.read(round(duration_s * rate), dtype="float64", always_2d=True)
    if len(samples) < round(duration_s * rate) - 1:
        raise ValueError(f"{path} is shorter than {start_s + duration_s:.1f} s")
    return samples.mean(axis=1), rate


def read_units(path: Path, start_s: float, duration_s: float):
    """Raven selection table → units fully inside the excerpt, timed from its start."""
    lines = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    header, units = lines[0], []
    column = {name: header.index(name) for name in ("Selection", "Begin Time (s)", "End Time (s)", "Low Freq (Hz)", "High Freq (Hz)", "Call Type")}
    for row in lines[1:]:
        begin, end = float(row[column["Begin Time (s)"]]), float(row[column["End Time (s)"]])
        if begin >= start_s and end <= start_s + duration_s:
            units.append({"selection": int(row[column["Selection"]]), "start_s": begin - start_s, "end_s": end - start_s,
                          "low_hz": float(row[column["Low Freq (Hz)"]]), "high_hz": float(row[column["High Freq (Hz)"]]),
                          "label": row[column["Call Type"]]})
    return units


def assemble(layout: Layout, source: dict, rate: int = 48000):
    """Separate coda clips in sequence, each resampled to one rate; the silences between them are ours."""
    import numpy as np

    from .brush import read_audio

    pieces, clips, clock = [], [], 0.0
    for row in source["rows"]:
        path = layout.input / "dswp" / f"dswp-{row:04d}.wav"
        clip, clip_rate = read_audio(path)
        clip = resample(clip, clip_rate, rate)
        fade = np.minimum(1, np.minimum(np.arange(len(clip)), np.arange(len(clip))[::-1]) / (.005 * rate))
        pieces += [(clip - clip.mean()) * fade, np.zeros(round(source["gap_s"] * rate))]
        clips.append({"row_index": row, "native_rate": clip_rate, "start_s": round(clock, 6), "end_s": round(clock + len(clip) / rate, 6), "sha256": digest(path)})
        clock += len(clip) / rate + source["gap_s"]
    return np.concatenate(pieces[:-1]), rate, clips


def load_source(layout: Layout, source: dict):
    if source["kind"] == "dclde":
        from .follow_dclde import load_dclde

        return load_dclde(layout, source)
    if source["kind"] == "pangaea":
        from .follow_pangaea import load_pangaea

        return load_pangaea(layout, source)
    if source["kind"] == "assembled":
        waveform, rate, clips = assemble(layout, source)
        return waveform, rate, {"clips": clips, "gap_s": source["gap_s"], "dataset": source["dataset"]}, None
    path = layout.input / source["file"]
    waveform, rate = read_excerpt(path, source["start_s"], source["duration_s"])
    units = read_units(layout.input / source["annotations"], source["start_s"], source["duration_s"]) if source.get("annotations") else None
    return waveform, rate, {"file": source["file"], "sha256": digest(path), "start_s": source["start_s"]}, units


# --- Measurement ------------------------------------------------------------------------------

def analysis_config(species: dict):
    from .brush import load_config as brush_config

    return {"analysis": brush_config()["analysis"] | species["analysis"]}


def spectra(signal, n_fft: int, hop: int):
    import numpy as np

    windows = np.lib.stride_tricks.sliding_window_view(signal, n_fft)[::hop]
    return np.abs(np.fft.rfft(windows * np.hanning(n_fft), axis=1))


def noise_floor(waveform, settings: dict):
    """Median magnitude per frequency over the whole excerpt: the steady background a call sits on."""
    import numpy as np

    return np.median(spectra(waveform, settings["n_fft"], settings["hop"]), axis=0) + 1e-12


def f0_track(waveform, rate: int, start_s: float, end_s: float, settings: dict, floor=None, band=None):
    """Subharmonic summation inside one unit: the F0 whose weighted harmonics carry the most energy.

    With `floor`, spectra are whitened first so steady noise cannot win; with `band` (an annotated call's
    low and high frequency), candidates stay inside the call's box.
    """
    import numpy as np
    from scipy.signal import medfilt

    n_fft, hop = settings["n_fft"], settings["hop"]
    segment = waveform[max(0, round(start_s * rate) - n_fft // 2):round(end_s * rate) + n_fft // 2]
    if len(segment) < n_fft + hop:
        return None
    magnitude = spectra(segment, n_fft, hop)
    if floor is not None:
        magnitude = magnitude / floor
    frequencies = np.fft.rfftfreq(n_fft, 1 / rate)
    low, high = settings["range_hz"]
    if band and band[0] and band[1] and min(high, band[1]) > max(low, .9 * band[0]) * 1.2:
        low, high = max(low, .9 * band[0]), min(high, band[1])
    candidates = low * 2 ** (np.arange(int(12 * 8 * np.log2(high / low)) + 1) / 96)
    salience = sum(settings["decay"] ** (h - 1) * np.stack([np.interp(h * candidates, frequencies, row) for row in magnitude])
                   for h in range(1, settings["harmonics"] + 1))
    log2f = np.log2(candidates[np.argmax(salience, axis=1)])
    kernel = min(settings["median_frames"], len(log2f) // 2 * 2 - 1)
    if kernel >= 3:
        log2f = medfilt(log2f, kernel)
    times = start_s + np.arange(len(log2f)) * hop / rate
    keep = times <= end_s
    return times[keep].tolist(), (2 ** log2f[keep]).tolist()


def measure_events(waveform, rate: int, species: dict, units: list[dict] | None = None, f0: dict | None = None,
                   label: str = "whistle"):
    """Tonal events with contours, or click events grouped into codas, measured from the waveform.

    Unlabelled tonal events are named `label` + " (detected)": the source's call name, or "whistle".
    """
    import numpy as np

    from .brush import measure

    measured = measure(waveform, rate, analysis_config(species))
    segments = measured["segments"]
    if species["material"] == "clicks":
        events = [{"kind": "click", "time_s": t, "group": g, "origin": "measured"}
                  for g, segment in enumerate(s for s in segments if s["kind"] == "clicks") for t in segment["time_s"]]
        return events, {"isolated_clicks": len(measured["isolated_clicks_s"]), "codas": len({e["group"] for e in events})}
    tonal = [s for s in segments if s["kind"] == "tonal"]
    if units is None:
        events = [{"kind": "tonal", "start_s": s["time_s"][0], "end_s": s["time_s"][-1] + measured["frame_hop_s"],
                   "time_s": s["time_s"], "hz": s["hz"], "label": f"{label} (detected)", "origin": "measured",
                   "contour": "measured ridge"} for s in tonal]
        return events, {"tonal_segments": len(tonal)}
    events, settings = [], f0 or species.get("f0", {})
    floor = noise_floor(waveform, settings) if settings.get("whiten") else None
    for unit in units:
        if unit.get("contour"):  # an analyst traced this whistle; its contour is the measurement
            contour = unit["contour"]
            events.append({"kind": "tonal", "start_s": unit["start_s"], "end_s": unit["end_s"], "time_s": contour["time_s"], "hz": contour["hz"],
                           "label": unit["label"], "origin": f"annotation {unit['selection']}", "contour": "analyst-traced contour (silbido)"}
                          | ({"cut": unit["cut"]} if unit.get("cut") else {}))
            continue
        band = (unit.get("low_hz"), unit.get("high_hz")) if settings.get("annotation_band") else None
        track = f0_track(waveform, rate, unit["start_s"], unit["end_s"], settings, floor, band)
        if track is None:
            continue
        events.append({"kind": "tonal", "start_s": unit["start_s"], "end_s": unit["end_s"], "time_s": track[0], "hz": track[1],
                       "label": unit["label"], "origin": f"annotation {unit['selection']}",
                       "contour": "subharmonic-summation F0 inside the annotated unit"} | ({"cut": unit["cut"]} if unit.get("cut") else {}))
    return events, {"annotated_units": len(units), "tonal_segments_in_excerpt": len(tonal)}


def register_shift(events: list[dict], target_hz: float):
    """Whole octaves that move the median measured frequency nearest the target register."""
    import numpy as np

    hz = [f for event in events if event["kind"] == "tonal" for f in event["hz"]]
    return int(round(math.log2(target_hz / float(np.median(hz))))) if hz else 0


def perturb(events: list[dict], duration: float):
    """Mirror event order in time and invert each contour around its median; nothing else changes."""
    import numpy as np

    mirrored = []
    for event in events:
        if event["kind"] == "click":
            mirrored.append(event | {"time_s": duration - event["time_s"]})
            continue
        start = duration - event["end_s"]
        offset = start - event["start_s"]
        octaves = np.log2(event["hz"])
        center = float(np.median(octaves))
        mirrored.append(event | {"start_s": start, "end_s": start + event["end_s"] - event["start_s"],
                                 "time_s": [t + offset for t in event["time_s"]], "hz": (2 ** (2 * center - octaves)).tolist()})
    return sorted(mirrored, key=lambda e: e.get("start_s", e.get("time_s")))


def onsets(events: list[dict]):
    """Reference event times: tonal starts and every click. A call cut at its start began before the window."""
    return sorted(e["start_s"] if e["kind"] == "tonal" else e["time_s"] for e in events if e.get("cut") not in ("start", "both"))


# --- Rendering ------------------------------------------------------------------------------

def contour_at(event: dict, grid):
    import numpy as np

    return np.interp(grid, event["time_s"], event["hz"])  # flat beyond the measured frames


def additive(frequency, harmonics, rate: int):
    import numpy as np

    phase = 2 * np.pi * np.cumsum(frequency) / rate
    out = sum(a * np.sin(k * phase) * (k * frequency < .45 * rate) for k, a in enumerate(harmonics, 1))
    return out / sum(harmonics)


def ramp(n: int, rate: int, attack_s: float, release_s: float):
    import numpy as np

    index = np.arange(n)
    return np.minimum(1, np.minimum(index / max(1, attack_s * rate), (n - 1 - index) / max(1, release_s * rate)))


def strike(rate: int, hz: float, partials, levels, decay_s: float):
    import numpy as np

    t = np.arange(round(6 * decay_s * rate)) / rate
    attack = np.minimum(1, t / .001)
    return attack * sum(level * np.sin(2 * np.pi * hz * ratio * t) * np.exp(-t * ratio / decay_s)
                        for ratio, level in zip(partials, levels)) / sum(levels)


def place(out, sound, start_s: float, rate: int):
    i = round(start_s * rate)
    if 0 <= i < len(out):
        n = min(len(sound), len(out) - i)
        out[i:i + n] += sound[:n]


def render_guide(events: list[dict], duration: float, rate: int, instrument: dict, shift: int):
    """The measured events as an instrument: contour × 2^shift, or one mallet strike per click."""
    import numpy as np

    out = np.zeros(round(duration * rate))
    first = {}
    for event in events:
        if event["kind"] == "click":
            first.setdefault(event["group"], event["time_s"])
            first[event["group"]] = min(first[event["group"]], event["time_s"])
    for event in events:
        if event["kind"] == "click":
            accent = instrument["accent"] if event["time_s"] == first[event["group"]] else 1.0
            sound = strike(rate, instrument["mallet_hz"], instrument["partials"], instrument["partial_levels"], instrument["decay_s"])
            place(out, instrument["level"] * accent / instrument["accent"] * sound, event["time_s"], rate)
            continue
        i0, i1 = round(event["start_s"] * rate), min(len(out), round(event["end_s"] * rate))
        if i1 - i0 < 2:
            continue
        frequency = contour_at(event, np.arange(i0, i1) / rate) * 2.0 ** shift
        out[i0:i1] += instrument["level"] * ramp(i1 - i0, rate, instrument["attack_s"], instrument["release_s"]) * additive(frequency, instrument["harmonics"], rate)
    return out


def midi_of(hz: float):
    return round(69 + 12 * math.log2(hz / 440))


def hz_of(midi: float):
    return 440 * 2 ** ((midi - 69) / 12)


def respond(events: list[dict], duration: float, rate: int, shift: int, rules: dict):
    """Deterministic answer: an open-fifth pad and bass at each tonal onset; drum and ticks on each coda."""
    import numpy as np

    out = np.zeros(round(duration * rate) + round(rate))
    tonal, clicks = rules["tonal"], rules["clicks"]
    for event in events:
        if event["kind"] == "tonal":
            root = midi_of(float(contour_at(event, [event["start_s"] + .03])[0]) * 2.0 ** shift)
            n = round((event["end_s"] - event["start_s"] + tonal["pad_release_s"]) * rate)
            envelope = ramp(n, rate, tonal["pad_attack_s"], tonal["pad_release_s"])
            for semitones in tonal["chord_semitones"]:
                pad = additive(np.full(n, hz_of(root + semitones)), tonal["pad_harmonics"], rate)
                place(out, tonal["pad_level"] / len(tonal["chord_semitones"]) * envelope * pad, event["start_s"], rate)
            place(out, tonal["bass_level"] * strike(rate, hz_of(root + tonal["bass_semitones"]), [1, 2], [1, .3], tonal["bass_decay_s"]), event["start_s"], rate)
    groups = {}
    for event in events:
        if event["kind"] == "click":
            groups.setdefault(event["group"], []).append(event["time_s"])
    for times in groups.values():
        t = np.arange(round(6 * clicks["drum_decay_s"] * rate)) / rate
        high, low = clicks["drum_hz"]
        sweep = low + (high - low) * np.exp(-t / .03)
        drum = np.sin(2 * np.pi * np.cumsum(sweep) / rate) * np.exp(-t / clicks["drum_decay_s"])
        place(out, clicks["drum_level"] * drum, min(times), rate)
        for moment in times:
            place(out, clicks["tick_level"] * strike(rate, clicks["tick_hz"], [1], [1], clicks["tick_decay_s"]), moment, rate)
    return out[:round(duration * rate)]


def write_wav(path: Path, samples, rate: int):
    import numpy as np
    import soundfile as sf

    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if not np.isfinite(samples).all():
        raise ValueError(f"Non-finite audio for {path}")
    if peak > .99:
        raise ValueError(f"{path.name} would clip (peak {peak:.2f}); lower the declared levels")
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, samples, rate, subtype="PCM_16")
    return path


def resample(samples, rate: int, target: int):
    from scipy.signal import resample_poly

    divisor = math.gcd(rate, target)
    return samples if rate == target else resample_poly(samples, target // divisor, rate // divisor)


def prepare(layout: Layout, config: dict, only: list[str] | None = None):
    """Measure every source and write animal, guide, perturbed and response stems plus a manifest."""
    import numpy as np

    interim, output = directories(layout)
    rate = config["sample_rate"]
    manifest_path = interim / "prepared.json"
    previous = {item["id"]: item for item in read_json(manifest_path)["sources"]} if manifest_path.exists() else {}
    for source in config["sources"]:
        if only and source["id"] not in only:
            continue
        species = config["species"][source["species"]]
        waveform, native_rate, provenance, units = load_source(layout, source)
        duration = len(waveform) / native_rate
        f0 = species["f0"] | source["f0"] if "f0" in species and "f0" in source else species.get("f0")
        events, counts = measure_events(waveform, native_rate, species, units, f0, source.get("call_label", "whistle"))
        if not events:
            raise ValueError(f"{source['id']}: nothing was measured; check the analysis band")
        shift = register_shift(events, species["target_median_hz"]) if species["material"] == "tonal" else 0
        mirrored = perturb(events, duration)
        folder = output / source["id"]
        animal = resample(waveform - waveform.mean(), native_rate, rate)
        peak = float(np.max(np.abs(animal)))
        gain = .8 / peak
        # Dense whistle choruses stack chords past full scale; one shared gain keeps the twin responses comparable.
        answers = [respond(e, duration, rate, shift, config["response"]) for e in (events, mirrored)]
        response_gain = min(1.0, .95 / max(1e-12, *(float(np.max(np.abs(a))) for a in answers)))
        stems = {
            "animal": write_wav(folder / "animal.wav", animal * gain, rate),
            "guide": write_wav(folder / "guide.wav", render_guide(events, duration, rate, species["instrument"], shift), rate),
            "perturbed": write_wav(folder / "perturbed.wav", render_guide(mirrored, duration, rate, species["instrument"], shift), rate),
            "response": write_wav(folder / "response.wav", answers[0] * response_gain, rate),
            "response-perturbed": write_wav(folder / "response-perturbed.wav", answers[1] * response_gain, rate),
        }
        previous[source["id"]] = {
            "id": source["id"], "species": source["species"], "title": source["title"], "note": source["note"],
            "duration_s": duration, "native_rate": native_rate, "provenance": provenance, "units": units,
            "events": events, "perturbed_events": mirrored, "onsets_s": onsets(events), "perturbed_onsets_s": onsets(mirrored),
            "counts": counts, "register_shift_octaves": shift, "instrument": species["instrument"],
            "playback_gain": gain, "response_gain": response_gain,
            "playback_note": "Animal stem: mean removed, resampled to 48 kHz, one gain to 0.8 peak. Energy above 24 kHz is removed.",
            "stems": {name: str(path.relative_to(output)) for name, path in stems.items()},
        }
        print(f"{source['id']}: {len(events)} events {counts}, shift {shift:+d} octaves, {duration:.1f} s", flush=True)
    write_json(manifest_path, {"created_at_utc": now(), "config_sha256": config["config_sha256"], "sample_rate": rate,
                               "perturbation": config["perturbation"], "response": config["response"]["interpretation"],
                               "sources": [previous[s["id"]] for s in config["sources"] if s["id"] in previous]})
    return manifest_path


# --- ACE-Step ------------------------------------------------------------------------------

def ace_jobs(layout: Layout, config: dict, prepared: dict, conditions=CONDITIONS, only: list[str] | None = None):
    _, output = directories(layout)
    ace, jobs, study = config["ace_step"], [], study_ids(config)
    for item in prepared["sources"]:
        if (only and item["id"] not in only) or (not only and item["id"] not in study):
            continue
        species = config["species"][item["species"]]
        for condition in conditions:
            spec = ace["conditions"][condition]
            jobs.append({
                "id": f"{item['id']}-{condition}", "source_id": item["id"], "condition": condition, "task": spec["task"],
                "src_audio": str((output / item["stems"][spec["source"]]).resolve()) if spec["source"] else None,
                "track": species["lego_track"] if spec["task"] == "lego" else None,
                "caption": species["caption"], "duration": round(item["duration_s"], 3), "seed": config["seed"],
                "audio_cover_strength": spec.get("audio_cover_strength", 1.0),
                "inference_steps": ace["inference_steps"], "guidance_scale": ace["guidance_scale"],
                "output": str((output / item["id"] / f"ace-{condition}.wav").resolve()),
            })
    return jobs


def run_ace(layout: Layout, config: dict, jobs: list[dict], jobs_path: Path, results_path: Path, ace_root: Path | None = None,
            offload: bool = True, quantization: str | None = "int8_weight_only"):
    """Run jobs in ACE-Step's own environment; one model load serves them all."""
    ace_root = (ace_root or layout.interim / ACE_DIR).resolve()
    python = ace_root / ".venv" / "bin" / "python"
    if not python.exists():
        raise ValueError(f"No ACE-Step environment at {ace_root}; clone {config['ace_step']['repository']} there and run 'uv sync'")
    write_json(jobs_path, {"ace_root": str(ace_root), "model": config["ace_step"]["model"], "offload": offload,
                           "quantization": quantization, "jobs": jobs, "results": str(results_path.resolve())})
    started = time.perf_counter()
    subprocess.run([str(python), str(RUNNER), str(jobs_path.resolve())], cwd=ace_root, check=True)
    print(f"ACE-Step: {len(jobs)} jobs in {time.perf_counter() - started:.0f} s", flush=True)
    return read_json(results_path)


def generate(layout: Layout, config: dict, ace_root: Path | None = None, conditions=CONDITIONS, only=None,
             offload: bool = True, quantization: str | None = "int8_weight_only"):
    """Generate every condition for the prepared sources under one caption and seed."""
    interim, _ = directories(layout)
    jobs = ace_jobs(layout, config, read_json(interim / "prepared.json"), conditions, only)
    run_ace(layout, config, jobs, interim / "ace-jobs.json", interim / "ace-results.json", ace_root, offload, quantization)
    return interim / "ace-results.json"


# --- CLI ---------------------------------------------------------------------------------------

app = typer.Typer(help="Music that follows the animal phrase: guides, responses, ACE-Step and alignment tests.", no_args_is_help=True)
DataOption = Annotated[Path, typer.Option(help="Root containing input/, interim/, output/.")]
SourcesOption = Annotated[list[str] | None, typer.Option("--source", help="Limit to these source IDs (repeatable).")]


@app.command("fetch")
def fetch_command(data_dir: DataOption = DEFAULT_DATA):
    """Download the humpback recording, its annotations and the DSWP coda rows."""
    fetch(Layout(data_dir), load_config())


@app.command("prepare")
def prepare_command(data_dir: DataOption = DEFAULT_DATA, source: SourcesOption = None):
    """Measure sources; write animal, guide, perturbed-guide and deterministic-response stems."""
    print(prepare(Layout(data_dir), load_config(), source))


@app.command("generate")
def generate_command(
    data_dir: DataOption = DEFAULT_DATA,
    source: SourcesOption = None,
    condition: Annotated[list[str] | None, typer.Option(help=f"{', '.join(CONDITIONS)} (repeatable).")] = None,
    ace_root: Annotated[Path | None, typer.Option(help="ACE-Step 1.5 checkout with its own .venv.")] = None,
    offload: Annotated[bool, typer.Option(help="CPU offload between stages; needed when other jobs share the GPU.")] = True,
):
    """Generate ACE-Step 1.5 outputs under a fixed caption and seed."""
    chosen = tuple(condition or CONDITIONS)
    if unknown := set(chosen) - set(CONDITIONS):
        raise typer.BadParameter(f"Unknown condition(s): {', '.join(sorted(unknown))}")
    print(generate(Layout(data_dir), load_config(), ace_root, chosen, source, offload))


@app.command("evaluate")
def evaluate_command(data_dir: DataOption = DEFAULT_DATA):
    """Timing, event and pitch-class agreement against own, swapped and perturbed guides."""
    from .follow_metrics import evaluate

    print(evaluate(Layout(data_dir), load_config(), PREDICTIONS))


@app.command("page")
def page_command(data_dir: DataOption = DEFAULT_DATA):
    """Write the listening page with stems, aligned displays, swap matrix and verdicts."""
    from .follow_gallery import write_page

    print(write_page(Layout(data_dir), load_config()))


@app.command("catalog")
def catalog_command(data_dir: DataOption = DEFAULT_DATA):
    """Write catalog.json for the sound map: located sources, events, listening files and dataset points."""
    from .follow_combine import catalog

    print(catalog(Layout(data_dir), load_config()))


@app.command("combine")
def combine_command(
    spec: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Combination spec JSON (sources, arrangement, trims, gains, optional ACE-Step).")],
    data_dir: DataOption = DEFAULT_DATA,
    model: Annotated[bool, typer.Option(help="Run ACE-Step when the spec asks for it.")] = True,
    ace_root: Annotated[Path | None, typer.Option(help="ACE-Step 1.5 checkout with its own .venv.")] = None,
    offload: Annotated[bool, typer.Option(help="CPU offload between stages; needed when other jobs share the GPU.")] = False,
    rerender: Annotated[bool, typer.Option(help="Render again even when a complete render of this combination exists.")] = False,
):
    """Combine several sources into one guide, response and optional ACE-Step cover; prints the manifest path last."""
    import json
    import sys

    from .follow_combine import combine

    try:
        print(combine(Layout(data_dir), load_config(), json.loads(spec.read_text(encoding="utf-8")), ace_root, model, offload, reuse=not rerender))
    except ValueError as error:  # one plain line, so the sound map can show it as is
        print(f"ERROR: {error}", file=sys.stderr)
        raise typer.Exit(2) from error


@app.command("run")
def run_command(
    data_dir: DataOption = DEFAULT_DATA,
    model: Annotated[bool, typer.Option(help="Also run ACE-Step; without it the page shows the deterministic response only.")] = True,
    ace_root: Annotated[Path | None, typer.Option(help="ACE-Step 1.5 checkout with its own .venv.")] = None,
):
    """fetch → prepare → generate → evaluate → page."""
    from .follow_gallery import write_page
    from .follow_metrics import evaluate

    layout, config = Layout(data_dir), load_config()
    fetch(layout, config)
    prepare(layout, config)
    if model:
        generate(layout, config, ace_root)
    evaluate(layout, config, PREDICTIONS)
    print(write_page(layout, config))
