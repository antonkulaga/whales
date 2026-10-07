"""DCLDE 2027 killer-whale and humpback excerpts for the music experiment.

Only each source's window is kept. Large WAV files are read with HTTP range
requests: the header first, then just the window's bytes. Smaller files are
downloaded whole, cut, and discarded. Call annotations come from the combined
Annotations.csv already in data/input/dclde. They are stored with each excerpt,
and rows that mark the same call are merged.
"""

import hashlib
import io
import math
from pathlib import Path
import struct
from urllib.request import Request, urlopen

from .data import Layout, digest, now, read_json, write_json

BUCKET = "https://storage.googleapis.com/noaa-passive-bioacoustic/"
WHOLE_LIMIT = 80_000_000  # bytes; larger WAVs are read by range


def url_for(source: dict):
    return f"{BUCKET}{source['object']}?generation={source['generation']}"


def get(url: str, start: int | None = None, end: int | None = None) -> bytes:
    headers = {"User-Agent": "whales-art/0.1"}
    if start is not None:
        headers["Range"] = f"bytes={start}-{end}"
    with urlopen(Request(url, headers=headers), timeout=300) as response:
        if start is not None and response.status != 206:
            raise ValueError(f"{url} ignored the byte range (HTTP {response.status})")
        return response.read()


def wav_layout(head: bytes):
    """RIFF chunks → format, channels, rate, bits and where the sample data starts."""
    if head[:4] != b"RIFF" or head[8:12] != b"WAVE":
        raise ValueError("Not a RIFF/WAVE file")
    position, fmt = 12, None
    while position + 8 <= len(head):
        name, size = head[position:position + 4], struct.unpack("<I", head[position + 4:position + 8])[0]
        body = position + 8
        if name == b"fmt ":
            tag, channels, rate, _, block, bits = struct.unpack("<HHIIHH", head[body:body + 16])
            if tag == 0xFFFE:  # WAVE_FORMAT_EXTENSIBLE: the subformat GUID starts with the real tag
                tag = struct.unpack("<H", head[body + 24:body + 26])[0]
            fmt = {"tag": tag, "channels": channels, "rate": rate, "block": block, "bits": bits}
        elif name == b"data":
            if fmt is None:
                raise ValueError("WAV data chunk before fmt chunk")
            return fmt | {"data_offset": body, "data_bytes": size}
        position = body + size + (size & 1)
    raise ValueError("WAV header longer than the bytes read")


def decode(raw: bytes, fmt: dict):
    import numpy as np

    bits, channels = fmt["bits"], fmt["channels"]
    if fmt["tag"] == 3 and bits == 32:
        samples = np.frombuffer(raw, "<f4").astype(np.float64)
    elif fmt["tag"] == 1 and bits == 16:
        samples = np.frombuffer(raw, "<i2") / 32768.0
    elif fmt["tag"] == 1 and bits == 24:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        samples = ((b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)) << 8 >> 8) / 8388608.0
    elif fmt["tag"] == 1 and bits == 32:
        samples = np.frombuffer(raw, "<i4") / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV encoding: tag {fmt['tag']}, {bits} bits")
    return samples.reshape(-1, channels).mean(axis=1)


def excerpt(source: dict):
    """The source window as mono float samples, plus how it was obtained."""
    import soundfile as sf

    url = url_for(source)
    start_s, duration_s = source["start_s"], source["duration_s"]
    if source["size"] > WHOLE_LIMIT:
        if not source["object"].lower().endswith(".wav"):
            raise ValueError(f"{source['id']}: only WAV files can be read by range")
        fmt = wav_layout(get(url, 0, 65535))
        total_s = fmt["data_bytes"] / fmt["block"] / fmt["rate"]
        start_s = max(0.0, min(start_s, total_s - duration_s))
        first = fmt["data_offset"] + round(start_s * fmt["rate"]) * fmt["block"]
        count = round(duration_s * fmt["rate"]) * fmt["block"]
        samples = decode(get(url, first, first + count - 1), fmt)
        return samples, fmt["rate"], {"method": "HTTP byte range", "byte_range": [first, first + count - 1],
                                      "file_duration_s": total_s, "start_s": start_s, "encoding": fmt}
    whole = get(url)
    samples, rate = sf.read(io.BytesIO(whole), dtype="float64", always_2d=True)
    total_s = len(samples) / rate
    start_s = max(0.0, min(start_s, total_s - duration_s))
    window = samples[round(start_s * rate):round((start_s + duration_s) * rate)].mean(axis=1)
    return window, rate, {"method": "whole file downloaded, cut and discarded", "file_bytes": len(whole),
                          "file_sha256": hashlib.sha256(whole).hexdigest(), "file_duration_s": total_s, "start_s": start_s}


