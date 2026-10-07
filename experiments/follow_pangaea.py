"""PANGAEA excerpts for the music experiment: AWI Ocean Acoustics recordings and their published labels.

Input: daily .tar archives of 5- or 10-minute WAV files from the AWI Ocean Acoustics Group's
moorings (HAFOS in the Weddell Sea, FRAM in Fram Strait), published on PANGAEA under CC-BY-4.0, and
the group's own label tables for the same recorders: Antarctic blue whale Z-call detections (time
and received level) and hourly bowhead whale presence.
Schema: one window per source, cut from one member of a daily archive and kept at a declared rate.
Each detection inside the window becomes a unit spanning a declared window around the logged time,
inside the detector's band, then trimmed to the frames where that band rises above its level over
the whole recording. A presence table only confirms that the species was logged in that hour, so events are
then measured from the waveform.
Output: data/input/pangaea-audio/<id>.wav plus sources.json, read by load_pangaea.

PANGAEA keeps these archives on tape. Until an archive is staged, requests are answered with
HTTP 503 and a 'loading from tape' page, so the download is retried. The archive is streamed:
reading stops at the wanted member, and only the window is stored. A copy of the archive saved as
data/interim/pangaea-archives/<dataset>-<file> is read instead, when present.
"""

import csv
from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import re
import tarfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .data import Layout, digest, now, read_json, write_json

DOWNLOAD = "https://download.pangaea.de/dataset/"
DOI = "https://doi.org/10.1594/PANGAEA."
TABLE = "https://doi.pangaea.de/10.1594/PANGAEA."  # the resolver drops ?format=textfile on redirect
STAGING_WAIT_S = 30
STAGING_LIMIT_S = 3600  # staging took 2–7 minutes per archive in October 2026


def archive_url(source: dict):
    return f"{DOWNLOAD}{source['dataset']}/files/{source['file']}"


def local_archive(layout: Layout, source: dict) -> Path:
    """Where a daily archive downloaded by hand is read from instead of PANGAEA (optional, never written here)."""
    return layout.interim / "pangaea-archives" / f"{source['dataset']}-{source['file']}"


def staged(url: str, wait_s: float = STAGING_WAIT_S, limit_s: float = STAGING_LIMIT_S):
    """An open response for a PANGAEA file, retried while the archive is being restored from tape."""
    started = time.monotonic()
    while True:
        try:
            return urlopen(Request(url, headers={"User-Agent": "whales-art/0.1"}), timeout=600)
        except HTTPError as error:
            if error.code != 503 or time.monotonic() - started > limit_s:
                raise
            print(f"PANGAEA is loading {url.rsplit('/', 1)[-1]} from tape; retrying in {wait_s:.0f} s", flush=True)
            time.sleep(wait_s)


def member_bytes(stream, member: str):
    """One member of a tar stream, read in order; the rest of the archive is never read."""
    with tarfile.open(fileobj=stream, mode="r|") as archive:
        for entry in archive:
            if Path(entry.name).name == member:
                return archive.extractfile(entry).read()
    raise ValueError(f"{member} is not in the archive")


def member_start(member: str):
    """UTC start of a recording, from the date and time in its file name (YYYYMMDD-HHMMSS or similar)."""
    found = re.search(r"(\d{8})[-_T]?(\d{6})", member)
    if not found:
        raise ValueError(f"No start time in the file name {member}")
    return datetime.strptime("".join(found.groups()), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)


def decoded(data: bytes, target: int | None = None):
    """A WAV member as mono float samples at `target` Hz when given, plus its native rate.

    The species analysis is set in samples, so a recording is brought to the rate it was tuned for.
    """
    import soundfile as sf

    samples, native = sf.read(io.BytesIO(data), dtype="float64", always_2d=True)
    samples, rate = samples.mean(axis=1), native
    if target and target != rate:
        from .follow import resample

        samples, rate = resample(samples, rate, target), target
    return samples, rate, native


def cut(samples, rate: int, start_s: float, duration_s: float):
    """The window, moved back when it would run past the end of the file; also its start and the file length."""
    total_s = len(samples) / rate
    start_s = max(0.0, min(start_s, total_s - duration_s))
    first = round(start_s * rate)
    return samples[first:first + round(duration_s * rate)], start_s, total_s


