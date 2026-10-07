# DCLDE 2027: challenges, data, and useful baselines

Checked **4 October 2026**. DCLDE means Detection, Classification, Localization,
and Density Estimation of marine mammals using passive acoustics. This guide
connects the workshop to this repository's [datasets](datasets.md),
[models](models.md), and sound-to-form experiments. Recommendations below are
project choices. The local metadata/model follow-up below was completed on
**7 October 2026**; no biological model performance was evaluated. A separate
[label audit](dclde-opportunities.md) checks what each track's labels support
for the [new proposals](novel-projects.md), including a provider annotation
convention that is confounded with orca population.

## Download metadata and the public models locally

The **entire 50,484,452-byte annotation CSV** is now available at
`data/input/dclde/Annotations.csv`, with a generation-pinned source manifest
and verified NOAA MD5/SHA-256. No DCLDE audio was downloaded.

```bash
uv run main.py dclde metadata
uv run main.py dclde summary
uv run --group viz main.py dclde charts
uv run --group viz main.py dclde visualize
uv run main.py dclde models

# Isolated CPU runtime; no changes to the project's ML environment required
uv run --no-project --python 3.12 --with onnxruntime --with numpy \
  --with polars --with typer dclde.py check-models
```

The summary writes `summary.md`, `summary.json`, categorical CSV tables,
provider/species/population cross-tabs, daily counts, and PNG/SVG distributions
under `data/output/dclde/`. A versioned
[statistics snapshot](../resources/audits/dclde-orca-summary.json) records the
full input hash and counting method.

| Statistic from the complete CSV | Result |
|---|---:|
| Annotation rows | 207,574 |
| Unique recording keys (`Provider`, `Dataset`, `Soundfile`) | 13,084 |
| Orca annotations | 59,107 |
| Orca annotations with / without known population | 52,657 / 6,450 |
| Humpback annotations | 124,977 |
| Largest provider, DFO_CRP | 76.54% of rows |
| Annotation dates | 2011-02-10 to 2023-04-28 |
| Median / 95th-percentile call-or-detection duration | 0.554 / 1.694 seconds |
| Invalid or missing time / frequency bounds | 650 / 2,398 |
| Exact duplicate rows excluding export index | 65 |
| Summed / union call-or-detection annotation time | 42.49 / 40.95 hours |

The union merges overlapping valid intervals within each recording, across
sound classes, and excludes `File` labels. **Neither duration is the total audio
coverage.** Provider and class imbalance describe this annotation release,
rather than whale abundance.

### Summary dashboard and deployment maps

`dclde visualize` writes six summary plots as `summary-statistics.png` and
`summary-statistics.svg`, plus `visual-data.json`, `deployment-map.csv`, and
`deployment-map.geojson` under `data/output/dclde/`. The plots show sound classes,
orca populations (including unknown), provider contributions, UTC recording
year, annotation levels, and valid call/detection durations in 30 log-spaced bins.
The input SHA-256 must match the summary before generating plots.

