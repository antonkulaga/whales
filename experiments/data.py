"""Local data layout, small real-audio samples, and provenance."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data"


@dataclass(frozen=True)
class Layout:
    root: Path = DEFAULT_DATA

    @property
    def input(self):
        return self.root / "input"

    @property
    def interim(self):
        return self.root / "interim"

    @property
    def output(self):
        return self.root / "output"

    @property
    def cache(self):
        return self.interim / "huggingface"

    def create(self):
        for path in (self.input, self.interim, self.output, self.cache):
            path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def get_json(url: str):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "whales-art/0.1"}), timeout=60) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except URLError:
            if attempt == 2:
                raise
        time.sleep(2**attempt)


def fetch_samples(layout: Layout, per_dataset: int = 3, offset: int = 0):
    """Download Viewer waveforms, not entire corpora; hash every local source."""
    from huggingface_hub import HfApi

    layout.create()
    manifest_path = layout.input / "audio" / "sources.json"
    previous = read_json(manifest_path).get("clips", []) if manifest_path.exists() else []
    known = {item["id"]: item for item in previous}
    clips = []
    for dataset, config, prefix in (
        ("orrp/DSWP", "default", "dswp"),
        ("dolphinteam/OpenWhistle-Classification-Finetuning", "balanced-review-sample", "openwhistle"),
    ):
        info = HfApi().dataset_info(dataset, timeout=60)
        url = "https://datasets-server.huggingface.co/rows?" + urlencode(
            dict(dataset=dataset, config=config, split="train", offset=offset, length=per_dataset)
        )
        items = get_json(url)["rows"]
        if len(items) != per_dataset:
            raise ValueError(f"Expected {per_dataset} samples from {dataset}; got {len(items)}")
        for item in items:
            clip_id = f"{prefix}-{item['row_idx']:04d}"
            path = layout.input / "audio" / f"{clip_id}.wav"
            if clip_id in known and path.exists() and digest(path) == known[clip_id]["sha256"]:
                clips.append(known[clip_id])
                continue
            row = item["row"]
            audio_url = row["audio"][0]["src"]
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(".part")
            try:
                with urlopen(audio_url, timeout=120) as response, partial.open("wb") as stream:
                    shutil.copyfileobj(response, stream)
                partial.replace(path)
            finally:
                partial.unlink(missing_ok=True)
            clips.append({
                "id": clip_id, "path": str(path.resolve()), "sha256": digest(path),
                "dataset": dataset, "config": config, "split": "train", "row_index": item["row_idx"],
                "hub_revision_at_inspection": info.sha,
                "declared_license": (info.card_data or {}).get("license"),
                "viewer_rows_url": url, "viewer_asset_url": urlsplit(audio_url)._replace(query="").geturl(),
                "fetched_at_utc": now(),
                "metadata": {k: v for k, v in row.items() if k not in ("audio", "f0_spectrogram")},
                "note": "Viewer is live, not pinned to Hub revision; waveform hash identifies the analyzed bytes.",
            })
            write_json(manifest_path, {"clips": clips, "selection": "Contiguous samples; not balanced or representative."})
            print(f"Downloaded {clip_id}: {path.stat().st_size:,} bytes", flush=True)
    write_json(manifest_path, {"clips": clips, "selection": "Contiguous samples; not balanced or representative."})
    return manifest_path


def fetch_long_samples(layout: Layout, limit: int = 2, minimum_seconds: float = 30):
    """Select longer uninterrupted sequences from a small review metadata slice."""
    from huggingface_hub import HfApi

    dataset, config = "dolphinteam/OpenWhistle-Pretraining", "review-sample"
    url = "https://datasets-server.huggingface.co/rows?" + urlencode(dict(dataset=dataset, config=config, split="train", offset=0, length=100))
    rows = get_json(url)["rows"]
    selected = sorted((item for item in rows if item["row"]["duration"] >= minimum_seconds),
                      key=lambda item: (-item["row"]["duration"], item["row_idx"]))[:limit]
    if len(selected) != limit:
        raise ValueError(f"Only {len(selected)} sequences >= {minimum_seconds}s in the inspected slice")
    info = HfApi().dataset_info(dataset, timeout=60)
    directory = layout.input / "long-audio"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "sources.json"
    previous = {item["id"]: item for item in read_json(path)["clips"]} if path.exists() else {}
    clips = []
    for item in selected:
        clip_id = f"openwhistle-long-{item['row_idx']:04d}"
        waveform = directory / f"{clip_id}.wav"
        if clip_id in previous and waveform.exists() and digest(waveform) == previous[clip_id]["sha256"]:
            clips.append(previous[clip_id])
            continue
        audio_url = item["row"]["audio"][0]["src"]
        partial = waveform.with_suffix(".part")
        try:
            with urlopen(audio_url, timeout=120) as response, partial.open("wb") as stream:
                shutil.copyfileobj(response, stream)
            partial.replace(waveform)
        finally:
            partial.unlink(missing_ok=True)
        clips.append({"id": clip_id, "path": str(waveform.resolve()), "sha256": digest(waveform),
                      "dataset": dataset, "config": config, "split": "train", "row_index": item["row_idx"],
                      "hub_revision_at_inspection": info.sha, "declared_license": (info.card_data or {}).get("license"),
                      "viewer_rows_url": url, "viewer_asset_url": urlsplit(audio_url)._replace(query="").geturl(),
                      "fetched_at_utc": now(), "metadata": {key: value for key, value in item["row"].items() if key != "audio"},
                      "note": "Live Viewer waveform; source corpus is 96 kHz, inspect downloaded waveform rate separately. No pitch shift or invented silence."})
        write_json(path, {"clips": clips, "selection": "Longest qualifying sequences among review-sample train rows 0–99; exploratory, not representative."})
        print(f"Downloaded {clip_id}: declared {item['row']['duration']:.1f}s, {waveform.stat().st_size:,} bytes", flush=True)
    write_json(path, {"clips": clips, "selection": "Longest qualifying sequences among review-sample train rows 0–99; exploratory, not representative."})
    return path
