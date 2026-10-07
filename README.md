# Whale and Dolphin Orchestra

<p align="center">
  <a href="https://whales.liviazaharia.com/"><img src="docs/screenshots/now-playing.png" width="100%" alt="The piece Giants and singers: spectrograms of a blue whale, a humpback, a fin whale and a killer whale on one timeline, above the combined guide built from their calls and the music generated from it"></a>
</p>
<p align="center"><sub><b>Giants and singers</b>, a blue whale, a humpback, a fin whale and a killer whale.
Top: their recordings on one timeline. Middle: the guide built from their measured calls.
Bottom: the music ACE-Step 1.5 generated from that guide.</sub></p>

<p align="center">
  <a href="https://whales.liviazaharia.com/"><b>Live prototype</b></a> ·
  <a href="#play-the-orchestra">Run it locally</a> ·
  <a href="docs/follow-the-phrase.md">How the music follows the animals</a> ·
  <a href="#next-sound-to-silver-in-progress">Sound to silver</a> ·
  <a href="#documentation">Research</a>
</p>

Click recording sites on a world map to seat whales and dolphins in an orchestra,
then hear one piece composed from all of them. Every player is a real recording:
humpback song from Haro Strait, killer-whale calls from the Salish Sea and Alaska,
sperm-whale codas from Dominica and bottlenose dolphin whistles from Eilat. Audio
analysis measures each call's onset and pitch contour. A guide plays those
measurements in an instrument and register per species, and ACE-Step 1.5, a
generative music model, composes the piece from the combined guide. While it
plays, every site pulses on its own calls, and spectrograms show what the analysis
measured and what the model made.

The repository also holds the research behind it, made for Livia's marine art
residency proposal: which recordings exist, what their labels support, which
models can use them, and what artists have already done with cetacean sound.

