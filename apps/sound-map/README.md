# Whale and Dolphin Orchestra

Click recording sites on the world map to seat whales and dolphins in the orchestra,
then compose one piece from all their measured phrases with ACE-Step 1.5. While it
plays, each recording site pulses on its own onsets and the arcs between players
light up.

This is a **pre-project prototype for the HIFMB × HWK ArtWaves residency proposal**
([call](https://hifmb.de/transfer/art-science/air/)), live at
[whales.liviazaharia.com](https://whales.liviazaharia.com/); the main
[README](../../README.md) has screenshots.
The interface takes its visual cues from a vineyard concert hall: curved seating
terraces, timber, ivory and brass, alongside warm paper and editorial typography.
An AI-generated ocean-atlas illustration of whales and dolphins inside a hall forms
a fixed decorative background at 42% opacity (32% on phones), visible around the
geography inside the map frame. Copy, spectrograms and controls have their own
surfaces; the backdrop cannot intercept pointer events. The map uses the full
rectangular viewport, with no seating overlay or oval mask hiding recording sites.
Six larger chairs show species silhouettes as recordings join the orchestra. The
desktop map is capped at 480 px high to keep the seating close to the geography.
Icons are from PhyloPic: Chris huh (humpback, dolphin and orca) and Margot Michaud
(sperm whale); sources and credits are bundled in `demo/follow/species/credits.json`.
The selected artwork and its
generation prompt are bundled in `demo/follow/concert-hall-atlas-v1.png` and
`concert-hall-atlas-v1.prompt.json`.

The artistic premise is to make marine biodiversity audible through an imagined
symphony for human ears. DCLDE killer-whale excerpts meet recordings from other
waters; measured rhythms and contour shapes guide ACE-Step while the original
voices remain playable. The technical tab links the dataset paper and scopes its
"largest" claim to curated DCLDE audio and annotations at publication in 2025.

- **Concert hall:** a title and one paragraph above a map spanning the available
  screen width; playable original recordings below it, ensemble controls, and finished
  pieces. A highlighted programme to the right of the desktop map opens by default,
  with larger piece titles and a **Listen now** button for immediate playback.
  Choosing a piece from its list fills the orchestra without starting playback.
  On phones the programme appears above the geography. The current piece shows individual source
  excerpts on a shared timeline, then the combined guide and generated composition.
- **Technical score:** Input → Schema → Guide → Output diagrams; a recording selector
  with actual spectrograms, measured onsets and pitch contours, playable original and
  guide audio; composition scores, fine-tuning, model controls, and engine logs.
  `?view=technical` opens this tab, including alongside a `#<piece id>` link.
- **Installation:** the proposed physical room, led by two AI-generated concept
  images: an oak table with a printed ocean map, tactile whale and dolphin figures
  with selection buttons, a large wall display of recorded → measured → generated
  sound, and speakers around the visitors. One button selects one recording; pressing
  again removes it, with a light and the screen confirming up to six seated voices.
  A small touchscreen handles composition and playback. The original recordings and
  guides could be routed to separate speakers; generated music is a shared mix.
  A three-step visit and the physical setup form the main page; build details and
  scientific collaborations expand below, with a link to the separate Silver tab.
  The room is a proposal to build with residency or other
  funding; hardware selection, screen synchronisation and spatial playback still need
  development. Images and generation prompts are in `demo/follow/installation/`,
  preserved by the demo refresh and included in the static export. `?view=installation`.
- **About:** Livia Zaharia and Anton Kulaga, with links and the GitHub repository.
  `?view=about`. Photos are in `demo/follow/about/` and are copied by the export.

- **Seating:** a site with one recording toggles it on click; a site with several opens
  a short list with "Seat all". The recordings list below the map seats, removes and
  previews every recording and shows its spectrogram with the measured calls.
- **Map:** zoom presets (All sites, North-east Pacific, Salish Sea, World) frame the
  clustered hydrophones. Seated sites get a halo and their seat numbers.
- **Orchestra:** controls directly below the map list the players without covering
  the geography or species seats. Use × to
  remove one and **Together** or **In sequence** to arrange them. **Compose piece** turns into
  **Update piece** after any change and **Play** when the current piece matches the ensemble.
  **New take** keeps the players with a new ACE-Step seed. Ctrl+Enter triggers the
  main button.
  Compose and Play are large, centered actions. During composition, an activity
  bar stays visible and the status follows the engine's current stage. A CPU
  notice appears only if the ACE-Step environment reports that CUDA is absent.
- **Presets:** a piece is named only when saved as a preset under the result. Opening
  any programme piece seats its players again; use Play to listen, or change the
  ensemble to compose a variation. The drawer's Escape key collapses it.
- **Keyboard:** arrow keys, Home, and End navigate the tabs. Spectrograms support
  arrow-key seeking, Home, and End, and map sites respond to Enter and Space.

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
`bun run dev`. The server falls back to `demo/follow/`, a committed bundle of the 20 source
excerpts and 22 finished combinations (MP3 stems and WebP spectrograms in Git LFS). It also
carries `presets.json`, the names of its presets, which the server reads beneath any saved in
`data/output/follow`. Anything in `data/output/follow` takes precedence. Making new combinations still
needs the pipeline. Refresh the bundle with `bun scripts/demo.ts [id,id,...]`; its
`README.md` lists the recordings.

Environment, read from the repository's `.env` by `uv run start` and both Bun scripts:
`ORCHESTRA_PORT` (3070), `ORCHESTRA_HOST` (127.0.0.1); `PORT` and `HOST` still work.
`WHALES_ROOT` overrides the repository root.
The server binds to localhost and runs one combination at a time, because the GPU is shared.

ACE-Step selects CUDA through `torch.cuda.is_available()`, otherwise CPU. CPU
inference uses float32 without GPU quantization or offloading; allow enough RAM
and a longer wait. `uv run start --ace yes` installs ACE-Step even without an
NVIDIA GPU. `/api/runtime` probes the same isolated Python environment as the
runner; an unavailable environment is reported as unknown, not as CPU-only.
Static hosting plays the exported pieces and does not run composition.

## How it fits together

| File | Role |
|---|---|
| `server.ts` | `/api/catalog`, `/api/combos`, `/api/combos/:id`, `POST /api/combos/:id/preset`, `POST /api/combine`, `/files/*` from `data/output/follow` (falling back to `demo/follow`) |
| `src/map.ts` | Equal Earth map from `resources/maps/world-countries-110m.geojson`, catalogue dataset dots, sites, arcs, pulses |
| `src/composer.ts` | The orchestra: seat/remove/load players, trims, offsets, gains, registers, ACE-Step options and seed, timeline preview |
| `src/player.ts` | WebAudio playback: every stem starts on the same clock; toggles change gains only |
| `src/lanes.ts` | Spectrogram lanes with each part's onsets and contours, envelopes, scores |
| `src/lib/` | Pure logic shared by UI, server and tests |
| `src/silver.ts`, `src/silver.css` | The **Sound to silver (optional)** tab (`?view=silver&idea=bend`): six idea tabs, with the live bench and moving-silver studies embedded from `/silver/files/` (`data/output/silver`, else `demo/silver`; refresh the copy with `bun scripts/silver.ts`). `/silver` redirects to it; the static export hides it |

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
renders anew. A complete earlier render with the same id is reused instantly, and
`--rerender` forces a fresh one. The app also remembers which orchestras it has already
rendered in the session, so going back to one opens it without calling the server.

Each part is scored only while it plays: timing z of the output's onset envelope against
that part's onsets, versus the same window shifted in time. In a layered piece this shows
which phrase the music follows.

Locations: Orcasound Lab uses the published hydrophone position from the DCLDE deployment
table. Dolphin Reef (Eilat) and the Dominica study region are approximate site anchors,
drawn as diamonds, because the clips carry no coordinates.
