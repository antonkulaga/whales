"""Metadata-only DCLDE analysis and selective public orca-model downloads."""

from collections import defaultdict
from datetime import datetime, timezone
import base64
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tomllib
from typing import Annotated
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
import zipfile

import polars as pl
import typer

ROOT = Path(__file__).resolve().parent
OBJECT = "dclde/2027/dclde_2027_killer_whales/Annotations.csv"
GCS = "https://storage.googleapis.com"
RECORD = "https://zenodo.org/api/records/22018132"
MODEL_IDS = ("orca-detector-dclde2026-v5", "orca-ecotype-dclde2026-v1")
app = typer.Typer(no_args_is_help=True, help=__doc__)


def get_json(url):
    with urlopen(url, timeout=60) as response:
        return json.load(response)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fetch_metadata(directory):
    """Download one annotation object, pinned to its current GCS generation."""
    meta = get_json(f"{GCS}/storage/v1/b/noaa-passive-bioacoustic/o/{quote(OBJECT, safe='')}")
    url = f"{GCS}/noaa-passive-bioacoustic/{OBJECT}?generation={meta['generation']}"
    path = directory / "Annotations.csv"
    directory.mkdir(parents=True, exist_ok=True)

    def matches(candidate):
        if not candidate.exists() or candidate.stat().st_size != int(meta["size"]):
            return False
        with candidate.open("rb") as stream:
            digest = hashlib.file_digest(stream, "md5").digest()
        return base64.b64encode(digest).decode() == meta["md5Hash"]

    if not matches(path):
        partial = path.with_suffix(".csv.part")
        if not matches(partial):
            with urlopen(url, timeout=90) as response, partial.open("wb") as stream:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
        if not matches(partial):
            raise ValueError("Annotation download does not match NOAA size/MD5; kept .part file")
        partial.replace(path)
    manifest = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "url": url, "object": meta["name"], "generation": meta["generation"],
        "bytes": int(meta["size"]), "updated": meta["updated"],
        "md5_base64": meta["md5Hash"], "sha256": sha256(path),
        "scope": "Complete combined annotation CSV only; no recordings downloaded.",
    }
    write_json(directory / "download.json", manifest)
    return path


def interval_union(intervals):
    """Duration covered by half-open intervals; overlapping annotations count once."""
    total = 0.0
    end = float("-inf")
    for start, stop in sorted(intervals):
        total += max(0.0, stop - max(start, end))
        end = max(end, stop)
    return total