**Live:** [whales.liviazaharia.com](https://whales.liviazaharia.com/), the working
prototype for the HIFMB × HWK [ArtWaves residency](https://hifmb.de/transfer/art-science/air/).

| 1 · Recorded | 2 · Measured | 3 · Guide | 4 · Generated |
|---|---|---|---|
| Short hydrophone excerpts from NOAA's DCLDE workshops and AWI's polar moorings | Onsets, durations, click groups and pitch contours, from signal analysis | Each species plays its measurements on its own instrument and register | ACE-Step 1.5 composes one piece from the combined guide |

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/concert-hall.png" alt="Concert hall: a world map with four dolphin recording sites joined by arcs from Palmyra Atoll to Eilat, beside the list of finished pieces"></td>
    <td width="50%"><img src="docs/screenshots/seated-orchestra.png" alt="Four dolphins seated on the stage, with the recordings they came from"></td>
  </tr>
  <tr>
    <td><b>Concert hall.</b> Choose recording sites on the map, or play a finished piece. Arcs join the players of <i>Whistles across three oceans</i>.</td>
    <td><b>The orchestra.</b> Each seated voice is a real recording that can be played on its own.</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/technical-score.png" alt="Technical score: recorded, measured, constructed and generated stages"></td>
    <td><img src="docs/screenshots/installation.png" alt="Installation concept: visitors around a printed ocean map table with whale figures and a wall screen"></td>
  </tr>
  <tr>
    <td><b>Technical score.</b> From the recording to the measured phrase, the guide and the generated music.</td>
    <td><b>Installation.</b> The proposed listening room (AI-generated concept image).</td>
  </tr>
</table>

Screenshots of the app, taken 8 October 2026.

## Play the orchestra

With [uv](https://docs.astral.sh/uv/) and [Bun](https://bun.sh) installed:

```bash
uv run start           # set up what is missing, then serve http://127.0.0.1:3070 in the background
uv run stop            # stop the server
```

`uv run start` does each step only when it is missing, so after the first run it
takes a second or two:

1. creates `.env` from `.env.template`;
2. pulls the demo bundle (20 recordings and 22 finished pieces) with Git LFS;
3. installs the app's packages with Bun;
4. downloads and measures the recordings, then writes the catalog;
5. with an NVIDIA GPU, installs ACE-Step 1.5 into `data/interim/tools/ACE-Step-1.5`,
   with the code and weights pinned to the versions that made the demo pieces
   (about 22 GB, once);
6. starts the server, which logs to `data/interim/orchestra/server.log`.

When a step fails, it prints a warning with the fix and the rest carries on. Without
Git LFS the finished demo pieces are missing. Without ACE-Step a piece keeps its guide
and deterministic response. Only a missing Bun or a busy port stops the start. Set
the port, host and ACE-Step choice in `.env` (`ORCHESTRA_PORT`, `ORCHESTRA_HOST`,
`ORCHESTRA_ACE`) or per run (`uv run start --port 3071 --ace no`); `bun run dev`
reads the same `.env`.

ACE-Step automatically uses CUDA when available and falls back to CPU otherwise.
For a CPU-only installation, run `uv run start --ace yes` (or set
`ORCHESTRA_ACE=yes`). CPU generation needs sufficient RAM for the model and takes
longer; finished pieces play immediately on either kind of server. Compose shows
an activity bar and the engine's current stage, with a CPU notice only when the
server detects no CUDA.

- **Seat players.** Click a site to seat its recording and click again to remove it.
  A site with several recordings opens a short list. The recordings list under the
  map works too, with a Listen button and a spectrogram strip for each recording.
- **Compose.** The dock at the bottom shows who is seated. Remove a player with ×,
  choose layered or sequenced, then press **Compose piece**. After any change the
  button becomes **Update piece**; **New take** keeps the players and asks
  ACE-Step for another seed. Ctrl+Enter does the same as the button.
- **Keep what you like.** Naming waits until you want to keep a piece: **Save
  preset** under the result. Presets and recent pieces are listed at the bottom,
  and opening one seats its players so you can change it and update.

The individual steps behind `uv run start` are listed in
[apps/sound-map/README.md](apps/sound-map/README.md#run). An orchestra holds up to six players (`combination.max_parts` in
`resources/follow-music.json`). Without ACE-Step a piece still renders its guide
and a deterministic response. The method, the measurements and the tests of
whether the music follows the animals are in [Follow the phrase](docs/follow-the-phrase.md);
the app is described in [apps/sound-map/README.md](apps/sound-map/README.md).

## Next: sound to silver (in progress)

The second idea turns sound into Livia's own material: a recording bends one of
her cast-silver rings (Inline, Roots). Time runs along the metal, pitch lifts the
band along the finger, level swells it outward and pitch slope leans it, while
casting checks guard wall thickness, gaps and the finger bore. The bending study
has run on both rings: Roots moves by up to 4 mm and Inline by about 2 mm, the
finger hole is unchanged in all 20 runs, and a live 3D bench plays each recording
while the ring bends ([report](docs/sound-to-silver-bending.md)). Animated studies
keep the metal moving after casting: ferrofluid stones, hinged nitinol, magnetic
fins and memory cells. Nothing has been cast yet.

All of it is in the orchestra app's **Sound to silver (optional)** tab, after
Installation, with the bench and the animations running inside it.

<p align="center">
  <img src="docs/screenshots/sound-to-silver.png" width="100%" alt="Sound to silver: a whistle bends Livia's cast-silver rings">
  <br><sub>The Sound to silver tab: whistles bend Livia's rings within casting limits.</sub>
</p>

One silver piece already exists as a pilot. **Hardata II** (implemented and run)
engraves a dolphin whistle as a contour groove around a ring band and reads it back
into sound. A 2026 dolphin encoder kept 75% of its whistle-type score from a
272-bit groove (macro-F1 0.62 against 0.82 on the original audio). Run it with
`uv run --group art main.py inscription fetch|run|matched`; see the
[pilot report](docs/hardata-ii-pilot.md) and the [visual atlas](docs/atlas/index.html).

Other steps toward silver: CLAP-directed jewelry concepts and silver geometry
studies ([artistic experiments](docs/artistic-experiments.md)) and the human
[sound brush](docs/sound-brush.md). [Livia's brief](docs/livia-experiment-brief.md)
describes the pieces these build on.

The same move, measured biology shaping a printable form, drove
[Materialized Enhancements](https://enhancement.bio/), started at the CODAME
ART+TECH festival *The New Human* in Milan in 2026 by the GlucoseDAO and Longevity
Genie team ([source](https://github.com/longevity-genie/materialized-enhancements)).
Visitors pick real genes from real organisms, such as tardigrade radiation
shielding or naked-mole-rat cancer resistance. Livia's parametric geometry turns
the protein properties of their picks into a 3D-printable Voronoi crystal.

## Documentation

**Orchestra and music**

- [Follow the phrase — measured guides, ACE-Step 1.5 accompaniment and covers, and swap/perturbation tests of whether music follows an animal phrase](docs/follow-the-phrase.md)
- [Orchestra app — server, demo bundle and static export](apps/sound-map/README.md)

**Data**

- [Dataset guide — contents, exact labels, context, scale, and access](docs/datasets.md)
- [Dolphin datasets and social context](docs/dolphin-datasets.md)
- [Whale datasets and annotations](docs/whale-datasets.md)
- [DCLDE 2027 — challenge tasks, inspected downloads, useful models, and starting experiments](docs/dclde-2027.md)
- [DCLDE label audit — what population, spatial and abundance labels actually support](docs/dclde-opportunities.md)
- [World map of dataset locations](docs/world-map.md)
- [Machine-readable dataset inventory](resources/datasets.json) · [observed Hugging Face schemas](resources/audits/) · [DCLDE file and model-package audit](resources/audits/dclde-2027.json)

**Models**

- [Model guide — inference readiness, papers, GitHub/HF, dates, sizes, dependencies, and licenses](docs/models.md)
- [Detailed model audit and visual conditioning notes](docs/audio-models.md)
- [2026 art models — actual interfaces, release evidence, explanatory figures and limitations](docs/2026-art-models.md)

**Art research and ideas**

- [Research overview and experiment plan](docs/research.md)
- [Five ideas investigated — music, sound drawing, dolphin images and annotated maps](docs/2026-art-ideas.md)
- [Existing art projects — whale music, sound-driven visuals, dolphin painting and CHAT](docs/cetacean-art-precedents.md)
- [CHAT in detail — hardware pictures, shared sound/action interfaces and the drawing proposal](docs/chat-sound-interface.md)
- [Artistic experiments — implemented outputs and revised brainstorming](docs/artistic-experiments.md)
- [Sound brush — keyboard → emitted waveform → recognized contour → stroke, with replay checks and an OpenWhistle comparison](docs/sound-brush.md)
- [Hardata II pilot — how many inscribed bits keep a dolphin whistle's type, and a simulated silver groove](docs/hardata-ii-pilot.md)
- [Sound to silver bending — whistles bend Livia's Inline and Roots rings at print resolution without tearing; casting checks find each sound's safe limit](docs/sound-to-silver-bending.md)
- [Eight new science-and-art proposals — ranking, recommended pilot and reading map](docs/novel-projects.md) · [experimental plans](docs/novel-experimental-plans.md) · [prior art](docs/novel-prior-art.md) · [novelty assessment](docs/novel-novelty-assessment.md) · [visual atlas of all six reports](docs/atlas/index.html) (open in a browser; playable pilot clips)

**For coding agents:** [AGENTS.md](AGENTS.md) covers the layout, commands and conventions.

The inventory was checked on **4 October 2026**. A source's public availability
does not establish its reuse license. Unknown fields and terms are identified
in the reports. The linked art investigation was checked on **7 October 2026**.
Its proposed experiments have not been locally benchmarked, except the human sound
brush, which is implemented and measured in [docs/sound-brush.md](docs/sound-brush.md),
and the music experiment, measured in [docs/follow-the-phrase.md](docs/follow-the-phrase.md).

## Research toolkit

Install [uv](https://docs.astral.sh/uv/) and run from this directory. The project
uses Python 3.12 (`>=3.11,<3.14`) to support modern ML dependencies such as AVEX.
Legacy WhAM/ImageBind environments should be separate experiments.
The core dependencies are Polars for table export, Hugging Face Hub for
metadata/authentication, and Typer for the CLI. `uv.lock` records exact versions.

For a new checkout, `uv run start` creates `.env` from `.env.template` (or copy it
yourself); set `HF_TOKEN` there when authenticated Hub access is needed. Use `uv run --env-file .env` to load
those settings; the local `.env` is ignored. `HF_HOME` keeps the Hub cache in
`data/interim/huggingface`, which is also ignored.

```bash
# Curated inventory; no network
uv run main.py catalog
uv run main.py catalog --json
uv run main.py catalog --csv data/output/datasets.csv

# Inspect live metadata, labels, config-specific IDs, and splits; no audio download
uv run main.py inspect dolphinteam/OpenWhistle-Classification-Finetuning
uv run main.py inspect orrp/DSWP --output data/interim/dswp-schema.json
uv run --env-file .env main.py inspect orrp/DSWP

# Draw six public F0 tracks and a simple artistic transformation
uv run --group viz main.py contours --limit 6

# Check label handling and preservation of uncertain contour gaps
uv run python -m unittest discover -s tests -v
```

`contours` writes `data/output/openwhistle/contours.png`, `contours.svg`, and
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
  --output data/output/other-contours
```

The annotation export preserves the label name, source row, recording timing,
F0 arrays, quality fields, source URL, inspection time, and transformation
parameters. Live Viewer queries are not pinned to a data revision. The recorded
Hub revision documents the inspection but does not guarantee the Viewer served
that revision. `resources/audits` records schemas, not audio or model evaluation.

## Next experiments

### Hardata II: inscribed whistles and a simulated silver groove

```bash
# Pinned OpenWhistle `balanced` parquet (audio, labels, F0): about 1.2 GB
uv run --group art main.py inscription fetch
# Encode, decode, engrave, probe; writes data/output/inscription/
uv run --group art main.py inscription run
# Exploratory: probe trained on decoded audio (domain shift versus lost information)
uv run --group art main.py inscription matched
uv run --group art python -m unittest tests.test_inscription
```

The gallery `data/output/inscription/index.html` plays each whistle, its decoded
versions and the encoder probe's answers, with unrolled band heightmaps and STL
ring bands. Predictions were registered in the code before the first run. See
the [pilot report](docs/hardata-ii-pilot.md) and the [proposal ranking](docs/novel-projects.md).

### Follow the phrase: music conditioned on a measured animal phrase

```bash
# Humpback FLAC + selection table (12.5 MB) and 16 DSWP codas
uv run --group art --group viz main.py follow fetch
uv run --group art --group viz main.py follow prepare
# ACE-Step 1.5 lives in its own uv environment under data/interim/tools/ACE-Step-1.5
uv run --group art --group viz main.py follow generate --no-offload
uv run --group art --group viz main.py follow evaluate
uv run --group art --group viz main.py follow page
```

`data/output/follow/index.html` plays each recording, its guide, the perturbed
guide, a deterministic response and seven ACE-Step conditions on one playhead,
with timing and pitch scores against swapped and perturbed guides. Predictions
were registered in the code before the first run. See the
[report](docs/follow-the-phrase.md).

To seat several recordings in the [Whale and Dolphin Orchestra](#play-the-orchestra),
run `uv run start`.

### DCLDE label audit for population, spatial and abundance questions

```bash
uv run python dclde_opportunities.py fetch   # ~15 MB of small tables, no audio
uv run python dclde_opportunities.py audit   # resources/audits/dclde-opportunities.json
```

### DCLDE metadata and public orca models

```bash
# Full ~50 MB annotation CSV, with source generation and checksum verification
uv run main.py dclde metadata
uv run main.py dclde summary
uv run --group viz main.py dclde charts

# Only the detector/classifier ONNX weights and small metadata (~94 MB local)
uv run main.py dclde models
```

The CSV is saved in `data/input/dclde/`, reports and charts in
`data/output/dclde/`, and model weights in `models/dclde/`; these downloads are
ignored by Git. This workflow downloads no DCLDE audio. See the
[local results and isolated CPU model check](docs/dclde-2027.md#download-metadata-and-the-public-models-locally).

### Artistic experiments

The first two [artistic experiments](docs/artistic-experiments.md) now have a
local inference implementation. The visual model is **FLUX.2 klein 4B** (January
2026), replacing the proposed SDXL-Turbo checkpoint. The latest compatible
inference stack is in the optional `art` group: Diffusers 0.40.0, Transformers
5.18.0 and PyTorch 2.14.1. Current Diffusers requires Hugging Face Hub below 2,
so the lockfile uses Hub 1.33.0. See the [official FLUX release](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B).

```bash
# Download only six real clips, not entire corpora
uv run --group art main.py art fetch

# Both experiments grounded in Livia's actual jewelry and Livistone
# Defaults use the sibling livia/ and livistone/ checkouts; override as needed
uv run --group art main.py art livia \
  --livia-dir /home/antonkulaga/sources/livia \
  --livistone-dir /home/antonkulaga/sources/livistone

# Cache CLAP acoustic scores, preprocessing and common-reference RMS controls
uv run --group art main.py art analyze
# Or use personal recordings and an edited descriptor/material palette
uv run --group art main.py art analyze --audio-dir /path/to/audio \
  --vocabulary resources/material-vocabulary.json

# Experiment 1: six recordings × jewelry and pavilion concepts, with references
uv run --group art main.py art materials
# Comparison: shuffle the association between audio and descriptors
uv run --group art main.py art materials --shuffle

# Experiment 2: one artwork/jewelry photo × four sound-driven reference edits
uv run --group art main.py art painting --image /path/to/jewelry.jpg

# Fetch, analyze, and generate both experiments in sequence
uv run --group art main.py art demo --image /path/to/jewelry.jpg

# Rebuild the combined input/schema/output overview with Listen buttons
uv run --group art main.py art gallery
uv run --group art main.py art jewelry
# Annotated waveform → CLAP/RMS → original/edited illustration
uv run --group art --group viz main.py art explain
# Longer actual sequences, 5s/15s/full comparisons and direct geometry controls
uv run --group art --group viz main.py art long-forms
# Sound brush: keyboard map, a typed phrase, any WAV, the full study + gallery
uv run --group art --group viz main.py art brush keys
uv run --group art --group viz main.py art brush play "C4:0.8@100 E4:1.0 rest:0.4 F4:0.9"
uv run --group art --group viz main.py art brush draw path/to/sound.wav
uv run --group art --group viz main.py art brush study
# MIDI file or live keyboard (phrase-level loop)
uv run --group art --group viz --group midi main.py art brush play --midi phrase.mid
uv run --group art --group viz --group midi main.py art brush live --list-ports
# Optional local browser preview at http://localhost:8765
uv run --group art python -m http.server 8765 --bind 127.0.0.1 --directory data/output

# Metadata, audio resampling, control bounds and provenance integrity checks
uv run --group art python -m unittest discover -s tests -v
```

`data/input/` contains source audio with hashes and metadata, plus artwork
copies. `data/interim/analysis.json` stores all CLAP cosine scores and controls;
`data/interim/huggingface/` caches checkpoints. `data/output/materials/` and
`data/output/painting/` each contain individual PNGs, a `contact-sheet.png`, a
standalone `index.html` listening gallery, source audio copies and a full
`manifest.json`. Generated data and weights are ignored by Git; the directory
placeholders, source, vocabulary and lockfile are tracked. Defaults are anchored
to the repository via `pathlib`; `--data-dir` allows another root.
`data/output/index.html` combines the experiments into an input → schema → output
overview. Each input has a Listen button, native audio controls, preprocessing,
descriptor scores, material mapping and the actual output prompts. The jewelry
section also displays the original reference image.

The first run downloads approximately 17 GB of official CLAP/FLUX components.
CLAP and image inference run sequentially; FLUX uses bfloat16 and model CPU
offload on CUDA to fit the 16 GB GPU. `--device cpu` is available but much slower.
Weights are cached after the first run. Six contiguous clips (three DSWP and
three OpenWhistle) are exploratory examples, not a representative evaluation.

The [artist brief](docs/livia-experiment-brief.md) connects the experiments to
Nanot of Power's silver lattice, Mitoring's amber and folded silver, Mycelium's
drainage problem, and Livistone's enlargement of jewelry into inhabited spaces.
The original photos are model inputs, not just names in a style prompt. The
gallery labels original works separately from generated concepts and explains
which references each output received. Paths and hashes are recorded in the
manifests; copies of the references travel with the output HTML.

Material studies hold seed, references and composition fixed. The
three-description CLAP palette selects repeated cells, continuous ribbons or
undulating folds in silver around amber; the two scales are a ring and a garden
pavilion. These correspondences are proposed experiment controls. Repeated
descriptor/style combinations intentionally generate identical images.
The edit experiment holds the input
photo, seed and instruction template fixed; CLAP selects a material and RMS
scaled on the shared reference clips selects “very subtle,” “subtle,” or
“moderate.” `--edit-min`/`--edit-max` bound that prompt control. FLUX uses native
reference-image editing, so this is **not denoising strength**. The actual prompt
varies with the sound. These controls need not cause smooth visual changes.
Recording amplitude also depends on gain and distance; CLAP scores are not
probabilities or verified call labels. Audio is mixed to mono, cropped to the
first ten seconds and anti-aliased to 48 kHz without pitch shifting.

`art jewelry` uses the existing CLAP scores to make substantial redesigns of
Mitoring and Mycelium. Clicks select staggered silver terraces, a whistle selects
a sweeping crest, and a wavering sound selects outward opening petals. Every
direction requests a clear change in silhouette, while retaining the natural
stone and wearable ring as reference anchors. There is no RMS-based subtlety
restriction. Each piece also gets a no-sound redesign with the same photo,
prompt template, seed and generation settings. Only the operation text differs.
The default gallery shows this series when present; earlier experiments remain
available through `art gallery --include-baseline`. CLAP selects text instructions;
the CLAP vector is not directly passed to the image model.

`art long-forms` explores direct geometry as another approach to the weak influence of a three-way prompt palette.
It selects two longer actual OpenWhistle pretraining sequences from the first
100 review rows (observed durations 30.8 and 36 seconds, both 96 kHz). It reads
the entire waveform and generates 5-second, 15-second and full-length prefix
studies. Duration controls rib count (one per 0.75 seconds); the 2–20 kHz
power-weighted spectral centroid controls each rib's mid-height radius
(12–20 mm); local RMS controls rib diameter (0.55–2.20 mm). Shared reference
ranges stay fixed across prefixes. These controls create the silver geometry
directly; no diffusion model interprets them. A fixed amber core and open silver
cocoon connect the study to Livia's settings and Livistone's shells.

`data/output/long-forms/` contains measured feature plots, six PNG views,
matching prefix audio, silver OBJ concept meshes in millimeters, an explanatory
`controls.png`/`controls.svg`, and `studies.json` with complete time series and
per-rib dimensions. Features summarize all recorded acoustic energy, including
noise; centroid is not whistle pitch. Meshes have intersections and open tube
ends and need further geometric work before fabrication. Without a jewelry
redesign series, the gallery shows the geometry study; `art gallery --include-baseline` restores
the earlier CLAP/FLUX series for comparison. WhAM is an available separate
route for synthetic sperm-whale codas; no synthetic whale audio was generated
in this run.
`art brush` is a human-operated, CHAT-style sound brush:

- **Keys:** white keys synthesize explicit whistle contours (rise, dip, hump, wave, clicks, plus a falling sweep and a steady tone that are not commands). Black keys play the local OpenWhistle and DSWP recordings.
- **Analysis:** the brush reads only the emitted WAV. It measures the ridge contour and click onsets and recognizes four designed contours by DTW with rejection. The recognized contour selects grow, branch, fold or open around one of Livia's stones; clicks lay beads.
- **Continuous controls:** pitch change turns the stroke (90° per octave), duration sets length, level sets width, and silence lifts the brush.
- **Replay:** identical audio reproduces the identical stroke hash.
- **Study:** `art brush study` writes keys, performances, one-feature comparisons, replay checks and an OpenWhistle-versus-contour comparison to `data/output/brush/index.html`. It needs `art fetch` and `art long-forms` inputs.

Listen controls sit beside the input audio and use louder playback copies. Half
speed lowers pitch to make high frequencies easier to hear; original speed and
pitch remain selectable. A common gain is used for all prefixes of one long
recording. The raw audio, raw RMS and geometry controls are retained unchanged;
playback gains and hashes are recorded.

1. **Whistle portraits:** compare frequency contours with a frozen
   OpenWhistle encoder; investigate signature types without assuming caller ID.
2. **Sound in context:** align recordings with observed behavior in DOLPHINFREE;
   treat group-minute activity labels separately from individual call meaning.
3. **Whale rhythms:** inspect the sperm-whale timing/dialogue tables; keep their
   provenance separate from the audio-only DSWP Hugging Face release.
4. **Visual controls:** compare direct acoustic features, CLAP/BioLingual text
   alignment, and a learned mapping to Livia's chosen visual parameters.
5. **Orca populations and spatial sound:** follow the [DCLDE starting sequence](docs/dclde-2027.md#recommended-starting-sequence-for-this-repository),
   beginning with annotation metadata and the public orca cascade; compare
   population patterns across held-out recording deployments.

No audio model has been trained or benchmarked here yet. The downloaded DCLDE
ONNX models passed synthetic CPU graph checks; this does not evaluate audio
preprocessing or biological accuracy. Raw data, checkpoints,
and generated experiments are ignored by Git; the uv lockfile and schema audits
are retained.

Use `data/input/` for recordings and artwork, `data/interim/` for analysis and
checkpoint caches, and `data/output/` for generated experiments. Legacy
`outputs/`, `models/` and alternate data locations remain ignored. The ignore
rules also cover alternate `.venv*`
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