The annotation CSV has no latitude/longitude columns. The map joins its
`Provider` and `Dataset` to published deployment coordinates in the
[dataset descriptor's Table 1](https://www.nature.com/articles/s41597-025-05281-5/tables/1).
The [saved deployment table and basemap provenance](../resources/maps/README.md)
document explicit identifier aliases and source inconsistencies.

| Coordinate status | Annotation rows | Interpretation |
|---|---:|---|
| Fixed instrument, published rounded coordinates | 30,209 | Recording deployment location |
| Approximate field-recording region | 8,078 | Authors' approximate center of focal-follow tracks |
| Withheld by DFO | 169,282 | Retained in counts; omitted from spatial points |
| Inconsistent published longitude sign | 5 | Excluded from map; raw coordinates preserved |

Thus **23 of 32 datasets / 38,287 rows (18.44%)** can be mapped. Identical
published coordinates are aggregated into 17 map symbols; the GeoJSON retains
one feature per mapped dataset. Circle/diamond areas scale with annotation rows
on a shared scale. Pacific Northwest, southern Alaska, and Salish Sea views use
Natural Earth coastlines. Selecting a site shows its counts, recording keys,
and contributing datasets.

These coordinates locate recording instruments or approximate recording
regions. They do not establish whale positions, movement tracks, acoustic
localizations, or spatial density. The unmapped majority prevents interpretation
as a complete geographical distribution of this release. Provider and year
counts are unadjusted for recording effort.

The detector and ecotype classifier are under `models/dclde/`, with their
manifests, labels, licenses, cards, and provenance. Selective ZIP range downloads
transferred **86.77 MB**, yielding **94.42 MB of ONNX weights**; upstream `.ckpt`
files were excluded. Both model SHA-256 hashes matched the manifests. Both
graphs loaded with **ONNX Runtime 1.30.0 on CPU** and returned finite outputs
for synthetic inputs. This checks graph execution, not the detector's external
spectrogram frontend or accuracy on recordings.
[Download and smoke-check evidence](../resources/audits/dclde-orca-local-models.json)

## Challenge status

The [official challenge page](https://www.dclde.org/challenges-and-data-sets)
currently describes **2027**. Older papers, filenames, and checkpoints still
use “2026”; retain those original identifiers when recording provenance.

| Track | Requested task | Evaluation information currently stated |
|---|---|---|
| DC-1 / DC-2 | Detect orca vocalizations; classify populations, especially Southern Resident versus Transient/Bigg's | Test release in 2027; detection, classification, and generalization |
| L-1 / L-2 | Localize fin-whale calls with one fiber in XY, or two fibers in XYZ | Ten minutes of labeled test events in 2027; submit UTC, coordinates, and uncertainty |
| DE-1 | Estimate right-whale density or abundance in Cape Cod Bay from multiple data streams | No scoring formula or submission schema stated |

The workshop is **1–6 August 2027**. The **1 March 2027** workshop/abstract
deadline and **5 April 2027** acceptance notification are tentative. These are
not confirmed prediction-submission deadlines. Exact DC metrics, event-matching
rules, external-data eligibility, and output formats still need confirmation.
The track leads are Kaitlin Palmer (DC), Léa Bouffaut (L), and Danielle Harris
(DE). [Official status and contacts](https://www.dclde.org/challenges-and-data-sets)

## What is actually downloadable

The current public root is
[`gs://noaa-passive-bioacoustic/dclde/2027/`](https://console.cloud.google.com/storage/browser/noaa-passive-bioacoustic/dclde/2027).
Anonymous Google Storage listings and selected metadata files were inspected.
The [saved audit](../resources/audits/dclde-2027.json) records object generations,
sizes, headers, counts, checksums, and inspection limits. GB/MB below are decimal.

| Resource and DOI | Observed contents | Small first inspection |
|---|---|---|
| [Orca detection/classification](https://doi.org/10.25921/15ey-mh50) | Nine provider folders; `Annotations.csv`, 50,484,452 bytes and **207,574 rows**. Associated audio is about 1.6 TB in the descriptor, not a fresh full-bucket size audit | Combined CSV, or the authors' [4.9 MB annotation/code archive](https://zenodo.org/records/15743034) |
| [Fin-whale DAS](https://doi.org/10.25921/v2vh-8w16) | Five batches: **120 annotation CSVs**, 1.45 MB; **120 detection NetCDFs**, 103.10 GB; two cable-geometry CSVs, 10.20 MB | One annotation CSV, 23,550 bytes; geometry header |
| [Cape Cod Bay array audio](https://doi.org/10.25921/ab3a-c842) | **11,249 FLAC files**, 57.44 GB, from a complete paginated listing | Metadata and one selected multichannel recording after checking its date |
| [Cape Cod Bay detections and aerial surveys](https://doi.org/10.25921/x68p-cj94) | **118 selection tables**, 336.30 MB; `AerialSurvey.csv`, **1,335 bytes / 21 rows**; manuscript and supplement PDFs | Aerial CSV and one daily selection table |

The orca paper describes more than 225,000 contributed provider annotations;
that is a different total from the collated CSV. NOAA's present CSV reproduces
the class counts previously observed in the author release.
[Dataset descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC12229703/),
[current CSV](https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/Annotations.csv)

### Orca annotation semantics

The CSV contains `Soundfile`, `Dataset`, `LowFreqHz`, `HighFreqHz`,
`FileBeginSec`, `FileEndSec`, `UTC`, `ClassSpecies`, `KW`, `KW_certain`,
`Ecotype`, `Provider`, `AnnotationLevel`, `FilePath`, `FileOk`, and an unnamed
row index. See the [whale report](whale-datasets.md#killer-whales-dclde-now-the-2027-workshop)
for complete class counts.

Retain three distinctions when building a manifest:

- Sound classes (`KW`, `HW`, `UndBio`, `AB`) differ from population labels
  (`SRKW`, `TKW`, `NRKW`, `SAR`, `OKW`). `NA` is missing information.
- `Detection`, `Call`, and `File` have different annotation scopes; they cannot
  all be treated as precisely segmented calls. Unannotated intervals are not
  automatically verified negatives.
- Author-side Windows paths need rebuilding against provider download paths.
  Spectral boxes and hydrophone sites do not identify a whale's spatial position.

The current folder has a **license inconsistency**: its
[`CC-BY-4.0.txt`](https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/CC-BY-4.0.txt)
starts with **Attribution-ShareAlike 4.0 International**, and contains the
ShareAlike legal text. Record both filename and contents; a uniform CC BY 4.0
audio license cannot be inferred from that filename. The authors' code license
is separately MIT. No blanket license was established for the DAS or DE data.

### DAS: arrival picks are not source coordinates

One complete annotation CSV has **180 rows**, with columns
`call_id`, `segment_id`, `utc_time`, `time`, `dist`, `call_type`, `cable`,
`snr`, `filename`. A repeated `call_id` spans several arrival picks. The geometry
header is `chan_idx`, `lat`, `lon`, `depth`, `chan_m`, `utm_x`, `utm_y`, `x`, `y`:
these coordinates describe the **cable sensors**.
[Annotation sample](https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_das-finwhale-localization/annotations/batch1/annotated_calls_north_2021-11-04_02_00_02.csv),
[north cable geometry](https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_das-finwhale-localization/geometry/north_DAS_multicoord.csv)

NOAA describes synchronized cables off Oregon, recorded in November 2021, and
advertises reference localizations. However, the inspected challenge folder
contains annotations, denoised/SNR `.nc` products, and geometry; **no separate
source-coordinate table or raw DAS recording folder was found there**. The
sample's `filename` uses colons in the time portion, while its bucket object
uses hyphens, so a filename join requires normalization. NetCDF variables,
dimensions, units, and sampling were not inspected.
[NOAA record](https://doi.org/10.25921/v2vh-8w16),
[listed challenge files](https://console.cloud.google.com/storage/browser/noaa-passive-bioacoustic/dclde/2027/dclde_2027_das-finwhale-localization)

The authors' [association/localization repository](https://github.com/Ocean-Data-Lab/Goestchel_JASA_2025b)
offers an additional `batch1_localizations_with_coords.csv`. Its observed header
includes `utc`, `sensor`, `call_type`, local/UTM XYZ, `lat`, `lon`, `wrms`, and
`deltax`. Treat this as a research output, pending coordinate-system and event-ID
alignment, rather than assuming it is the official scoring reference. Raw
recordings from the same experiment have a separate
[OOI access route](https://oceanobservatories.org/pi-instrument/rapid-a-community-test-of-distributed-acoustic-sensing-on-the-ocean-observatories-initiative-regional-cabled-array/).

### Right whales: detections do not directly count animals

NOAA describes five synchronized MARUs recording at **2 kHz / 16 bit**, with
10–800 Hz filtering and aligned five-channel, normally 15-minute recordings.
The stated survey is 17 February–12 June 2019; listed files also include
15–16 February, so exclude setup periods only after checking metadata.
[Audio record](https://doi.org/10.25921/ab3a-c842)

An inspected daily table contains **4,186 candidate detections**, with columns
`Selection`, `Channel`, `Begin Time (s)`, `End Time (s)`, `Begin File`,
`File Offset (s)`, `Score`, `Tags`. Aerial columns include date, flight times,
duration, surveyed track lines, and total individuals. No individual whale
coordinates are in that aerial CSV.
[Selection sample](https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde2027_narw_detections_in_cape_cod_bay/data/20190215.selections.txt),
[aerial table](https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde2027_narw_detections_in_cape_cod_bay/other/AerialSurvey.csv)

The DE challenge notes that false positives remain, and supplies no explicit
call-production-rate data. Detailed sighting locations require an agreement
coordinated by the DE lead. Start from
[Garcia & Tolkova et al., DOI 10.3354/esr01384](https://doi.org/10.3354/esr01384).
A proposed abundance analysis must distinguish detector errors, the same call
received on several sensors, repeated calls by one whale, effective monitored
area, calling rate, and visual survey effort. These are analysis requirements,
not labels supplied by an audio classifier.

## Models and methods worth testing

| Candidate | Best use | Verified availability / practical limit |
|---|---|---|
| **Microsoft/SPARROW orca detector v5 + ecotype v1** | First pretrained DC baseline | Public MIT ONNX weights downloaded and hash-verified; CPU synthetic graph checks passed; audio evaluation untested |
| **Perch 2.0 + fitted probe** | Few-shot population/species comparison | Published experiments include DCLDE; 32 kHz, 5 s, 1,536-dimensional embeddings. Needs a trained task head; released terrestrial species logits are not ecotype predictions |
| **AVES-bio / AVEX** | Alternative frozen representation | Compare with Perch under the same split; 16 kHz discards frequencies above 8 kHz |
| **ORCA-SPOT** | Legacy binary orca detector comparison | Public GPLv3 code and preprocessing; binary orca/noise rather than ecotype classification; older Python/PyTorch environment |
| **DORI Whisper tiny CPU** | Broad marine-mammal candidate screening | Public quantized ONNX release; labels mean marine-mammal absence/presence, not orca identity; BigScience OpenRAIL-M license |
| **DAS4Whales + Goestchel association/localization scripts** | Fin-whale arrival association and physical localization | Public scientific code; paper repository GPLv3, recommends at least 32 GB RAM. Some examples need separately downloaded association products |
| **Detection correction + localization + abundance model** | DE-1 | Method development needed; no ready-to-use challenge abundance checkpoint verified |

Primary evidence:
[SPARROW catalogue](https://github.com/microsoft/SPARROW-Engine/blob/main/docs/model-zoo-catalogue.md),
[inspected weight release](https://zenodo.org/records/22018132),
[Perch underwater-transfer study](https://arxiv.org/abs/2512.03219),
[AVEX](https://github.com/earthspecies/avex),
[ORCA-SPOT](https://github.com/ChristianBergler/ORCA-SPOT),
[DORI detector card](https://huggingface.co/DORI-SRKW/whisper-tiny-mm-cpu),
[DAS4Whales](https://github.com/DAS4Whales/DAS4Whales).

**SPARROW loading details matter.** The inspected August 2026 Zenodo release
has a 145.39 MB detector ZIP and a 169.25 MB classifier ZIP, including upstream
checkpoints; the ONNX files themselves are 44.68 and 49.74 MB. Both use
24 kHz / 3 s windows. Stage 1 accepts `[B,1,256,555]` dB-mel input: reproduce
the manifest's frontend and apply its sigmoid postprocessing. Stage 2 accepts
`audio` float32 `[B,72000]` **and** `orig_sample_rate` int64 `[1]`; its
temperature scaling is already inside the graph, with softmax outside.
The class order is **SRKW, TKW, SAR, NRKW, OKW**. Documented thresholds are
0.7 for detection and 0.9401 for classifier abstention to `Unassigned_KW`.
These are upstream settings to evaluate, not calibrated values for our data.
The tiny `orca-cascade.zip` is a mobile TFLite pipeline descriptor and needs
the two component models. It contains no weights.
[Release with inspectable package manifests](https://zenodo.org/records/22018132)

The associated research direction is a two-stage ResNet detector/classifier.
The [September 2026 preprint](https://arxiv.org/abs/2609.01792) reports 0.933
end-to-end seven-class macro-F1 on its benchmark, but detection F1 of only
0.405 on a new Puget Sound domain before adaptation, rising to 0.755 afterwards.
The package's detector v5 card independently reports recall of 0.333 on a
180-window reference set. Neither result establishes performance here, and
the exported package should not be assumed identical to every paper experiment.

Perch's underwater study uses fitted logistic-regression probes, rather than
zero-shot species outputs, and DCLDE helped with model selection. Its random
few-shot benchmark is useful evidence for a baseline but does not replace
held-out deployment evaluation. [Study protocol](https://arxiv.org/html/2512.03219v1)

The DAS paper is now **published**, rather than merely accepted as the workshop
page says: [Goestchel et al., DOI 10.1121/10.0044257](https://doi.org/10.1121/10.0044257),
July 2026. Its [scripts](https://github.com/Ocean-Data-Lab/Goestchel_JASA_2025b)
are the most directly relevant starting point for L-1/L-2. Audio embeddings
alone do not solve arrival-time association or 3D localization.

## Additional data that may help

| Resource | Potential role | Constraint to retain |
|---|---|---|
| [DORI collection](https://huggingface.co/collections/DORI-SRKW/dori-6989a492e143f25e92916790) | Target-domain candidate mining; Orcasound, ONC, OOI, SanctSound sources; Pacific white-sided dolphin/humpback confusers | Partial expert verification, changing prerelease labels, and possible overlap with DCLDE sources; deduplicate before assigning splits |
| [OOI DAS experiment](https://doi.org/10.58046/5J60-FJ89) | Raw recordings for association/localization experiments | Same experiment as challenge data; not an independent external test |
| [Watkins archive](https://www.whalingmuseum.org/research/digital/watkins-marine-mammal-sound-recording/) | Broad species examples and qualitative comparisons | Different recording domains; WHOI original terms restrict commercial use |
| [OpenWhistle](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Pretraining) | Exploratory whistle representations and artistic controls | Dolphin-domain transfer candidate, not labeled orca ecotypes |

The [DORI paper, v2](https://arxiv.org/abs/2602.09295v2) reports 919 hours of
SRKW examples, but its DCLDE ecotype accuracy is only 33.6%; training/test class
sets differ. This does not support using those labels as expert ground truth.
Its labels have CC BY 4.0 terms while source audio retains owner-specific terms.
The [ONC card](https://huggingface.co/datasets/DORI-SRKW/DORI-ONC) calls the
release provisional and notes limited annotation validation. A byte-range
inspection of its `DORI.csv` found per-row `license` entries of **CC BY-NC-SA
4.0**, alongside species/ecotype labels, provenance, and segment timings.
Preserve per-file terms rather than replacing them with the card's general license.

WhAM and DoLittle remain useful for artistic audio generation, but no evidence
checked here establishes them as challenge detectors, localizers, or abundance
estimators. CLAP/BioLingual are retrieval experiments rather than verified
population classifiers. See the [general model guide](models.md).

## Recommended starting sequence for this repository

1. **Start with DC metadata.** Select providers with usable call bounds, map
   exact labels and uncertainty, and join a small set of audio files. Split by
   source recording/bout and deployment before producing overlapping windows;
   reserve at least one provider/site for transfer evaluation.
2. **Compare the public orca cascade with Perch + a probe.** Report per-class
   precision/recall, macro-F1, rejected/unknown cases, and performance by provider.
   Use the same windows and split; retain original sample rates in the manifest.
   Proposed local metrics do not imply an official challenge scoring rule.
3. **Use DAS annotations for a small spatial prototype.** Inspect cable geometry
   and one batch before downloading NetCDFs. Confirm variable units, time origin,
   coordinate reference system, depth sign, call association, and reference
   outputs before visualizing localized whale trajectories.
4. **Begin DE with the tiny aerial table.** Align survey effort and daily acoustic
   summaries, then assess detector errors and cross-channel duplication. Call
   counts can guide an artwork immediately; animal abundance needs an explicit
   observation model and sensitivity analysis for calling rate/detectability.

The original 4 October survey inspected metadata and model packaging without
weights. The 7 October follow-up downloaded the full combined annotation CSV
and the two selected ONNX models, and ran synthetic CPU checks. Full audio
corpora and NetCDF detection arrays were not downloaded. Training, biological
model evaluation, paper-score reproduction, and external-data challenge
eligibility remain outside this metadata and model-download workflow.