def number(text: str):
    try:
        return float(text)
    except (TypeError, ValueError):
        return math.nan  # the table writes missing values as NA


def units_for(rows: list[dict], start_s: float, duration_s: float):
    """Annotated calls inside the window, timed from its start; rows marking the same call are merged."""
    calls = sorted((number(r["FileBeginSec"]), number(r["FileEndSec"]), number(r["LowFreqHz"]), number(r["HighFreqHz"])) for r in rows)
    calls = [c for c in calls if not (math.isnan(c[0]) or math.isnan(c[1]))]
    merged = []
    for begin, end, low, high in calls:
        if begin < start_s or end > start_s + duration_s or end <= begin:
            continue
        last = merged[-1] if merged else None
        if last and begin < last["end"] and (min(end, last["end"]) - begin) > .5 * min(end - begin, last["end"] - last["begin"]):
            last["end"], last["rows"] = max(last["end"], end), last["rows"] + 1
            continue
        merged.append({"begin": begin, "end": end, "low": low, "high": high, "rows": 1})
    return [{"selection": i + 1, "start_s": round(m["begin"] - start_s, 4), "end_s": round(m["end"] - start_s, 4),
             "low_hz": None if math.isnan(m["low"]) else m["low"], "high_hz": None if math.isnan(m["high"]) else m["high"],
             "rows_merged": m["rows"]} for i, m in enumerate(merged)]


def fetch_dclde(layout: Layout, config: dict):
    import csv

    import soundfile as sf

    sources = [s for s in config["sources"] if s["kind"] == "dclde"]
    if not sources:
        return
    directory = layout.input / "dclde-audio"
    manifest_path = directory / "sources.json"
    known = {item["id"]: item for item in read_json(manifest_path)["clips"]} if manifest_path.exists() else {}
    wanted = {s["soundfile"] for s in sources}
    rows: dict[str, list[dict]] = {}
    annotations = layout.input / "dclde" / "Annotations.csv"
    if not annotations.exists():
        raise ValueError(f"{annotations} is missing; download it with 'main.py dclde' first")
    with annotations.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["Soundfile"] in wanted:
                rows.setdefault(row["Soundfile"], []).append(row)
    clips = []
    for source in sources:
        path = directory / f"{source['id']}.wav"
        if source["id"] in known and path.exists() and digest(path) == known[source["id"]]["sha256"] \
                and known[source["id"]]["object"] == source["object"] and known[source["id"]]["requested_start_s"] == source["start_s"]:
            clips.append(known[source["id"]])
            continue
        samples, rate, how = excerpt(source)
        if rate > 48000:  # keep 0–24 kHz; HARP recordings at 200 kHz would make F0 bins too coarse
            from .follow import resample

            samples, how["resampled_from_hz"], rate = resample(samples, rate, 48000), rate, 48000
        directory.mkdir(parents=True, exist_ok=True)
        sf.write(path, samples, rate, subtype="FLOAT")
        selected = [r for r in rows.get(source["soundfile"], []) if r["ClassSpecies"] == source["class"]
                    and (source["class"] != "KW" or r["KW_certain"] == "1")]
        units = units_for(selected, how["start_s"], source["duration_s"])
        for unit in units:
            unit["label"] = source["call_label"]
        clips.append({"id": source["id"], "object": source["object"], "generation": source["generation"], "url": url_for(source),
                      "requested_start_s": source["start_s"], "start_s": how["start_s"], "duration_s": source["duration_s"],
                      "rate": rate, "sha256": digest(path), "fetched_at_utc": now(), "how": how, "units": units,
                      "annotation_rows": len(selected), "note": "DCLDE 2027 killer-whale dataset, NOAA passive bioacoustic archive on Google Cloud."})
        write_json(manifest_path, {"clips": clips})
        print(f"{source['id']}: {len(units)} annotated calls in {source['duration_s']:.0f} s ({how['method']})", flush=True)
    write_json(manifest_path, {"clips": clips})
    return manifest_path


def load_dclde(layout: Layout, source: dict):
    from .brush import read_audio

    directory = layout.input / "dclde-audio"
    clip = next(item for item in read_json(directory / "sources.json")["clips"] if item["id"] == source["id"])
    path = directory / f"{source['id']}.wav"
    if digest(path) != clip["sha256"]:
        raise ValueError(f"{path} changed since it was fetched")
    waveform, rate = read_audio(path)
    return waveform, rate, {"file": str(Path("dclde-audio") / path.name), "sha256": clip["sha256"], "start_s": clip["start_s"],
                            "object": clip["object"], "generation": clip["generation"]}, clip["units"]
