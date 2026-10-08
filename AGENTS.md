# AGENTS.md

Guidance for coding agents working in this repository. The README explains the
project for people; this file covers what you need to change it safely.

## What the project is

- **Whale and Dolphin Orchestra** (main focus): click recording sites on a map to
  seat whales and dolphins, then compose one piece from their measured phrases with
  ACE-Step 1.5. App in `apps/sound-map/`, engine in `experiments/follow*.py`
  (`main.py follow ...`), method in `docs/follow-the-phrase.md`.
- **Sound to silver** (in progress): sound shapes Livia's cast-silver jewelry. The
  Hardata II inscription pilot is implemented (`main.py inscription`,
  `docs/hardata-ii-pilot.md`); bending whole rings has started in
  `experiments/silver.py` with `resources/sound-silver.json`.
- **Research** behind both: datasets, models, DCLDE 2027, art precedents and
  proposals, all in `docs/`.

## Layout

| Path | Contents |
|---|---|
| `main.py` | Typer CLI: `catalog`, `inspect`, `contours`, and the `art`, `dclde`, `follow`, `inscription` groups |
| `orchestra.py` | `uv run start` / `uv run stop` (console scripts in `pyproject.toml`): one-command setup and a background server |
| `experiments/` | Experiment modules: CLAP/FLUX art, sound brush, follow the phrase, inscription, silver |
| `apps/sound-map/` | Bun + TypeScript orchestra app: `server.ts`, `src/`, `tests/`, `scripts/demo.ts`, `scripts/export.ts` |
| `apps/sound-map/demo/follow/` | Committed playback bundle (Git LFS) so a fresh clone plays without the pipeline |
| `resources/` | Tracked configs and small audits: `follow-music.json`, `sound-brush.json`, `sound-silver.json`, `audits/`, `maps/` |
| `docs/` | Reports; `docs/atlas/` is a static page |
| `tests/` | Python `unittest` suite |
| `data/input`, `data/interim`, `data/output` | Downloads, caches and generated outputs. Git-ignored: never commit them |

ACE-Step 1.5 lives in its own uv environment at `data/interim/tools/ACE-Step-1.5`.

## Commands

```bash
# Whole orchestra: set up what is missing, serve in the background; settings in .env
uv run start                # --port, --host, --ace auto|yes|no override ORCHESTRA_* in .env
uv run stop

# Python 3.12 via uv (pyproject allows >=3.11,<3.14); optional groups: art, viz, mesh, midi
uv run python -m unittest discover -s tests
uv run --group art --group viz main.py follow catalog

# Orchestra app
cd apps/sound-map
bun install
bun test && bun run typecheck
bun run dev                 # http://127.0.0.1:3070; ORCHESTRA_PORT/HOST from ../../.env, WHALES_ROOT
bun scripts/demo.ts         # refresh demo/follow from data/output/follow
bun scripts/silver.ts       # refresh demo/silver (the Sound to silver tab's media) from data/output/silver, docs and jewelry renders
bun run export              # static copy into data/output/follow (atlas.html and friends)
```

Run the Python tests and `bun test` plus `bun run typecheck` before you commit
changes in their areas.

## Conventions

- **Tooling:** uv for dependencies, `pathlib.Path` for paths, Typer for commands,
  Polars for tables. Add isolated dependency groups when model stacks conflict.
- **Data and media:** generated files stay under `data/`. Shared media goes through
  Git LFS (`.gitattributes` covers audio, images, weights and archives). The demo
  bundle is the deliberate exception that is committed; `.gitignore` re-allows its MP3s.
- **One GPU, shared:** the server runs one combination at a time. Check before
  starting long ACE-Step or FLUX jobs; other sessions may be using the GPU.
- **Piece ids hash the whole config:** a combination's id covers the resolved spec
  and `resources/follow-music.json`. Editing that file re-renders every piece. Preset
  names live in `data/output/follow/presets.json`, never in specs, so naming never
  changes an id.
- **Renders are reused:** a complete earlier render with the same id is returned without
  recomputing anything. Bump `RENDER_VERSION` in `experiments/follow_combine.py`
  whenever rendering, response or scoring code changes, so stale renders get rebuilt.
  `main.py follow combine --rerender` rebuilds a single piece.
- **`index.html` anchors:** `scripts/export.ts` parses `<title>`, the `./style.css`
  link and the `./main.ts` script tag. Keep them when editing the page.
- **Pages and galleries** follow Input → Schema → Output. Keep original recordings
  playable, and label recorded, measured and generated material separately.
- **Visual design:** the project owner dislikes too many separate panels and
  slogan-like headings. Prefer one clear composition and concise copy; don't repeat
  what an image or interaction already shows. Setup concepts should be image-led,
  with selections updating one central preview.
- **Readable, continuous pages:** preserve background artwork in open areas and
  keep body text on a calm surface with enough opacity to read clearly. Use normal
  readable body type and ordinary paragraphs
  for related explanations; do not split short copy into cards, bordered panels,
  side notes or separate heading strips.
- **Links and navigation:** do not append diagonal arrows or external-link icons
  to links or buttons. Remove redundant standalone "explore", "read more", "back"
  and "open full screen" links that repeat navigation or linked titles. Put useful
  source and credit links directly in the relevant text.
- **Ring animation:** integrate the viewer directly into the project page, using
  the full available width and one page scrollbar. Do not embed a second scrolling
  page in an iframe. Make playback prominent, with large recording choices in a
  right sidebar; omit obscure laboratory controls from the project view. Show the
  selected cast ring as a small photograph below the animation. Never reserve a
  side column for the photograph or add a fullscreen link as a layout workaround.
- **Claims:** onsets and pitch contours come from signal analysis; ACE-Step and FLUX
  are generative models. Never present an output as decoded animal meaning.
- **Licenses:** this is an art and research project. Credit sources, but don't add
  license caveats, risk notes or license audits.
- **Silver forms** open outward from an exposed stone. Earlier rib cages read as
  imprisonment.
- **Availability claims:** before calling a model or checkpoint unavailable, search
  the Hugging Face Hub properly (organization listings, tags, Spaces). Many "Whale",
  "Orca" and "Dolphin" repos are unrelated text models (for example `dphn`).

## Working alongside other sessions

Several agent sessions often edit this repository at the same time.

- Run `git status` before editing. `README.md`, `main.py`, `pyproject.toml`,
  `uv.lock` and `docs/` are shared, so make targeted edits there.
- Never revert or reformat someone else's uncommitted work.
- Tell the other sessions which files you are taking over.
- Commit only the files you changed, and leave commits of other sessions' work to
  the user.
