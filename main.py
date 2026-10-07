"""Cetacean dataset explorer and reproducible sound-to-image experiments."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Annotated
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError
import polars as pl
import typer

from experiments.cli import app as art_app
from experiments.follow import app as follow_app
from experiments.inscription import app as inscription_app
from dclde import app as dclde_app

ROOT = Path(__file__).resolve().parent
CLASSIFICATION = "dolphinteam/OpenWhistle-Classification-Finetuning"
app = typer.Typer(help=__doc__, no_args_is_help=True, add_completion=False)
app.add_typer(art_app, name="art")
app.add_typer(dclde_app, name="dclde")
app.add_typer(follow_app, name="follow")
app.add_typer(inscription_app, name="inscription")


@dataclass
class ContourOptions:
    config: str
    split: str
    offset: int
    limit: int
    min_confidence: float
    output: Path


def get_json(url):
    with urlopen(Request(url, headers={"User-Agent": "whales-explorer/0.1"}), timeout=45) as response:
        return json.load(response)


def server_url(endpoint, **params):
    return f"https://datasets-server.huggingface.co/{endpoint}?{urlencode(params)}"


def class_labels(feature):
    if isinstance(feature, dict) and feature.get("_type") == "ClassLabel":
        return {str(i): name for i, name in enumerate(feature["names"])}
    return None


def inspect_dataset(dataset, config=None):
    hub_url = f"https://huggingface.co/api/datasets/{quote(dataset, safe='/')}"
    info_url = server_url("info", dataset=dataset)
    hub = HfApi().dataset_info(dataset, timeout=45)
    info = get_json(info_url)
    configs = info["dataset_info"]
    if config:
        if config not in configs:
            raise ValueError(f"Unknown config {config!r}; choose from {', '.join(configs)}")
        configs = {config: configs[config]}
    return {
        "dataset": dataset,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "hub_revision_at_inspection": hub.sha,
        "gated": hub.gated,
        "declared_license": (hub.card_data or {}).get("license"),
        "sources": [hub_url, info_url],
        "note": "Viewer metadata is live, not a revision-pinned download. Missing license is unknown.",
        "configs": {
            name: {
                "features": value["features"],
                "class_labels": {
                    field: labels for field, feature in value["features"].items()
                    if (labels := class_labels(feature)) is not None
                },
                "splits": value.get("splits", {}),
            } for name, value in configs.items()
        },
    }


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def contour_segments(row, threshold):
    """Leave gaps at low-confidence points instead of interpolating across them."""
    if not row.get("f0_ok", False):
        return []
    times, frequencies, confidences = (row.get(k, []) for k in ("f0_time", "f0_hz", "f0_conf"))
    if not (len(times) == len(frequencies) == len(confidences)):
        raise ValueError("F0 arrays have different lengths")
    segments, current = [], []
    previous_time = None
    for t, frequency, confidence in zip(times, frequencies, confidences):
        valid = all(isinstance(x, (int, float)) and math.isfinite(x) for x in (t, frequency, confidence))
        valid = valid and t >= 0 and frequency > 0 and confidence >= threshold
        if valid:
            if previous_time is not None and t <= previous_time:
                raise ValueError("F0 times must increase")
            current.append((t, frequency))
            previous_time = t
        else:
            if current:
                segments.append(current)
            current = []
    if current:
        segments.append(current)
    return segments


def polar_point(t, frequency, duration):
    angle = 2 * math.pi * t / duration
    radius = 0.2 + 0.8 * max(0, min(1, (frequency - 3000) / 19050))
    return radius * math.cos(angle), radius * math.sin(angle)


def render_contours(rows, output, threshold):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise ValueError("Use: uv run --group viz main.py contours ...") from error
    fig, axes = plt.subplots(len(rows), 2, figsize=(10, 2.4 * len(rows)), squeeze=False)
    for i, item in enumerate(rows):
        row = item["metadata"]
        left, right = axes[i]
        duration = float(row["duration"])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Contour duration must be positive and finite")
        segments = contour_segments(row, threshold)
        for segment in segments:
            times, frequencies = zip(*segment)
            left.plot(times, [f / 1000 for f in frequencies], color="#187d91", marker=".", markersize=2)
            x, y = zip(*(polar_point(t, f, duration) for t, f in segment))
            right.plot(x, y, color="#187d91", marker=".", markersize=2)
        if not segments:
            left.text(0.5, 0.5, "No reliable F0 points", ha="center", transform=left.transAxes)
        left.set(xlim=(0, duration), ylim=(3, 22.05), ylabel="Frequency (kHz)", xlabel="Time (s)")
        left.set_title(f"Row {item['row_index']} · {item['label_name']}", loc="left", fontsize=10)
        left.grid(alpha=0.15)
        right.set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1), aspect="equal")
        right.set_title("Time → angle; frequency → radius", fontsize=9)
        right.axis("off")
    fig.suptitle(f"OpenWhistle contours · F0 confidence ≥ {threshold:g}\nWhistle tracks and an artistic mapping", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    for extension in ("png", "svg"):
        fig.savefig(output / f"contours.{extension}", dpi=140)
    plt.close(fig)


def sample_contours(args: ContourOptions):
    report = inspect_dataset(CLASSIFICATION, args.config)
    config = report["configs"][args.config]
    if args.split not in config["splits"]:
        raise ValueError(f"Unknown split {args.split!r}")
    url = server_url("rows", dataset=CLASSIFICATION, config=args.config, split=args.split,
                     offset=args.offset, length=args.limit)
    rows = []
    for item in get_json(url)["rows"]:
        row = item["row"]
        metadata = {k: v for k, v in row.items() if k not in ("audio", "f0_spectrogram")}
        rows.append({"row_index": item["row_idx"],
                     "label_name": config["class_labels"]["label"][str(row["label"])],
                     "metadata": metadata})
    if not rows:
        raise ValueError("No rows returned; choose an offset within the split")
    for item in rows:
        contour_segments(item["metadata"], args.min_confidence)
    args.output.mkdir(parents=True, exist_ok=True)
    render_contours(rows, args.output, args.min_confidence)
    write_json(args.output / "annotations.json", {
        "inspection": report, "rows_source": url, "rows": rows,
        "mapping": {"angle": "2*pi*time/duration", "radius": "0.2+0.8*clip((frequency_hz-3000)/19050,0,1)",
                    "min_f0_confidence": args.min_confidence,
                    "interpretation": "Artistic mapping; no inferred emotion, meaning, or confirmed caller identity."},
    })
    print(f"Saved {len(rows)} annotated contours to {args.output.resolve()}")


@app.command("catalog")
def catalog_command(
    as_json: Annotated[bool, typer.Option("--json", help="Print the full JSON inventory.")] = False,
    csv: Annotated[Path | None, typer.Option(help="Export the inventory as CSV using Polars.")] = None,
):
    """Print the curated dataset and label inventory."""
    data = json.loads((ROOT / "resources/datasets.json").read_text(encoding="utf-8"))
    if csv is not None:
        csv.parent.mkdir(parents=True, exist_ok=True)
        pl.from_dicts(data["datasets"]).write_csv(csv)
        print(f"Saved {csv.resolve()}")
    if as_json:
        print(json.dumps(data, indent=2))
    elif csv is None:
        print(f"Dataset inventory · verified {data['verified_on']}\n")
        for item in data["datasets"]:
            print(f"{item['id']}\n  Labels: {item['labels']}\n  Start: {item['starting_point']}\n")


@app.command("inspect")
def inspect_command(
    dataset: Annotated[str, typer.Argument(help="Hugging Face dataset ID.")],
    config: Annotated[str | None, typer.Option(help="Inspect only this configuration.")] = None,
    output: Annotated[Path | None, typer.Option(help="Save metadata JSON to this path.")] = None,
):
    """Fetch current HF schemas, class names, splits, and license metadata."""
    report = inspect_dataset(dataset, config)
    if output:
        write_json(output, report)
        print(f"Saved {output.resolve()}")
    else:
        print(json.dumps(report, indent=2))


@app.command("contours")
def contours_command(
    config: Annotated[str, typer.Option(help="OpenWhistle dataset configuration.")] = "balanced-review-sample",
    split: Annotated[str, typer.Option(help="Dataset split.")] = "train",
    offset: Annotated[int, typer.Option(min=0, help="First viewer row.")] = 0,
    limit: Annotated[int, typer.Option(min=1, max=24, help="Number of contours.")] = 6,
    min_confidence: Annotated[float, typer.Option(min=0, max=1, help="Minimum F0 confidence.")] = 0.3,
    output: Annotated[Path, typer.Option(help="Directory for plots and annotations.")] = ROOT / "data/output/openwhistle",
):
    """Fetch a few OpenWhistle F0 annotations and draw shapes."""
    if not math.isfinite(min_confidence):
        raise typer.BadParameter("Confidence must be finite.", param_hint="--min-confidence")
    sample_contours(ContourOptions(config, split, offset, limit, min_confidence, output))


def main():
    try:
        app()
    except (OSError, ValueError, KeyError, HfHubHTTPError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
