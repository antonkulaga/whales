"""DCLDE excerpts for the music experiment: the 2027 killer-whale release and earlier workshops.

Only each source's window is kept. Large WAV files are read with HTTP range
requests: the header first, then just the window's bytes. Smaller files are
downloaded whole, cut, and discarded. Call annotations come from the combined
Annotations.csv already in data/input/dclde. They are stored with each excerpt,
and rows that mark the same call are merged.

Sources with a `release` (2011, 2013, 2015, 2022) come from earlier DCLDE workshops in the same
NOAA bucket. Their windows are read through soundfile over HTTP ranges, which seeks inside WAV and
FLAC alike, and their labels come from that release's own table: Raven-style logs with time and
frequency (2013), HARP call logs with times only (2015), traced whistle contours (2011), or none
when the release labels whole encounters (2022), so events are then measured from the waveform.
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


MIN_INSIDE_S = .3  # a call the window cuts is kept when at least this much of it is inside


def units_for(rows: list[dict], start_s: float, duration_s: float):
    """Annotated calls in the window, timed from its start; rows marking the same call are merged.

    A call the window's edge cuts keeps its inside part, marked `cut` ("start", "end" or "both"), so the
    guide still plays what the recording plays. A call cut at its start has no onset inside the window.
    """
    calls = sorted((number(r["FileBeginSec"]), number(r["FileEndSec"]), number(r["LowFreqHz"]), number(r["HighFreqHz"])) for r in rows)
    calls = [c for c in calls if not (math.isnan(c[0]) or math.isnan(c[1])) and c[1] > c[0]]
    merged = []
    for begin, end, low, high in calls:
        last = merged[-1] if merged else None
        if last and begin < last["end"] and (min(end, last["end"]) - begin) > .5 * min(end - begin, last["end"] - last["begin"]):
            last["end"], last["rows"] = max(last["end"], end), last["rows"] + 1
            continue
        merged.append({"begin": begin, "end": end, "low": low, "high": high, "rows": 1})
    stop = start_s + duration_s
    kept = []
    for m in merged:
        cut = {(True, False): "start", (False, True): "end", (True, True): "both"}.get((m["begin"] < start_s, m["end"] > stop))
        inside = min(m["end"], stop) - max(m["begin"], start_s)
        if inside > 0 and (cut is None or inside >= MIN_INSIDE_S):
            kept.append(m | {"cut": cut})
    units = []
    for i, m in enumerate(kept):
        unit = {"selection": i + 1, "start_s": round(max(m["begin"], start_s) - start_s, 4), "end_s": round(min(m["end"], stop) - start_s, 4),
                "low_hz": None if math.isnan(m["low"]) else m["low"], "high_hz": None if math.isnan(m["high"]) else m["high"],
                "rows_merged": m["rows"]}
        if m["cut"]:
            unit["cut"] = m["cut"]
        units.append(unit)
    return units


class RangeFile(io.RawIOBase):
    """A remote object as a seekable file: every read is one HTTP range request."""

    def __init__(self, url: str, size: int):
        self.url, self.size, self.position, self.fetched = url, size, 0, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset: int, whence: int = 0):
        self.position = (offset, self.position + offset, self.size + offset)[whence]
        return self.position

    def readinto(self, buffer):
        n = min(len(buffer), self.size - self.position)
        if n <= 0:
            return 0
        data = get(self.url, self.position, self.position + n - 1)
        buffer[:len(data)] = data
        self.position += len(data)
        self.fetched += len(data)
        return len(data)


def remote_window(source: dict):
    """The window from a remote WAV or FLAC, one channel or the channel mean; soundfile seeks, so only nearby bytes are read."""
    import soundfile as sf

    raw = RangeFile(url_for(source), source["size"])
    with sf.SoundFile(io.BufferedReader(raw, 1 << 20)) as stream:
        rate, channels, total_s = stream.samplerate, stream.channels, stream.frames / stream.samplerate
        start_s = max(0.0, min(source["start_s"], total_s - source["duration_s"]))
        stream.seek(round(start_s * rate))
        samples = stream.read(round(source["duration_s"] * rate), dtype="float64", always_2d=True)
    channel = source.get("channel")  # towed arrays: one hydrophone, since averaging spaced sensors smears whistles
    samples = samples[:, channel] if channel is not None else samples.mean(axis=1)
    return samples, rate, {"method": "HTTP byte ranges read through soundfile", "bytes_fetched": raw.fetched,
                           "file_duration_s": total_s, "start_s": start_s, "channels": channels, "channel": channel}


def annotation_file(layout: Layout, table: dict) -> Path:
    from .follow import download

    return download(f"{BUCKET}{table['object']}?generation={table['generation']}", layout.input / table["object"])


def utc(text: str):
    from datetime import datetime, timezone

    moment = datetime.fromisoformat(text.strip())
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def logged_calls(layout: Layout, spec: dict):
    """A release's call log as rows timed from the start of the source's audio file, in the shape units_for reads.

    `raven-log` (2013): a header row, ISO times with their offset, low/high frequency, a confidence column.
    `harp-log` (2015): no header; project, site, species, start, end and call type, times in UTC, no frequencies.
    """
    import csv

    start, rows = utc(spec["file_start"]), []

    def row(begin, end, low="NA", high="NA"):
        return {"FileBeginSec": (begin - start).total_seconds(), "FileEndSec": (end - start).total_seconds(), "LowFreqHz": low, "HighFreqHz": high}

    for table in spec["tables"]:
        with annotation_file(layout, table).open(newline="", encoding="utf-8-sig") as stream:
            if spec["format"] == "raven-log":
                rows += [row(utc(r["Start_DateTime_ISO8601"]), utc(r["End_DateTime_ISO8601"]), r["Low.Freq..Hz."], r["High.Freq..Hz."])
                         for r in csv.DictReader(stream)
                         if r["Species"].split("-")[0] == spec["species"] and r["Detection_Confidence"] in spec["confidence"]]
            else:
                rows += [row(utc(r[3]), utc(r[4])) for r in csv.reader(stream) if len(r) >= 5 and r[2].strip() == spec["species"]]
    return rows


def silbido_contours(data: bytes):
    """Each tonal in a silbido .ann file (DCLDE 2011 annotations) as (time s, Hz) points; big-endian, after silbidopy."""
    import struct

    TIME, FREQ, SNR, PHASE, SCORE, CONFIDENCE, RIDGE, SPECIES, CALL = 1, 2, 4, 8, 16, 32, 64, 512, 1024
    position, version, mask = 0, -1, TIME | FREQ  # headerless files carry time and frequency only
    if data[:8] == b"silbido!":
        version, mask, _, position = struct.unpack(">HHHI", data[8:18])
    fields = [f for f in (TIME, FREQ, SNR, PHASE, RIDGE) if mask & f]
    while position < len(data):
        position += 8 * (bool(mask & CONFIDENCE) + bool(mask & SCORE))
        for flag in (SPECIES, CALL):
            if mask & flag:
                position += 2 + struct.unpack(">H", data[position:position + 2])[0]
        position += 8 if version > 2 else 0  # graph id
        (count,) = struct.unpack(">i", data[position:position + 4])
        position += 4
        values = struct.unpack(f">{count * len(fields)}d", data[position:position + 8 * count * len(fields)])
        position += 8 * count * len(fields)
        yield sorted(zip(values[fields.index(TIME)::len(fields)], values[fields.index(FREQ)::len(fields)]))


def traced_whistles(layout: Layout, spec: dict, start_s: float, duration_s: float):
    """Whistles an analyst traced in the window, with their contours thinned to 5 ms steps.

    A whistle the window's edge cuts keeps its inside part, marked `cut`, like logged calls. Whistles
    centred above `max_hz` are left out: the stems keep 0–24 kHz, so they could not be heard.
    """
    units, stop = [], start_s + duration_s
    for points in silbido_contours(annotation_file(layout, spec["tables"][0]).read_bytes()):
        inside = [(t, f) for t, f in points if start_s <= t <= stop]
        cut = {(True, False): "start", (False, True): "end", (True, True): "both"}.get((points[0][0] < start_s, points[-1][0] > stop)) if points else None
        if len(inside) < 2 or (cut and inside[-1][0] - inside[0][0] < MIN_INSIDE_S):
            continue
        hz = sorted(f for _, f in inside)
        if hz[len(hz) // 2] > spec["max_hz"]:
            continue
        kept = [inside[0]]
        for t, f in inside[1:]:
            if t - kept[-1][0] >= .005:
                kept.append((t, f))
        unit = {"start_s": round(inside[0][0] - start_s, 4), "end_s": round(inside[-1][0] - start_s, 4),
                "low_hz": round(hz[0], 1), "high_hz": round(hz[-1], 1),
                "contour": {"time_s": [round(t - start_s, 4) for t, _ in kept], "hz": [round(f, 1) for _, f in kept]}}
        if cut:
            unit["cut"] = cut
        units.append(unit)
    units.sort(key=lambda u: u["start_s"])
    for i, unit in enumerate(units):
        unit["selection"] = i + 1
    return units


def release_units(layout: Layout, source: dict, start_s: float):
    """Units for an earlier release: logged calls, traced whistles, or None when only the encounter is labelled."""
    spec = source.get("annotations")
    if spec is None:
        return None, 0
    if spec["format"] == "silbido":
        units = traced_whistles(layout, spec, start_s, source["duration_s"])
        return units, len(units)
    rows = logged_calls(layout, spec)
    inside = [r for r in rows if r["FileBeginSec"] < start_s + source["duration_s"] and r["FileEndSec"] > start_s]
    return units_for(rows, start_s, source["duration_s"]), len(inside)


def window_units(layout: Layout, source: dict, start_s: float, rows: dict[str, list[dict]]):
    """A source's labelled calls in its window, named with its call label, and how many table rows back them."""
    if source.get("release"):
        units, annotation_rows = release_units(layout, source, start_s)
    else:
        selected = [r for r in rows.get(source["soundfile"], []) if r["ClassSpecies"] == source["class"]
                    and (source["class"] != "KW" or r["KW_certain"] == "1")]
        units, annotation_rows = units_for(selected, start_s, source["duration_s"]), len(selected)
    for unit in units or []:
        unit["label"] = source["call_label"]
    return units, annotation_rows


