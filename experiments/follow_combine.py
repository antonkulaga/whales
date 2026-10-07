"""Combine several measured phrases into one piece, and place them on the map.

A combination spec names sources and how they sit in time: layered at chosen
offsets, or in sequence with a gap. Each part may be trimmed and given a gain and
register. Every part keeps its own measured events, instrument and register; the
recordings, guides and deterministic response are summed, then one gain scales the
whole combination so the declared balance survives. ACE-Step can then cover or
accompany the combined guide. Timing is scored against every part separately, so
a layered combination shows which phrase the music follows.

The sound map (apps/sound-map) writes specs, runs `main.py follow combine`, and
reads the manifest this module writes. Python stays the only implementation of
measurement, generation and scoring.
"""

import hashlib
import json
import math
from pathlib import Path
import shutil

from .data import Layout, ROOT, now, read_json, write_json
from .follow import directories, onsets, respond, render_guide, run_ace, write_wav
from .follow_gallery import MUSIC_BAND, event_data, listening
from .follow_metrics import leakage, load_mono, onset_envelope, timing

WORLD = ROOT / "resources" / "maps" / "world-map-data.json"
COUNTRIES = ROOT / "resources" / "maps" / "world-countries-110m.geojson"
ARRANGEMENTS = ("layer", "sequence")
TASKS = ("cover", "lego")


def prepared_sources(layout: Layout):
    interim, _ = directories(layout)
    path = interim / "prepared.json"
    if not path.exists():
        raise ValueError("No prepared sources; run 'main.py follow prepare' first")
    return {item["id"]: item for item in read_json(path)["sources"]}


def catalog(layout: Layout, config: dict):
    """catalog.json: located sources with events and listening files, plus the dataset points for context."""
    _, output = directories(layout)
    prepared = prepared_sources(layout)
    rate = config["sample_rate"]
    sources = []
    for source in config["sources"]:
        item = prepared.get(source["id"])
        if item is None:
            continue
        species = config["species"][item["species"]]
        files = {}
        for name in ("animal", "guide"):
            band = species["spectrogram_hz"] if name == "animal" else MUSIC_BAND
            audio, image = listening(output / item["stems"][name], band, rate)
            files[name] = {"audio": str(audio.relative_to(output)), "image": str(image.relative_to(output)), "band": list(band)}
        sources.append({"id": item["id"], "species": item["species"], "title": item["title"], "note": item["note"],
                        "duration_s": round(item["duration_s"], 3), "location": source["location"], "material": species["material"],
                        "instrument": species["instrument"]["name"], "register_shift_octaves": item["register_shift_octaves"],
                        "events": event_data(item["events"]), "onsets_s": [round(t, 4) for t in item["onsets_s"]], "files": files})
    world = read_json(WORLD)
    points = [{key: point.get(key) for key in ("id", "label", "dataset", "lon", "lat", "kind", "species", "source", "note")}
              for point in world["points"]]
    shutil.copyfile(COUNTRIES, output / "world-countries.geojson")
    data = {"created_at_utc": now(), "sources": sources, "points": points, "countries": "world-countries.geojson",
            "combination": config["combination"], "seed": config["seed"],
            "species": {name: {"caption": s["caption"], "instrument": s["instrument"]["name"], "material": s["material"],
                               "lego_track": s["lego_track"]} for name, s in config["species"].items()}}
    write_json(output / "catalog.json", data)
    return output / "catalog.json"