def summarize(path, output):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        columns = next(csv.reader(stream))
    required = {"Soundfile", "Dataset", "Provider", "ClassSpecies", "Ecotype",
                "AnnotationLevel", "FileBeginSec", "FileEndSec", "UTC",
                "KW_certain", "LowFreqHz", "HighFreqHz"}
    if not required.issubset(columns):
        raise ValueError(f"Missing annotation columns: {sorted(required - set(columns))}")
    frame = pl.read_csv(path, schema_overrides={c: pl.String for c in columns},
                        empty_string_is_null=False)
    frame = frame.with_columns(
        pl.col("FileBeginSec").cast(pl.Float64, strict=False).alias("start"),
        pl.col("FileEndSec").cast(pl.Float64, strict=False).alias("stop"),
        pl.col("LowFreqHz").cast(pl.Float64, strict=False).alias("low"),
        pl.col("HighFreqHz").cast(pl.Float64, strict=False).alias("high"),
        pl.col("UTC").str.slice(0, 10).str.to_date("%Y-%m-%d", strict=False).alias("date"),
    ).with_columns((pl.col("stop") - pl.col("start")).alias("duration"))
    keys = ["Provider", "Dataset", "Soundfile"]
    valid = (pl.col("start").is_finite() & pl.col("stop").is_finite()
             & (pl.col("start") >= 0) & (pl.col("stop") > pl.col("start")))
    frequency_valid = (pl.col("low").is_finite() & pl.col("high").is_finite()
                       & (pl.col("low") >= 0) & (pl.col("high") >= pl.col("low")))
    # File-level labels do not establish a precisely bounded acoustic event.
    events = frame.filter(valid & pl.col("AnnotationLevel").is_in(["Call", "Detection"]))
    groups = {}
    output.mkdir(parents=True, exist_ok=True)
    for field in ["ClassSpecies", "Ecotype", "AnnotationLevel", "Provider", "Dataset", "KW_certain"]:
        counts = frame.group_by(field).agg(
            pl.len().alias("annotations"),
            pl.struct(keys).n_unique().alias("recordings"),
        ).with_columns((100 * pl.col("annotations") / frame.height).alias("percent"))
        counts = counts.sort("annotations", descending=True)
        counts.write_csv(output / f"{field}.csv")
        groups[field] = counts.to_dicts()
    cross = frame.group_by("Provider", "ClassSpecies", "Ecotype").len(name="annotations").sort(
        "Provider", "ClassSpecies", "Ecotype")
    cross.write_csv(output / "provider-species-ecotype.csv")
    orcas = frame.filter(pl.col("ClassSpecies") == "KW")
    known_orcas = orcas.filter(~pl.col("Ecotype").is_in(["NA", ""]))
    orca_ecotypes = known_orcas.group_by("Ecotype").len(name="annotations").with_columns(
        (100 * pl.col("annotations") / known_orcas.height).alias("percent_of_known_orca_ecotypes")
        if known_orcas.height else pl.lit(0.0).alias("percent_of_known_orca_ecotypes")
    ).sort("annotations", descending=True)
    orca_ecotypes.write_csv(output / "orca-ecotypes.csv")
    temporal = frame.filter(pl.col("date").is_not_null()).group_by("date").agg(
        pl.len().alias("annotations"), pl.struct(keys).n_unique().alias("recordings"),
    ).sort("date")
    temporal.write_csv(output / "daily.csv")
    intervals = defaultdict(list)
    for provider, dataset, soundfile, start, stop in events.select(*keys, "start", "stop").iter_rows():
        intervals[(provider, dataset, soundfile)].append((start, stop))
    duration = events["duration"]
    stats = {
        "annotations": frame.height,
        "recordings": frame.select(pl.struct(keys).n_unique()).item(),
        "distinct_soundfile_names": frame["Soundfile"].n_unique(),
        "recording_key": keys,
        "exact_duplicate_rows_excluding_export_index": frame.select(
            [c for c in columns if c]).height - frame.select([c for c in columns if c]).unique().height,
        "valid_utc_date_rows": frame["date"].count(),
        "date_min": str(frame["date"].min()), "date_max": str(frame["date"].max()),
        "invalid_or_missing_time_bounds": frame.filter(~valid.fill_null(False)).height,
        "invalid_or_missing_frequency_bounds": frame.filter(~frequency_valid.fill_null(False)).height,
        "valid_call_or_detection_rows": events.height,
        "orca_annotations": orcas.height,
        "orca_annotations_with_known_ecotype": known_orcas.height,
        "orca_annotations_without_ecotype": orcas.height - known_orcas.height,
        "known_orca_ecotypes": orca_ecotypes.to_dicts(),
        "duration_seconds": {"min": duration.min(), "median": duration.median(),
                             "p95": duration.quantile(0.95), "max": duration.max()},
        "summed_annotation_hours": duration.sum() / 3600,
        "union_annotated_hours": sum(interval_union(x) for x in intervals.values()) / 3600,
        "groups": groups,
    }
    report = {
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(path.resolve()), "input_sha256": sha256(path),
        "scope": "Combined annotation CSV only; not audio coverage, detected whale counts, or model evaluation.",
        "statistics": stats,
        "method": "Keep NA labels explicit. Recording key = Provider + Dataset + Soundfile. "
                  "Durations use finite 0 <= begin < end, Call/Detection only. Union intervals "
                  "within each recording across all classes; not total recorded or listening hours. "
                  "Missing and invalid time/frequency bounds are reported rather than imputed.",
    }
    write_json(output / "summary.json", report)
    lines = ["# DCLDE orca metadata summary", "", f"Source: `{path.resolve()}`", "",
             f"**{stats['annotations']:,} annotations across {stats['recordings']:,} recording keys.**",
             f"Annotation dates: {stats['date_min']} to {stats['date_max']}.", "",
             "These are annotation counts, not individual whales or total recording coverage.", ""]
    for field, counts in groups.items():
        lines.extend([f"## {field}", "", "| Label | Annotations | % | Recording keys |",
                      "|---|---:|---:|---:|"])
        for row in counts:
            label = (row[field] or "(empty)").replace("|", "\\|")
            lines.append(f"| {label} | {row['annotations']:,} | {row['percent']:.2f} | {row['recordings']:,} |")
        lines.append("")
    lines.extend(["## Timing and quality", "",
                  f"Valid call/detection intervals: {events.height:,}.",
                  f"Summed annotation duration: {stats['summed_annotation_hours']:.2f} hours.",
                  f"Union of annotated intervals within recordings: {stats['union_annotated_hours']:.2f} hours.",
                  f"Duration seconds (min / median / p95 / max): {stats['duration_seconds']}.",
                  f"Invalid/missing time bounds: {stats['invalid_or_missing_time_bounds']:,}.",
                  f"Invalid/missing frequency bounds: {stats['invalid_or_missing_frequency_bounds']:,}.",
                  f"Exact duplicate rows excluding export index: {stats['exact_duplicate_rows_excluding_export_index']:,}.",
                  f"Orca annotations with known population: {known_orcas.height:,}; "
                  f"without population: {orcas.height - known_orcas.height:,}.",
                  "", report["method"], "",
                  "Species/population frequencies reflect annotation practices and provider sampling. "
                  "Unannotated intervals are not confirmed negatives; NA is unknown. "
                  "No model predictions were used. CSV tables and JSON preserve exact values.", ""])
    (output / "summary.md").write_text("\n".join(lines))
    return report


