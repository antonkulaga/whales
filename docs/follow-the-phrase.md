# Follow the phrase: does generated music follow a particular animal phrase?

Implemented and measured **7 October 2026**. This is the experiment proposed in
[idea 1](2026-art-ideas.md#1-music-that-follows-whale-or-dolphin-sound): measure a
real phrase, give the music model a guide, and check whether the music follows that
phrase rather than music in general. Each species is tested separately.

Run it with `uv run --group art --group viz main.py follow run`, then open
`data/output/follow/index.html`. The page plays every stem on its own or over the
recording, draws the guide's onsets and contours on each spectrogram, and shows the
swap matrix. It is generated locally and Git-ignored.

## Inputs

| Source | Recording | Events | Guide |
|---|---|---|---|
| humpback-a | Orcasound Lab, 28 Oct 2021, 142–172 s: ascending moan → growl → whup ×3 | 10 units from Emily Vierling's Raven selection table | Subharmonic-summation F0 inside each unit, bowed tone, 0 octaves |
| humpback-b | Same recording, 56–86 s: moans, upsweep, cries | 8 annotated units | Same, −1 octave |
| dolphin-a/b | OpenWhistle pretraining sequences 94 and 37, first 30 s at 96 kHz | 105 and 110 whistle segments **detected** from the waveform | Measured ridge, flute-like tone, −3 and −4 octaves |
| sperm-a/b | DSWP coda clips, rows 0–7 and 8–15, joined with **0.8 s gaps we inserted** | 16 and 7 click groups, detected | One mallet strike per click, first click accented |

The humpback recording and selection table come from the public Orcasound
`acoustic-sandbox` bucket. Check Orcasound's non-commercial terms before an
installation release. DSWP is CC BY 4.0. The OpenWhistle card declares no license.

## Conditions

Every source gets the same caption, seed (20261007), 50 steps and guidance 7 for its
species. Only the source audio changes.

| Output | What the model receives |
|---|---|
| Deterministic response | No model. An open-fifth pad and bass at each tonal onset, or a drum and ticks on each coda. It follows by construction, so it shows what following looks like in the scores. |
| `ace-prompt` | ACE-Step 1.5 base `text2music`, caption only |
| `ace-raw`, `ace-guide`, `ace-perturbed` | `lego`: a keyboard (or percussion) track generated in the context of the recording, guide or perturbed guide |
| `ace-cover-raw`, `ace-cover-guide`, `ace-cover-perturbed` | `cover` at strength 0.6: the source transformed toward the caption |

The perturbed guide mirrors event order in time (an event ending at *t* starts at
*T − t*) and inverts each contour around its median. Instrument, register, loudness,
duration, caption and seed stay fixed.

ACE-Step runs in its own uv environment under `data/interim/tools/ACE-Step-1.5`
(commit `ca1e85f`, `acestep-v15-base@e432212`, INT8 weights, no LM). The whole grid of
42 generations took 295 s on an RTX 4090 laptop GPU.

## Scores

- **Timing z.** Correlation between the output's spectral-flux onset envelope and
  40 ms Gaussian bumps at the guide's onsets, against the same output circularly
  shifted by at least 1 s. Around 0 means the music is no more aligned than at a
  wrong time.
- **Pitch z.** Pitch-class agreement inside tonal events at one best transposition,
  against shifted outputs.
- **Swap rank.** Where the output's own guide ranks among both same-species guides
  and their perturbed twins.
- **Source leak.** Peak waveform correlation with the conditioning audio within
  ±100 ms. From 0.15 up, the output partly copies its source instead of answering it.

## Results

Timing z against each output's own guide (perturbed outputs against the perturbed
guide). † marks a source leak ≥ 0.15.