def finite(value, name: str):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def plan(spec: dict, config: dict, prepared: dict):
    """Validate a spec and resolve every part's trim, offset, gain and register; the id hashes the result."""
    limits = config["combination"]
    arrangement = spec.get("arrangement", "layer")
    if arrangement not in ARRANGEMENTS:
        raise ValueError(f"arrangement must be one of {', '.join(ARRANGEMENTS)}")
    parts = spec.get("parts") or []
    if not 1 <= len(parts) <= limits["max_parts"]:
        raise ValueError(f"Give between 1 and {limits['max_parts']} parts")
    gap = finite(spec.get("gap_s", 1.0), "gap_s")
    if not 0 <= gap <= 30:
        raise ValueError("gap_s must be between 0 and 30 seconds")
    low_gain, high_gain = limits["gain_db"]
    resolved, clock = [], 0.0
    for index, part in enumerate(parts):
        source = part.get("source")
        if source not in prepared:
            raise ValueError(f"Part {index + 1}: unknown or unprepared source {source!r}")
        item = prepared[source]
        start, end = (finite(v, f"part {index + 1} trim") for v in (part.get("trim_s") or [0, item["duration_s"]]))
        start, end = max(0.0, start), min(item["duration_s"], end)
        if end - start < limits["min_part_s"]:
            raise ValueError(f"Part {index + 1}: trim must keep at least {limits['min_part_s']} s of {source}")
        offset = clock if arrangement == "sequence" else finite(part.get("offset_s", 0.0), f"part {index + 1} offset")
        if offset < 0:
            raise ValueError(f"Part {index + 1}: offset must not be negative")
        gain = finite(part.get("gain_db", 0.0), f"part {index + 1} gain")
        if not low_gain <= gain <= high_gain:
            raise ValueError(f"Part {index + 1}: gain must be between {low_gain} and {high_gain} dB")
        shift = part.get("shift_octaves")
        shift = item["register_shift_octaves"] if shift is None else int(shift)
        if abs(shift) > 6:
            raise ValueError(f"Part {index + 1}: register shift must be within ±6 octaves")
        resolved.append({"index": index, "source": source, "species": item["species"], "trim_s": [round(start, 3), round(end, 3)],
                         "offset_s": round(offset, 3), "gain_db": round(gain, 2), "shift_octaves": shift})
        clock = offset + end - start + gap
    duration = round(max(p["offset_s"] + p["trim_s"][1] - p["trim_s"][0] for p in resolved) + .5, 3)
    if duration > limits["max_duration_s"]:
        raise ValueError(f"The combination lasts {duration:.0f} s; the limit is {limits['max_duration_s']} s")
    ace = spec.get("ace")
    if ace:
        species = {p["species"] for p in resolved}
        task = ace.get("task", "cover")
        if task not in TASKS:
            raise ValueError(f"ace.task must be one of {', '.join(TASKS)}")
        single = config["species"][species.pop()] if len(species) == 1 else None
        ace = {"task": task, "caption": str(ace.get("caption") or (single["caption"] if single else limits["caption"]))[:400],
               "audio_cover_strength": min(1.0, max(0.0, finite(ace.get("audio_cover_strength", limits["audio_cover_strength"]), "audio_cover_strength"))),
               "track": ace.get("track") or (single["lego_track"] if single else "keyboard"), "seed": int(ace.get("seed", config["seed"]))}
    combo = {"arrangement": arrangement, "gap_s": gap, "parts": resolved, "duration_s": duration, "ace": ace or None}
    # The config hash is part of the id, so editing instruments or rules never reuses stale stems.
    combo["id"] = hashlib.sha1(json.dumps([combo, config["config_sha256"]], sort_keys=True).encode()).hexdigest()[:12]
    combo["title"] = str(spec.get("title") or " + ".join(p["source"] for p in resolved))[:120]
    return combo


def placed(events: list[dict], trim, offset: float):
    """Events wholly inside the trim, moved to the part's offset; events cut by the trim are dropped."""
    start, end = trim
    moved = offset - start
    out = []
    for event in events:
        if event["kind"] == "click":
            if start <= event["time_s"] < end:
                out.append(event | {"time_s": event["time_s"] + moved})
        elif event["start_s"] >= start and event["end_s"] <= end:
            out.append(event | {"start_s": event["start_s"] + moved, "end_s": event["end_s"] + moved,
                                "time_s": [t + moved for t in event["time_s"]]})
    return out


def scores(audio, rate: int, parts: list[dict], frame_rate: int, metrics: dict):
    """Timing against all onsets over the whole piece, and against each part only while that part plays."""
    env = onset_envelope(audio, rate, frame_rate)
    sigma, shift = metrics["onset_sigma_s"], metrics["min_null_shift_s"]
    everything = sorted(t for part in parts for t in part["onsets_s"])
    per_part = []
    for part in parts:
        start = round(part["offset_s"] * frame_rate)
        stop = min(len(env), start + round((part["trim_s"][1] - part["trim_s"][0]) * frame_rate))
        window = env[start:stop]
        # Circular shifts need room: at least three times the minimum shift inside the part's span.
        if len(window) < 3 * shift * frame_rate:
            per_part.append(None)
            continue
        window = (window - window.mean()) / (window.std() + 1e-12)
        per_part.append(timing(window, [t - part["offset_s"] for t in part["onsets_s"]], frame_rate, sigma, shift))
    return {"all": timing(env, [t for t in everything if t < len(env) / frame_rate], frame_rate, sigma, shift), "parts": per_part,
            "part_window": "each part is scored only between its offset and its end",
            "envelope": [round(float(v), 2) for v in env[::2]], "envelope_rate_hz": frame_rate / 2}