def table(layout: Layout, dataset: int):
    """A PANGAEA data matrix as rows of named columns; the metadata block above it is skipped."""
    from .follow import download

    path = download(f"{TABLE}{dataset}?format=textfile", layout.input / "pangaea" / f"{dataset}.tab")
    text = path.read_text(encoding="utf-8")
    return list(csv.DictReader(text.split("*/\n", 1)[-1].splitlines(), delimiter="\t"))


def utc(text: str):
    moment = datetime.fromisoformat(text.strip())
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def detection_units(rows: list[dict], begin, start_s: float, duration_s: float, labels: dict):
    """Logged detections inside the window as calls spanning `call_window_s` around each logged time; overlaps merge.

    A detection log gives one time per call, not its extent. The declared window says where the call
    lies around that time (for the AWI Z-call log, the time falls in the downsweep), and the detector's
    band bounds the contour search.
    """
    from .follow_dclde import units_for

    column = next(name for name in rows[0] if name.startswith("SPL")) if rows else None
    before, after = labels["call_window_s"]
    logged = [((utc(r["Date/Time"]) - begin).total_seconds(), float(r[column])) for r in rows]
    calls = [{"FileBeginSec": t + before, "FileEndSec": t + after, "LowFreqHz": labels["band_hz"][0], "HighFreqHz": labels["band_hz"][1]}
             for t, _ in logged]
    inside = [{"offset_s": round(t - start_s, 3), "spl_db": spl} for t, spl in logged if start_s <= t < start_s + duration_s]
    return units_for(calls, start_s, duration_s), inside