@app.command("charts")
def charts_command(
    output: Annotated[Path, typer.Option()] = ROOT / "data/output/dclde",
):
    """Plot annotation distributions; requires the optional viz dependencies."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stats = json.loads((output / "summary.json").read_text())["statistics"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout="constrained")
    panels = [(stats["groups"]["ClassSpecies"], "ClassSpecies", "Sound-class annotations"),
              (stats["known_orca_ecotypes"], "Ecotype", "Orca annotations with known population")]
    for axis, (rows, label, title) in zip(axes, panels):
        values = [row["annotations"] for row in rows]
        bars = axis.barh([row[label] for row in rows], values, color="#246d84")
        axis.invert_yaxis()
        axis.bar_label(bars, labels=[f"{v:,}" for v in values], padding=4, fontsize=9)
        axis.set_xlim(0, max(values, default=1) * 1.25)
        axis.set_title(title, fontsize=11)
        axis.set_xlabel("Annotation rows")
        axis.spines[["top", "right"]].set_visible(False)
    fig.suptitle("DCLDE orca metadata — annotation counts, not animal counts", fontsize=12)
    for suffix in ("png", "svg"):
        fig.savefig(output / f"distributions.{suffix}", dpi=160)
    plt.close(fig)
    typer.echo(str((output / "distributions.png").resolve()))


@app.command("visualize")
def visualize_command(
    source: Annotated[Path, typer.Option()] = ROOT / "data/input/dclde/Annotations.csv",
    output: Annotated[Path, typer.Option()] = ROOT / "data/output/dclde",
):
    """Create six summary plots, deployment CSV/GeoJSON, and portable visual data."""
    from dclde_visuals import generate
    generate(source, output)
    typer.echo(str((output / "summary-statistics.png").resolve()))


class RemoteZip(io.RawIOBase):
    """Seekable byte-range reader; never falls back to a whole archive download."""

    def __init__(self, url, size):
        super().__init__()
        self.url, self.size, self.position = url, size, 0
        self.transferred_bytes = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset + (self.position if whence == 1 else self.size if whence == 2 else 0)
        if whence not in (0, 1, 2) or position < 0:
            raise ValueError("Invalid archive seek")
        self.position = position
        return position

    def read(self, size=-1):
        size = min(self.size - self.position, size if size >= 0 else self.size)
        if size <= 0:
            return b""
        start, stop = self.position, self.position + size - 1
        # Distinct query keys avoid intermediary caches serving a different range.
        request = Request(self.url + "?" + urlencode({"range": start, "end": stop}),
                          headers={"Range": f"bytes={start}-{stop}"})
        with urlopen(request, timeout=120) as response:
            if response.status != 206:
                raise ValueError("Server does not support byte ranges; refusing full ZIP download")
            expected = f"bytes {start}-{stop}/{self.size}"
            if response.headers.get("Content-Range") != expected:
                raise ValueError("Unexpected byte range returned")
            data = response.read(size + 1)
        if len(data) != size:
            raise ValueError("Incomplete archive range")
        self.position += len(data)
        self.transferred_bytes += len(data)
        return data


def fetch_models(directory):
    record = get_json(RECORD)
    results = []
    for model_id in MODEL_IDS:
        archive = next(f for f in record["files"] if f["key"].endswith(f"__{model_id}.zip"))
        typer.echo(f"Fetching ONNX and metadata only: {model_id}")
        with RemoteZip(archive["links"]["self"], archive["size"]) as remote, zipfile.ZipFile(remote) as zipped:
            members = []
            for info in zipped.infolist():
                name = PurePosixPath(info.filename)
                if name.is_absolute() or ".." in name.parts or not name.parts or name.parts[0] != model_id:
                    raise ValueError("Unsafe or unexpected archive member path")
                # Retain model plus small inference/licensing metadata, excluding training weights.
                if info.is_dir() or not (info.filename.endswith("/1/model.onnx")
                                        or (info.file_size < 1024 * 1024
                                            and name.suffix in {".md", ".toml", ".json", ".txt"})):
                    continue
                target = directory.joinpath(*name.parts)
                if target.exists():
                    # Compare against manifest hash for ONNX, ZIP CRC for all members.
                    import zlib
                    crc = 0
                    with target.open("rb") as stream:
                        while chunk := stream.read(1024 * 1024):
                            crc = zlib.crc32(chunk, crc)
                    if target.stat().st_size == info.file_size and crc == info.CRC:
                        members.append({"name": info.filename, "bytes": info.file_size, "sha256": sha256(target)})
                        continue
                target.parent.mkdir(parents=True, exist_ok=True)
                partial = target.with_name(target.name + ".part")
                # ZipFile verifies the member CRC while decompressing.
                partial.write_bytes(zipped.read(info))
                partial.replace(target)
                members.append({"name": info.filename, "bytes": info.file_size, "sha256": sha256(target)})
            model_dir = directory / model_id
            manifest = tomllib.loads((model_dir / "manifest.toml").read_text())
            onnx = model_dir / manifest["model"]["file"]
            if sha256(onnx) != manifest["model"]["onnx_sha256"]:
                raise ValueError(f"ONNX SHA-256 mismatch: {model_id}")
            results.append({"id": model_id, "record": RECORD, "archive": archive["key"],
                            "archive_bytes": archive["size"], "archive_checksum_declared": archive["checksum"],
                            "archive_checksum_verified": False, "transferred_bytes": remote.transferred_bytes,
                            "members": members, "onnx_sha256_verified": True})
    result = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Selected ONNX model files and small metadata; no upstream .ckpt files or audio",
              "models": results}
    write_json(directory / "download.json", result)
    return result


@app.command("metadata")
def metadata_command(
    directory: Annotated[Path, typer.Option(help="Local annotation directory.")] = ROOT / "data/input/dclde",
):
    """Download the full ~50 MB annotation CSV; no audio."""
    typer.echo(f"Verified {fetch_metadata(directory).resolve()}")


@app.command("summary")
def summary_command(
    source: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = ROOT / "data/input/dclde/Annotations.csv",
    output: Annotated[Path, typer.Option()] = ROOT / "data/output/dclde",
):
    """Analyze the local annotation CSV; write Markdown, JSON and CSV tables."""
    report = summarize(source, output)
    typer.echo(f"Analyzed {report['statistics']['annotations']:,} rows: {output.resolve() / 'summary.md'}")


@app.command("models")
def models_command(
    directory: Annotated[Path, typer.Option()] = ROOT / "models/dclde",
):
    """Fetch two public orca ONNX models (~94 MB unpacked) and metadata only."""
    result = fetch_models(directory)
    typer.echo(f"Verified {len(result['models'])} models: {directory.resolve()}")


@app.command("check-models")
def check_models_command(
    directory: Annotated[Path, typer.Option()] = ROOT / "models/dclde",
):
    """Load ONNX graphs and run synthetic inputs; requires numpy + onnxruntime."""
    import numpy as np
    import onnxruntime as ort

    checks = []
    for model_id in MODEL_IDS:
        model_dir = directory / model_id
        manifest = tomllib.loads((model_dir / "manifest.toml").read_text())
        path = model_dir / manifest["model"]["file"]
        if sha256(path) != manifest["model"]["onnx_sha256"]:
            raise ValueError(f"Model hash mismatch: {path}")
        session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        inputs = {}
        for tensor in session.get_inputs():
            shape = [n if isinstance(n, int) else 1 for n in tensor.shape]
            if tensor.name == "orig_sample_rate":
                inputs[tensor.name] = np.array([24000], dtype=np.int64)
            elif tensor.type == "tensor(float)":
                # Nonconstant input avoids zero-variance normalization artifacts.
                inputs[tensor.name] = np.random.default_rng(42).normal(0, 0.01, shape).astype(np.float32)
            else:
                raise ValueError(f"Unsupported input {tensor.name}: {tensor.type}")
        outputs = session.run(None, inputs)
        if not all(np.isfinite(x).all() for x in outputs):
            raise ValueError(f"Nonfinite synthetic output: {model_id}")
        checks.append({"id": model_id, "inputs": [{"name": x.name, "shape": x.shape, "type": x.type}
                                                  for x in session.get_inputs()],
                       "output_shapes": [list(x.shape) for x in outputs],
                       "finite_outputs": True, "onnx_sha256": sha256(path)})
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "onnxruntime": ort.__version__, "provider": "CPUExecutionProvider", "checks": checks,
              "limitation": "Synthetic graph-loading check only; no frontend validation or biological performance evaluation."}
    write_json(directory / "smoke-check.json", result)
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    app()
