"""Audit what DCLDE 2027 labels can support: population, spatial and abundance questions.

Downloads only small public metadata (DAS arrival picks, the authors' batch-1
localizations, the 21-row aerial survey and DORI's label table) beside the full
annotation CSV, then writes a versioned JSON audit. No audio is downloaded.

    uv run python dclde_opportunities.py fetch
    uv run python dclde_opportunities.py audit
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Annotated
from urllib.parse import quote
from urllib.request import Request, urlopen

import polars as pl
import typer

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data" / "input" / "dclde"
AUDIT = ROOT / "resources" / "audits" / "dclde-opportunities.json"
GCS = "https://storage.googleapis.com"
BUCKET = "noaa-passive-bioacoustic"
DAS_PREFIX = "dclde/2027/dclde_2027_das-finwhale-localization/annotations/"
SMALL_FILES = {
    "narw/AerialSurvey.csv": f"{GCS}/{BUCKET}/dclde/2027/dclde2027_narw_detections_in_cape_cod_bay/other/AerialSurvey.csv",
    "goestchel/batch1_localizations_with_coords.csv": "https://raw.githubusercontent.com/Ocean-Data-Lab/Goestchel_JASA_2025b/main/batch1_localizations_with_coords.csv",
    "dori/DORI.csv": "https://huggingface.co/datasets/DORI-SRKW/DORI-ONC/resolve/main/DORI.csv",
}
app = typer.Typer(help=__doc__, no_args_is_help=True, add_completion=False)


def sha256(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(url: str, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    with urlopen(Request(url, headers={"User-Agent": "whales-dclde/0.1"}), timeout=120) as response, partial.open("wb") as stream:
        shutil.copyfileobj(response, stream)
    partial.replace(path)


@app.command("fetch")
def fetch_command(directory: Annotated[Path, typer.Option(help="DCLDE input directory.")] = INPUT):
    """Download the small DAS, localization, aerial-survey and DORI tables with hashes."""
    listing_url = f"{GCS}/storage/v1/b/{BUCKET}/o?prefix={quote(DAS_PREFIX)}&fields=items(name,size,md5Hash,generation),nextPageToken"
    with urlopen(listing_url, timeout=60) as response:
        listing = json.load(response)
    if listing.get("nextPageToken"):
        raise ValueError("DAS annotation listing is paginated; extend the fetcher before trusting it")
    files = []
    for item in listing["items"]:
        relative = Path("das-annotations") / item["name"].split("/")[-2] / item["name"].split("/")[-1]
        target = directory / relative
        if not target.exists():
            download(f"{GCS}/{BUCKET}/{quote(item['name'])}", target)
        files.append({"path": str(relative), "source": item["name"], "generation": item["generation"], "bytes": int(item["size"]), "sha256": sha256(target)})
    for relative, url in SMALL_FILES.items():
        target = directory / relative
        if not target.exists():
            download(url, target)
        files.append({"path": relative, "source": url, "bytes": target.stat().st_size, "sha256": sha256(target)})
    manifest = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "files": files,
                "note": "Live URLs; GitHub and Hugging Face files are not pinned to a revision here, so hashes identify the analysed bytes."}
    (directory / "opportunities-sources.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(files)} files; manifest at {directory / 'opportunities-sources.json'}")


def table(frame: pl.DataFrame):
    return frame.to_dicts()


def orca_population(path: Path):
    frame = pl.read_csv(path, infer_schema_length=50_000, null_values=["NA", ""])
    kw = frame.filter(pl.col("ClassSpecies") == "KW").with_columns(
        pl.col("UTC").str.slice(0, 10).alias("day"), (pl.col("FileEndSec") - pl.col("FileBeginSec")).alias("duration_s"))
    by_level = kw.group_by(["AnnotationLevel", "Ecotype"]).len().sort(["AnnotationLevel", "Ecotype"])
    calls = kw.filter(pl.col("AnnotationLevel") == "Call")
    conventions = calls.filter(pl.col("Ecotype").is_not_null()).group_by(["Provider", "Ecotype"]).agg(
        pl.len().alias("calls"), pl.col("day").n_unique().alias("days"),
        pl.col("duration_s").median().round(2).alias("median_duration_s"),
        pl.col("LowFreqHz").median().round(0).alias("median_low_hz"), pl.col("HighFreqHz").median().round(0).alias("median_high_hz"),
    ).sort(["Provider", "Ecotype"])
    boxes = kw.group_by("Provider").agg(
        pl.len().alias("rows"), (pl.col("LowFreqHz") == pl.col("HighFreqHz")).sum().alias("zero_bandwidth"),
        pl.col("LowFreqHz").is_null().sum().alias("no_frequency_bounds")).sort("Provider")
    tkw = calls.filter(pl.col("Ecotype") == "TKW").group_by("Provider").len().with_columns((pl.col("len") / pl.col("len").sum() * 100).round(1).alias("percent"))
    pairs = kw.filter(pl.col("Ecotype").is_in(["SRKW", "TKW"])).group_by(["Provider", "Dataset", "AnnotationLevel", "Ecotype"]).agg(
        pl.len().alias("rows"), pl.col("day").n_unique().alias("days"), pl.col("Soundfile").n_unique().alias("files"))
    both = pairs.group_by(["Provider", "Dataset", "AnnotationLevel"]).agg(pl.col("Ecotype").n_unique().alias("k")).filter(pl.col("k") == 2)
    pairs = pairs.join(both, on=["Provider", "Dataset", "AnnotationLevel"]).drop("k").sort(["Provider", "Dataset", "AnnotationLevel", "Ecotype"])
    return {
        "input_sha256": sha256(path),
        "killer_whale_rows_by_level_and_ecotype": table(by_level),
        "call_level_box_conventions_by_provider_and_ecotype": table(conventions),
        "frequency_box_conventions_by_provider": table(boxes),
        "tkw_call_annotations_by_provider": table(tkw),
        "same_dataset_srkw_and_tkw": table(pairs),
        "interpretation": [
            "SIO and SIMRES killer-whale boxes all have LowFreqHz == HighFreqHz; OrcaSound rows have no frequency bounds.",
            "SIO supplies over half of call-level TKW annotations, so pooled box geometry or bandwidth confounds population with provider convention.",
            "NRKW appears only at Detection level; SAR comes from one provider.",
            "Independent units for population tests are encounter days, not calls.",
        ],
    }


def das(directory: Path):
    paths = sorted((directory / "das-annotations").glob("batch*/*.csv"))
    picks = pl.concat([pl.read_csv(p).with_columns(pl.lit(p.parent.name).alias("batch")) for p in paths], how="diagonal_relaxed")
    calls = picks.group_by(["batch", "cable", "filename", "call_id"]).agg(
        pl.len().alias("picks"), pl.col("call_type").first(), (pl.col("dist").max() - pl.col("dist").min()).alias("span_m"),
        (pl.col("time").max() - pl.col("time").min()).alias("moveout_s"))
    localization = pl.read_csv(directory / "goestchel" / "batch1_localizations_with_coords.csv")
    return {
        "annotation_files": len(paths), "picks": picks.height, "calls": calls.height,
        "calls_by_batch_and_cable": table(calls.group_by(["batch", "cable"]).len().sort(["batch", "cable"])),
        "calls_by_type": table(calls.group_by("call_type").len().sort("call_type")),
        "median_picks_per_call": float(calls["picks"].median()), "median_moveout_s": float(calls["moveout_s"].median()),
        "median_cable_span_m": float(calls["span_m"].median()),
        "utc_range": [picks["utc_time"].min(), picks["utc_time"].max()],
        "authors_batch1_localizations": {"rows": localization.height, "utc_range": [localization["utc"].min(), localization["utc"].max()],
                                         "by_sensor_and_type": table(localization.group_by(["sensor", "call_type"]).len().sort(["sensor", "call_type"])),
                                         "depth_values_m": sorted(set(localization["z_local"].to_list())),
                                         "note": "Research output from the authors' repository; deltax units undocumented; not the official scoring reference."},
        "interpretation": ["Each call has ~14 arrival picks along a cable: distance–time pairs that trace a moveout curve whose apex marks the closest cable point.",
                           "Arrival picks locate nothing by themselves; localization needs association across picks/cables and a propagation model."],
    }


def aerial(directory: Path):
    frame = pl.read_csv(directory / "narw" / "AerialSurvey.csv").rename(lambda c: c.strip())
    counts = frame["Total # of Individuals"].cast(pl.Int64)
    return {"flights": frame.height, "dates": [frame["DATE"].first(), frame["DATE"].last()],
            "total_individuals_per_flight": counts.to_list(), "max_count": int(counts.max()),
            "note": "Aggregate counts per flight over surveyed track lines; no individual positions. Effort (lines surveyed, hours) varies per flight."}


def dori(directory: Path):
    frame = pl.read_csv(directory / "dori" / "DORI.csv", infer_schema_length=100_000)
    calls = frame.filter(pl.col("call_annotation_clean").str.contains(r"^s\d+$"))
    return {"rows": frame.height,
            "species": table(frame.group_by("species_label_clean").len().sort("len", descending=True)),
            "ecotype": table(frame.group_by("ecotype_label_clean").len().sort("len", descending=True)),
            "srkw_call_type_rows": calls.height, "srkw_call_types": calls["call_annotation_clean"].n_unique(),
            "top_call_types": table(calls.group_by("call_annotation_clean").len().sort("len", descending=True).head(15)),
            "license_values": table(frame.group_by("license").len().sort("len", descending=True)),
            "note": "Prerelease, partially verified labels; per-row license values differ from the card; possible overlap with DCLDE sources."}


@app.command("audit")
def audit_command(directory: Annotated[Path, typer.Option(help="DCLDE input directory.")] = INPUT,
                  output: Annotated[Path, typer.Option(help="Audit JSON.")] = AUDIT):
    """Count the labels each DCLDE track can actually support and save the evidence."""
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "population": orca_population(directory / "Annotations.csv"),
        "spatial_das": das(directory),
        "abundance_aerial": aerial(directory),
        "dori_call_types": dori(directory),
        "scope": "Metadata only. No audio, no model evaluation, no official scoring rules.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Saved {output}")


if __name__ == "__main__":
    app()
