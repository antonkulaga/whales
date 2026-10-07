# Local experiment data

`input/world-map/` contains metadata-only Watkins, Madeira, SanctSound and NOAA
snapshots plus saved taxonomy responses. `output/world-map/` contains summary,
species/location CSV and GeoJSON exports. See the
[world-map guide](../docs/world-map.md) for sources, byte counts and rebuilding.

- `input/`: original downloaded audio, source manifests and copies of artwork.
- `interim/`: CLAP scores, preprocessing/controls and Hugging Face checkpoint cache.
- `output/`: generated PNGs, contact sheets, standalone listening galleries and full provenance manifests.
- `output/brush/`: the sound-brush study. It holds emitted WAVs, audible guides, controls/stroke JSON, SVG drawings, explanatory figures, `learned.json` and `manifest.json`. Live MIDI phrases go to `output/brush/live/`, and replay copies to `interim/brush-replay/`.

Local contents of all three directories are ignored by Git. The directory
placeholders and this description are tracked. Recreate the Livia experiments
with `uv run --group art main.py art livia`, using the sibling `livia` and
`livistone` checkouts (or supply `--livia-dir` and `--livistone-dir`).
The gallery keeps copies of its source audio and artist references beside the images, so it can be
opened locally or served without depending on another checkout.
The earlier generic palette is preserved in `interim/superseded-generic/`.

`input/openwhistle-classification/balanced/` holds the pinned OpenWhistle parquet
shards for the Hardata II pilot; `interim/inscription/` keeps groove heightmaps
and `output/inscription/` the gallery, decoded audio, STL bands and
`results.json`. `input/dclde/` also holds the small DAS pick tables, the authors'
batch-1 localizations, the aerial survey and DORI labels used by
`dclde_opportunities.py`, with `opportunities-sources.json` hashes.

`input/dclde/Annotations.csv` is the full NOAA orca annotation release, downloaded
without recordings. `output/dclde/` contains summary Markdown/JSON, categorical
and daily CSV tables, and distribution plots. Reproduce with `uv run main.py
dclde metadata`, `uv run main.py dclde summary`, and `uv run --group viz main.py
dclde charts`. Model downloads live separately under `models/dclde/`.