def combine(layout: Layout, config: dict, spec: dict, ace_root: Path | None = None, run_model: bool = True, offload: bool = False):
    """Write stems, listening files and manifest.json for one combination; returns the manifest path."""
    import numpy as np

    _, output = directories(layout)
    prepared = prepared_sources(layout)
    combo = plan(spec, config, prepared)
    folder = output / "combos" / combo["id"]
    folder.mkdir(parents=True, exist_ok=True)
    rate, n = config["sample_rate"], round(combo["duration_s"] * config["sample_rate"])
    locations = {s["id"]: s["location"] for s in config["sources"]}
    mixes = {name: np.zeros(n) for name in ("animal", "guide", "response")}
    layers, parts = [], []
    for part in combo["parts"]:
        item = prepared[part["source"]]
        species = config["species"][item["species"]]
        events = placed(item["events"], part["trim_s"], part["offset_s"])
        gain = 10 ** (part["gain_db"] / 20)
        start, end = (round(t * rate) for t in part["trim_s"])
        recording = load_mono(output / item["stems"]["animal"], rate)[start:end]
        animal = np.zeros(n)
        i = round(part["offset_s"] * rate)
        animal[i:i + len(recording)] = recording[:n - i]
        guide = render_guide(events, combo["duration_s"], rate, species["instrument"], part["shift_octaves"])
        response = respond(events, combo["duration_s"], rate, part["shift_octaves"], config["response"])
        for name, layer in (("animal", animal), ("guide", guide), ("response", response)):
            mixes[name] += gain * layer
        layers.append({"animal": gain * animal, "guide": gain * guide})
        parts.append(part | {"title": item["title"], "location": locations[part["source"]], "instrument": species["instrument"]["name"],
                             "events": event_data(events), "onsets_s": [round(t, 4) for t in onsets(events)]})
    peak = max(float(np.max(np.abs(x))) for x in [*mixes.values(), *(v for layer in layers for v in layer.values())])
    scale = min(1.0, .9 / peak) if peak > 0 else 1.0
    stems = {}
    for name, mix in mixes.items():
        band = MUSIC_BAND if name != "animal" else (60.0, 20000.0)
        wav = write_wav(folder / f"{name}.wav", mix * scale, rate)
        audio, image = listening(wav, band, rate)
        stems[name] = {"audio": str(audio.relative_to(output)), "image": str(image.relative_to(output)), "band": list(band)}
    for part, layer in zip(parts, layers):
        part["files"] = {}
        for name, signal in layer.items():
            wav = write_wav(folder / f"part-{part['index']}-{name}.wav", signal * scale, rate)
            (audio,) = listening(wav, MUSIC_BAND, rate, image=False)
            part["files"][name] = str(audio.relative_to(output))
    ace_result = None
    if combo["ace"] and run_model:
        ace_wav = folder / "ace.wav"
        if not ace_wav.exists():
            a = combo["ace"]
            job = {"id": f"combo-{combo['id']}", "source_id": combo["id"], "condition": a["task"], "task": a["task"],
                   "src_audio": str((folder / "guide.wav").resolve()), "track": a["track"] if a["task"] == "lego" else None,
                   "caption": a["caption"], "duration": combo["duration_s"], "seed": a["seed"], "audio_cover_strength": a["audio_cover_strength"],
                   "inference_steps": config["ace_step"]["inference_steps"], "guidance_scale": config["ace_step"]["guidance_scale"],
                   "output": str(ace_wav.resolve())}
            run_ace(layout, config, [job], folder / "ace-jobs.json", folder / "ace-results.json", ace_root, offload)
        ace_result = read_json(folder / "ace-results.json")["jobs"][f"combo-{combo['id']}"]
        audio, image = listening(ace_wav, MUSIC_BAND, rate)
        stems["ace"] = {"audio": str(audio.relative_to(output)), "image": str(image.relative_to(output)), "band": list(MUSIC_BAND)}
    m = config["metrics"]
    results = {}
    for name in ("response", "ace"):
        if name in stems:
            audio = load_mono(folder / f"{name}.wav", rate)
            results[name] = scores(audio, rate, parts, m["frame_rate_hz"], m)
            if name == "ace":
                results[name]["leakage"] = leakage(audio, mixes["guide"] * scale, rate)
    manifest = {"id": combo["id"], "title": combo["title"], "created_at_utc": now(), "config_sha256": config["config_sha256"],
                "spec": combo, "duration_s": combo["duration_s"], "scale": scale, "parts": parts, "stems": stems,
                "scores": results, "ace": ace_result, "interpretation": config["combination"]["interpretation"]}
    write_json(folder / "manifest.json", manifest)
    return folder / "manifest.json"
