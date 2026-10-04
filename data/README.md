# Local experiment data

- `input/`: original downloaded audio, source manifests and copies of artwork.
- `interim/`: CLAP scores, preprocessing/controls and Hugging Face checkpoint cache.
- `output/`: generated PNGs, contact sheets, standalone listening galleries and full provenance manifests.

Local contents of all three directories are ignored by Git. The directory
placeholders and this description are tracked. Recreate the Livia experiments
with `uv run --group art main.py art livia`, using the sibling `livia` and
`livistone` checkouts (or supply `--livia-dir` and `--livistone-dir`).
The gallery keeps copies of its source audio and artist references beside the images, so it can be
opened locally or served without depending on another checkout.
The earlier generic palette is preserved in `interim/superseded-generic/`.