| Output | humpback-a | humpback-b | dolphin-a | dolphin-b | sperm-a | sperm-b |
|---|---:|---:|---:|---:|---:|---:|
| response | +16.2 | +16.3 | +15.5 | +11.8 | +6.7 | +11.2 |
| ace-prompt | +1.1 | −0.2 | −0.7 | −0.5 | +1.1 | +0.5 |
| ace-raw | −1.3 | +1.5 | −2.3 | +1.3 | +0.7 | +2.6 |
| ace-guide | +1.6 | +0.0 | −1.6 | +0.8 | +2.2 | +7.4† |
| ace-perturbed | +1.5 | +0.9 | −0.2 | +1.9 | +0.0 | +2.1 |
| ace-cover-raw | +0.2 | −0.9 | −0.1 | −0.9 | +1.7 | +1.1 |
| ace-cover-guide | +4.1 | +3.4 | +0.8 | +3.9 | +2.9† | +6.0† |
| ace-cover-perturbed | +2.1 | +2.3 | +1.2 | +2.0 | +1.8† | +3.7† |

Pitch z for the tonal sources:

| Output | humpback-a | humpback-b | dolphin-a | dolphin-b |
|---|---:|---:|---:|---:|
| response | +0.6 | +0.5 | +5.5 | +2.0 |
| ace-guide | +0.3 | −1.1 | +0.2 | −0.2 |
| ace-cover-guide | +3.3 | +2.1 | +3.9 | −0.1 |
| ace-cover-perturbed | +0.5 | +1.8 | +2.6 | +2.6 |

The deterministic response follows timing strongly but pitch only weakly for
humpbacks. It holds one chord per unit, while the units glide.

## Registered predictions

P1–P5 were written into `experiments/follow.py` at 16:19 UTC, before the first
evaluation. P6–P7 were added at 16:32 UTC, after one lego trial on humpback-a and
before any cover output existed. The page shows each verdict with its numbers.

| | Prediction | Verdict | Reading |
|---|---|---|---|
| P1 | Deterministic response follows (z ≥ 3) and prefers the perturbed guide when rendered from it | Supported | The positive control works for all six sources. |
| P2 | Prompt-only output follows no guide (\|z\| < 2) | Supported | z from −0.7 to +1.1. |
| P3 | Lego on the guide beats lego on the recording for ≥ 2 of 3 species | Supported on its wording | Dolphin and humpback differences are below z = 2 on both sides. The sperm-whale win comes from sperm-b, whose lego track partly copies the guide's mallet strikes (leak 0.44). |
| P4 | Lego on the guide ranks its own guide first for ≥ half of sources | Not supported | 2 of 6. |
| P5 | Lego on the perturbed guide prefers the perturbed guide for ≥ half of sources | Supported on its wording | Every comparison except sperm-b stays below z = 2, so the ordering is noise. |
| P6 | Cover of the guide follows timing (z ≥ 3) for ≥ 4 of 6 sources | Supported, narrowly | humpback-a, humpback-b and dolphin-b pass cleanly. The fourth pass, sperm-b, partly copies the guide (leak 0.19). |
| P7 | Cover of the perturbed guide prefers the perturbed guide for ≥ 4 of 6 | Supported | 6 of 6 move toward the perturbed guide; dolphin-a and sperm-a stay below z = 2. |

## What this means for the artwork