def band_level(samples, rate: int, band, frame_s: float):
    """Level in dB of one frequency band, frame by frame."""
    import numpy as np
    from scipy.signal import butter, sosfiltfilt

    hop = round(frame_s * rate)
    filtered = sosfiltfilt(butter(4, band, "bandpass", fs=rate, output="sos"), samples)
    return 10 * np.log10(np.mean(filtered[:len(filtered) // hop * hop].reshape(-1, hop) ** 2, axis=1) + 1e-30)


def trimmed(samples, rate: int, units: list[dict], margin_db: float, background=None, frame_s: float = .5):
    """Each call cut to the frames where its band stands `margin_db` above the background's median band level.

    A logged window is wider than the call it holds; frames of noise at either end would turn into
    contour points. `background` is the whole recording the window came from: a short window can be
    mostly call, so its own median is not the background. Calls with no frame above the margin are
    dropped rather than kept as noise.
    """
    import numpy as np

    out = []
    for unit in units:
        band = [unit["low_hz"], unit["high_hz"]]
        level = band_level(samples, rate, band, frame_s)
        floor = float(np.median(band_level(samples if background is None else background, rate, band, frame_s)))
        first, last = int(unit["start_s"] / frame_s), min(len(level), int(np.ceil(unit["end_s"] / frame_s)))
        loud = np.flatnonzero(level[first:last] >= floor + margin_db)
        if len(loud):
            out.append(unit | {"start_s": round(float(first + loud[0]) * frame_s, 3), "end_s": round(float(first + loud[-1] + 1) * frame_s, 3),
                               "logged_span_s": [unit["start_s"], unit["end_s"]]})
    for i, unit in enumerate(out):
        unit["selection"] = i + 1
    return out


def presence(rows: list[dict], moment):
    """The logged hour that holds `moment`, or None; empty cells are hours without the species."""
    for row in rows:
        values = list(row.values())
        if utc(values[0]) <= moment < utc(values[1]):
            return {"hour_start": values[0], "hour_end": values[1], "present": values[2].strip() not in ("", "0")}
    return None


def day_types(rows: list[dict], day: str):
    """Song types logged as present on one day, in the repertoire table's own numbering."""
    return sorted({r["Type"] for r in rows if r["Date/Time"].startswith(day) and r["Presence/absence"].strip() == "1"},
                  key=lambda t: [int(part) for part in t.split(".")])


def labelled(layout: Layout, source: dict, begin, start_s: float):
    """Units and label evidence for a window: detections become units, presence only confirms the hour."""
    labels = source["labels"]
    rows = table(layout, labels["dataset"])
    if labels["format"] == "detections":
        units, inside = detection_units(rows, begin, start_s, source["duration_s"], labels)
        return units, {"format": "detections", "dataset": labels["dataset"], "doi": f"{DOI}{labels['dataset']}", "detections": inside}
    if labels["format"] == "presence":
        hour = presence(rows, begin + timedelta(seconds=start_s))
        if not (hour and hour["present"]):
            raise ValueError(f"{source['id']}: the presence table does not log the species in this hour")
        evidence = {"format": "presence", "dataset": labels["dataset"], "doi": f"{DOI}{labels['dataset']}", "hour": hour}
        if "song_types" in labels:  # a daily repertoire table: which song types were heard that day, not in this window
            day = (begin + timedelta(seconds=start_s)).date().isoformat()
            evidence["song_types"] = {"dataset": labels["song_types"], "doi": f"{DOI}{labels['song_types']}", "day": day,
                                      "types_heard_that_day": day_types(table(layout, labels["song_types"]), day)}
        return None, evidence
    raise ValueError(f"{source['id']}: unknown label format {labels['format']!r}")


def fetch_pangaea(layout: Layout, config: dict):
    import soundfile as sf

    sources = [s for s in config["sources"] if s["kind"] == "pangaea"]
    if not sources:
        return
    directory = layout.input / "pangaea-audio"
    manifest_path = directory / "sources.json"
    known = {item["id"]: item for item in read_json(manifest_path)["clips"]} if manifest_path.exists() else {}
    keys = ("dataset", "file", "member", "requested_start_s", "duration_s", "rate")
    clips = []
    for source in sources:
        path = directory / f"{source['id']}.wav"
        wanted = {"dataset": source["dataset"], "file": source["file"], "member": source["member"],
                  "requested_start_s": source["start_s"], "duration_s": source["duration_s"], "rate": source.get("rate")}
        old = known.get(source["id"])
        if old and path.exists() and digest(path) == old["sha256"] and all(old.get(k) == wanted[k] for k in keys):
            clips.append(old)
            continue
        local = local_archive(layout, source)
        with (local.open("rb") if local.exists() else staged(archive_url(source))) as stream:
            data = member_bytes(stream, source["member"])
        whole, rate, native = decoded(data, source.get("rate"))
        samples, start_s, total_s = cut(whole, rate, source["start_s"], source["duration_s"])
        directory.mkdir(parents=True, exist_ok=True)
        sf.write(path, samples, rate, subtype="FLOAT")
        begin = member_start(source["member"])
        units, evidence = labelled(layout, source, begin, start_s)
        if units and "trim_db" in source["labels"]:
            units = trimmed(samples, rate, units, source["labels"]["trim_db"], whole)
        for unit in units or []:
            unit["label"] = source["call_label"]
        how = {"method": f"daily archive {'read from ' + str(local) if local.exists() else 'streamed from PANGAEA'} to the member; only the window is kept",
               "member_bytes": len(data), "member_start_utc": begin.isoformat(), "file_duration_s": total_s, "start_s": start_s,
               "native_rate": native}
        clips.append(wanted | {"id": source["id"], "url": archive_url(source), "doi": f"{DOI}{source['dataset']}",
                               "start_s": how["start_s"], "rate": rate, "sha256": digest(path), "fetched_at_utc": now(),
                               "how": how, "units": units, "labels": evidence,
                               "note": "AWI Ocean Acoustics Group recording on PANGAEA (CC-BY-4.0)."})
        write_json(manifest_path, {"clips": clips})
        found = f"{len(units)} logged calls" if units is not None else "species logged in this hour; events measured from the waveform"
        print(f"{source['id']}: {found} in {source['duration_s']:.0f} s of {source['member']}", flush=True)
    write_json(manifest_path, {"clips": clips})
    return manifest_path


def load_pangaea(layout: Layout, source: dict):
    from .brush import read_audio

    directory = layout.input / "pangaea-audio"
    clip = next(item for item in read_json(directory / "sources.json")["clips"] if item["id"] == source["id"])
    path = directory / f"{source['id']}.wav"
    if digest(path) != clip["sha256"]:
        raise ValueError(f"{path} changed since it was fetched")
    waveform, rate = read_audio(path)
    return waveform, rate, {"file": str(Path("pangaea-audio") / path.name), "sha256": clip["sha256"], "start_s": clip["start_s"],
                            "doi": clip["doi"], "archive": clip["file"], "member": clip["member"], "labels": clip["labels"]}, clip["units"]