def fetch_dclde(layout: Layout, config: dict):
    import csv

    import soundfile as sf

    sources = [s for s in config["sources"] if s["kind"] == "dclde"]
    if not sources:
        return
    directory = layout.input / "dclde-audio"
    manifest_path = directory / "sources.json"
    known = {item["id"]: item for item in read_json(manifest_path)["clips"]} if manifest_path.exists() else {}
    wanted = {s["soundfile"] for s in sources if not s.get("release")}
    rows: dict[str, list[dict]] = {}
    annotations = layout.input / "dclde" / "Annotations.csv"
    if wanted and not annotations.exists():
        raise ValueError(f"{annotations} is missing; download it with 'main.py dclde' first")
    if wanted:
        with annotations.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                if row["Soundfile"] in wanted:
                    rows.setdefault(row["Soundfile"], []).append(row)
    clips = []
    for source in sources:
        path = directory / f"{source['id']}.wav"
        release = source.get("release")
        if source["id"] in known and path.exists() and digest(path) == known[source["id"]]["sha256"] \
                and known[source["id"]]["object"] == source["object"] and known[source["id"]]["requested_start_s"] == source["start_s"]:
            clip = known[source["id"]]  # the audio is cached; the calls are re-read, since labels and their rules can change
            units, annotation_rows = window_units(layout, source, clip["start_s"], rows)
            clips.append(clip | {"units": units, "annotation_rows": annotation_rows})
            continue
        samples, rate, how = remote_window(source) if release else excerpt(source)
        if rate > 48000:  # keep 0–24 kHz; HARP recordings at 200 kHz would make F0 bins too coarse
            from .follow import resample

            samples, how["resampled_from_hz"], rate = resample(samples, rate, 48000), rate, 48000
        directory.mkdir(parents=True, exist_ok=True)
        sf.write(path, samples, rate, subtype="FLOAT")
        units, annotation_rows = window_units(layout, source, how["start_s"], rows)
        clips.append({"id": source["id"], "object": source["object"], "generation": source["generation"], "url": url_for(source),
                      "requested_start_s": source["start_s"], "start_s": how["start_s"], "duration_s": source["duration_s"],
                      "rate": rate, "sha256": digest(path), "fetched_at_utc": now(), "how": how, "units": units,
                      "annotation_rows": annotation_rows,
                      "note": f"DCLDE {release or 2027} workshop data, NOAA passive bioacoustic archive on Google Cloud."})
        write_json(manifest_path, {"clips": clips})
        found = f"{len(units)} annotated calls" if units is not None else "no call labels, events measured from the waveform"
        print(f"{source['id']}: {found} in {source['duration_s']:.0f} s ({how['method']})", flush=True)
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
