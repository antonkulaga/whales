# Whale and Dolphin Orchestra

Click recording sites on the world map to seat whales and dolphins in the orchestra,
then compose one piece from all their measured phrases with ACE-Step 1.5. While it
plays, each recording site pulses on its own onsets and the arcs between players
light up.

- **Seating:** a site with one recording toggles it on click; a site with several opens
  a short list with "Seat all". The recordings list under the map seats, removes and
  previews every recording and shows its spectrogram with the measured calls.
- **Map:** zoom presets (All sites, North-east Pacific, Salish Sea, World) frame the
  clustered hydrophones. Seated sites get a halo and their seat numbers.
- **Dock:** a bar pinned to the bottom of the window lists the players. Use × to
  remove one and Layer or Sequence to arrange them. **Compose piece** turns into
  **Update piece** after any change and **Up to date** when nothing changed.
  **New take** keeps the players with a new ACE-Step seed. Ctrl+Enter triggers the
  main button.
- **Presets:** a piece is named only when saved as a preset under the result. Opening
  any saved piece seats its players again.

The app is Bun + TypeScript. Measurement, guides, the deterministic response, ACE-Step
and scoring all run in Python (`main.py follow combine`); the server writes a spec, runs
that command and streams its log back as NDJSON.

## Run

From the repository root, `uv run start` does everything below and serves the app in the
background; `uv run stop` stops it (see `orchestra.py`). The same steps by hand:

```bash
# Once, from the repository root: inputs, stems and the catalog
uv run --group art --group viz main.py dclde metadata    # annotations that cut the orca excerpts
uv run --group art --group viz python -c "from experiments.data import Layout, fetch_long_samples; fetch_long_samples(Layout())"
uv run --group art --group viz main.py follow fetch
uv run --group art --group viz main.py follow prepare
uv run --group art --group viz main.py follow catalog
# ACE-Step 1.5 (optional): clone into data/interim/tools/ACE-Step-1.5 and `uv sync` there

cd apps/sound-map
bun install
bun run dev        # http://127.0.0.1:3070, reloads on edits
bun test           # arrangement, pulse and path-safety logic
bun run typecheck
```

On a fresh clone you can skip the Python steps: `git lfs pull`, then `bun install` and
`bun run dev`. The server falls back to `demo/follow/`, a committed bundle of the 14 source
excerpts and 10 finished combinations (MP3 stems and WebP spectrograms in Git LFS, about
65 MB). Anything in `data/output/follow` takes precedence. Making new combinations still
needs the pipeline. Refresh the bundle with `bun scripts/demo.ts [id,id,...]`; its
`README.md` lists the recordings.

Environment, read from the repository's `.env` by `uv run start` and both Bun scripts:
`ORCHESTRA_PORT` (3070), `ORCHESTRA_HOST` (127.0.0.1); `PORT` and `HOST` still work.
`WHALES_ROOT` overrides the repository root.
The server binds to localhost and runs one combination at a time, because the GPU is shared.

## How it fits together

| File | Role |
|---|---|
| `server.ts` | `/api/catalog`, `/api/combos`, `/api/combos/:id`, `POST /api/combos/:id/preset`, `POST /api/combine`, `/files/*` from `data/output/follow` (falling back to `demo/follow`) |
| `src/map.ts` | Equal Earth map from `resources/maps/world-countries-110m.geojson`, catalogue dataset dots, sites, arcs, pulses |
| `src/composer.ts` | The orchestra: seat/remove/load players, trims, offsets, gains, registers, ACE-Step options and seed, timeline preview |
| `src/player.ts` | WebAudio playback: every stem starts on the same clock; toggles change gains only |
| `src/lanes.ts` | Spectrogram lanes with each part's onsets and contours, envelopes, scores |
| `src/lib/` | Pure logic shared by UI, server and tests |

A combination spec looks like this:

```json
{
  "title": "Haro Strait answers Dominica",
  "arrangement": "layer",
  "gap_s": 1.0,
  "parts": [
    {"source": "humpback-a", "offset_s": 0},
    {"source": "sperm-b", "offset_s": 4, "gain_db": -3, "trim_s": [0, 20]}
  ],
  "ace": {"task": "cover", "audio_cover_strength": 0.6}
}
```

The same file works from the command line:
`uv run --group art --group viz main.py follow combine spec.json`. Results go to
`data/output/follow/combos/<id>/` (Git-ignored); open `http://127.0.0.1:3070/#<id>` to
see one. The id hashes the resolved spec and the experiment config, so changing either
renders anew.

Each part is scored only while it plays: timing z of the output's onset envelope against
that part's onsets, versus the same window shifted in time. In a layered piece this shows
which phrase the music follows.

Locations: Orcasound Lab uses the published hydrophone position from the DCLDE deployment
table. Dolphin Reef (Eilat) and the Dominica study region are approximate site anchors,
drawn as diamonds, because the clips carry no coordinates.