- **Lego accompaniment does not follow these phrases.** It writes on its own grid.
  This matches the [stop condition](2026-art-ideas.md#first-comparison-and-deliverable):
  in this setting, describe lego output as atmosphere inspired by the sound. When
  the requested track matches the guide's own sound (percussion over mallet strikes),
  it starts to copy the guide.
- **The raw recording never steers the music.** Neither lego nor cover follows it.
  Measuring the phrase and rendering a guide is necessary.
- **Cover of a measured guide follows modestly, and it follows a change.** Timing z
  of 3–4 for humpbacks and one dolphin sequence, with pitch-class agreement for
  three of four tonal sources. All six perturbed covers move toward their perturbed
  guide. This is the route to develop, with the deterministic response as the
  reliable fallback.
- Dense dolphin whistle sequences (3–4 events per second) are hard to follow in
  timing for every model condition. Sparser selections or slower declared time
  stretching are the next test.

## Limits

One seed, one caption per species and one cover strength were tested, so the
numbers will move with those choices. A rerun with the same seed is not
bit-identical on this GPU with INT8 weights: spectrogram correlation was 0.96 and 0.89
for two cover reruns. Cover passes the source to the model only as 5 Hz codes (200 ms
each) during the first `int(50 × 0.6) = 30` of 50 steps, which limits timing precision.
Replacing the perturbed guide with silence dropped the output's spectrogram
correlation to 0.06 and 0.03, so the cover does use its source. The F1 event scores are modest everywhere,
even where timing z is high. Whistle and click events are detections, not
annotations. Pleasing music says nothing about animal preference or meaning.

## Combining sources on the map

[Phrase Atlas](../apps/sound-map/README.md) is a Bun + TypeScript app over the same engine.
Pick recordings at their sites, layer or sequence them with trims, offsets, gains and
registers, and optionally ask ACE-Step for a cover or lego track of the combined guide.
While the piece plays, each site pulses on its own onsets. Each part is scored only
while it plays, so a layered piece shows which phrase the music follows.

The first combinations repeat the single-source pattern. In "Haro Strait answers
Dominica" (humpback-a layered with sperm-b), the ACE-Step cover follows the humpback
(z +3.3) and ignores the codas (z +0.3). In a humpback → dolphin → sperm-whale sequence
it follows the humpback part (z +3.4) more than the dolphin and coda parts (+1.9, +2.3).
The deterministic response follows every part (z 5–14).

For the map, eight more recordings come from the DCLDE 2027 killer-whale dataset, using
30 s windows with the densest annotated calls. Seven are killer whales: Southern Residents
at Orcasound Lab, Bush Point, Port Townsend and Tekteksen; Bigg's transients at Cape
Elizabeth; offshore killer whales at Kachemak Bay and Montague Strait. The eighth is a
humpback at Cape Elizabeth. The two Cape Elizabeth windows (from 710 MB and 3.4 GB files)
were read with HTTP byte ranges. These sources are marked `"study": false`, so the
registered six-source study, its ACE-Step grid and its verdicts are unchanged. Their
guides track F0 on whitened spectra inside each annotated call's frequency box, because
hydrophone noise otherwise pulled the tracker to the bottom of its range.

Across ten combined pieces, the cover follows parts in sequences better than in dense
layers:

- **Sequence:** "Southern Residents down the Salish Sea" follows its Port Townsend part
  at z +5.4 and its other parts at +1.6 to +2.3.
- **Dense layers:** with three or four overlapping parts, no part reaches z 2.2.
- **Duet:** "Dominica answers Kachemak" follows the offshore orcas (+2.9) and ignores the codas.

`bun run export` in `apps/sound-map` writes a read-only copy (`atlas.html` and the files
it lists in `atlas-files.json`), which was published as a private listening page.

## Files

- `experiments/follow.py`: sources, measurement, guides, perturbation, response, ACE-Step jobs, CLI
- `experiments/follow_ace.py`: runner executed by ACE-Step's own interpreter
- `experiments/follow_metrics.py`: timing, events, pitch, leakage, swap ranks and verdicts
- `experiments/follow_gallery.py`, `experiments/follow_page.html`: listening page
- `resources/follow-music.json`: sources, registers, instruments, captions and model settings
- `tests/test_follow.py`: synthetic-signal tests for every stage
- `experiments/follow_combine.py`, `tests/test_follow_combine.py`: combinations, catalog and their tests
- `apps/sound-map/`: the Phrase Atlas app

```bash
uv run --group art --group viz main.py follow fetch      # humpback FLAC + table, DSWP rows
uv run --group art --group viz main.py follow prepare    # measure; animal, guide, perturbed, response stems
git clone https://github.com/ace-step/ACE-Step-1.5 data/interim/tools/ACE-Step-1.5
(cd data/interim/tools/ACE-Step-1.5 && uv sync)
uv run --group art --group viz main.py follow generate --no-offload
uv run --group art --group viz main.py follow evaluate
uv run --group art --group viz main.py follow page
uv run --group art --group viz python -m unittest tests.test_follow
```
