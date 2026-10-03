# Whales: sound, identity, and form

An exploration repo for Livia's marine art residency proposal: discover what
cetacean recordings actually annotate, then experiment with sound-driven shapes
and images. Start with the data and context before choosing a training task.

## Research

- [Dataset guide — contents, exact labels, context, scale, and access](docs/datasets.md)
- [Model guide — inference readiness, papers, GitHub/HF, dates, sizes, dependencies, and licenses](docs/models.md)
- [Artistic experiments — ten combinations of audio, visual, and sound models](docs/artistic-experiments.md)
- [Research overview and experiment plan](docs/research.md)
- [Dolphin datasets and social context](docs/dolphin-datasets.md)
- [Whale datasets and annotations](docs/whale-datasets.md)
- [Detailed model audit and visual conditioning notes](docs/audio-models.md)
- [Machine-readable dataset inventory](resources/datasets.json)
- [Observed Hugging Face schemas](resources/audits/)

The inventory was checked on **4 October 2026**. A source's public availability
does not establish its reuse license. Unknown fields and terms are identified
in the reports.

## Run

Install [uv](https://docs.astral.sh/uv/) and run from this directory. The project
uses Python 3.12 (`>=3.11,<3.14`) to support modern ML dependencies such as AVEX.
Legacy WhAM/ImageBind environments should be separate experiments.
The locked core dependencies are Polars 1.44.2 for table export, Hugging Face
Hub 2.1.1 for Hub metadata/authentication, and Typer 0.27.2 for the CLI.

For a new checkout, copy `.env.template` to `.env` and set `HF_TOKEN` locally
when authenticated Hub access is needed. Use `uv run --env-file .env` to load
those settings; the local `.env` is ignored. `HF_HOME` keeps the Hub cache in
`data/huggingface`, which is also ignored.

```bash
# Curated inventory; no network
uv run main.py catalog
uv run main.py catalog --json
uv run main.py catalog --csv outputs/datasets.csv

# Inspect live metadata, labels, config-specific IDs, and splits; no audio download
uv run main.py inspect dolphinteam/OpenWhistle-Classification-Finetuning
uv run main.py inspect orrp/DSWP --output outputs/dswp-schema.json
uv run --env-file .env main.py inspect orrp/DSWP

# Draw six public F0 tracks and a simple artistic transformation
uv run --group viz main.py contours --limit 6

# Check label handling and preservation of uncertain contour gaps
uv run python -m unittest discover -s tests -v
```

`contours` writes `outputs/openwhistle/contours.png`, `contours.svg`, and
`annotations.json`. It queries a small Hugging Face Viewer row range and does
not download waveform files, whole corpora, or weights. The optional `viz`
dependency group installs matplotlib. Example selection is a contiguous viewer
slice, **not** a balanced sample or a training/evaluation split.

The left panel shows frequency over time. The right panel maps relative time
to angle and frequency to radius using a common 3–22.05 kHz scale. Points below
the chosen F0 confidence threshold are omitted and leave gaps; tracks rejected
by upstream `f0_ok` are not drawn. The shapes are artistic transformations, not
decoded messages. Confidence filtering does not establish that a track is
biologically correct. Read the raw tracks and inspect spectrograms before
interpreting patterns.

```bash
uv run --group viz main.py contours --config all-review-sample \
  --split test --offset 10 --limit 8 --min-confidence 0.5 \
  --output outputs/other-contours
```

The annotation export preserves the label name, source row, recording timing,
F0 arrays, quality fields, source URL, inspection time, and transformation
parameters. Live Viewer queries are not pinned to a data revision. The recorded
Hub revision documents the inspection but does not guarantee the Viewer served
that revision. `resources/audits` records schemas, not audio or model evaluation.

## Next experiments

1. **Whistle portraits:** compare frequency contours with a frozen
   OpenWhistle encoder; investigate signature types without assuming caller ID.
2. **Sound in context:** align recordings with observed behavior in DOLPHINFREE;
   treat group-minute activity labels separately from individual call meaning.
3. **Whale rhythms:** inspect the sperm-whale timing/dialogue tables; keep their
   provenance separate from the audio-only DSWP Hugging Face release.
4. **Visual controls:** compare direct acoustic features, CLAP/BioLingual text
   alignment, and a learned mapping to Livia's chosen visual parameters.

No audio model has been trained or benchmarked here yet. Raw data, checkpoints,
and generated experiments are ignored by Git; the uv lockfile and schema audits
are retained.

Use `data/` for downloaded recordings, `models/` for weights, and `outputs/`
for generated experiments. The ignore rules also cover alternate `.venv*`
environments, model/data binaries, archives, caches, run logs, and local secret
files. Documentation, notebooks, JSON metadata audits, `.python-version`, and
`uv.lock` stay in version control; `.env.template` may be
committed with placeholder values. Selected shared media belongs in `assets/`
and uses the Git LFS rules in `.gitattributes`:

```bash
git lfs install --local
git add assets/<filename>
git lfs ls-files
```

The installed pre-push hook uploads any selected LFS assets. The current
research snapshot includes source, docs, and JSON metadata; no recordings or
model weights are included.
