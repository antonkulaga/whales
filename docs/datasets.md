# Cetacean datasets

**Recordings, labels, context, and access for Livia's sound-to-form project.**

Checked **4 October 2026** · [Model guide](models.md) · [Research plan](research.md)

Datasets supply examples and annotations. The [model guide](models.md) describes
the trained systems that consume those examples. This guide covers the 16
resources in the [machine-readable inventory](../resources/datasets.json).
The [DCLDE 2027 guide](dclde-2027.md) details the workshop tracks, current
download contents, actual inspected schemas, and challenge-specific models.

## Choose by artistic question

| Question | Dataset to inspect first | Why | Smallest useful starting point |
|---|---|---|---|
| What does an individual's recurring whistle look like? | OpenWhistle classification | Named signature types and frequency tracks | Six tracks with the repo's `contours` command |
| How does sound relate to observed activity? | Madeira, then DOLPHINFREE | Group behavior is observed and recorded | Madeira's 36 KB metadata workbook |
| How do whales organize rhythm and exchanges? | Sperm-whale timing/dialogue tables | Click intervals, group codes, and ordered timing | Two CSVs, about 1.25 MB together |
| How do sounds vary across populations? | DCLDE orca annotations | Population/ecotype labels and acoustic bounds | Authors' 4.9 MB annotation/code archive |
| Can sound organize a spatial artwork? | Fin-whale DAS localization | Arrival picks and cable geometry support localization | One 23.55 KB annotation CSV; source-coordinate reference needs alignment |
| How does acoustic activity relate to abundance? | Cape Cod Bay detections and aerial surveys | Candidate calls plus survey effort and aggregate whale counts | Aerial CSV, 1.335 KB / 21 rows |
| Can a model learn to generate whale sound? | DSWP or SanctSound DAC9 | Coda waveforms or humpback codec tokens | One DSWP WAV; one compatible DoLittle token prompt |

These are project choices, rather than biological claims. The tables below
describe what each resource actually records.

## 1. Recordings and representations

Sizes are approximate unless an exact row count is stated. Different subsets
of the same release overlap; their counts should not be added together.

| Dataset / release | Animals | Data supplied | Scale | Format / sample rate | Main use |
|---|---|---|---|---|---|
| [DSWP](https://huggingface.co/datasets/orrp/DSWP) | Sperm whales | Isolated coda audio | 1,501 clips; about 45 min | WAV; recording systems vary | Coda structure and WhAM experiments |
| [OpenWhistle Pretraining](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Pretraining) | Dolphin Reef dolphin recordings | Unlabeled audio sequences and timing | 31,780 sequences; 114.284 h | HF Parquet with audio; 96 kHz mono | Self-supervised representation learning |
| [OpenWhistle CNN](https://huggingface.co/datasets/dolphinteam/OpenWhistle-CNN) | Dolphins | Short audio windows and spectrogram images | 76,516 windows; 0.4 s each | HF Parquet; audio + images | Binary whistle detection |
| [OpenWhistle Classification](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Classification-Finetuning) | Dolphins | Whistle clips, categories, F0 tracks and quality fields | `balanced` 3,000; `unbalanced` 3,488; `all` 8,354 | HF Parquet; audio + arrays + images | Whistle-type comparison and visual contours |
| [OpenWhistle Detection](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Detection-Finetuning) | Dolphins | Audio windows and multi-label targets | 5,600 windows; 0.5 s each | HF Parquet; audio + target vectors | Detecting types within a window |
| [DOLPHINFREE](https://zenodo.org/records/14637675) | Short-beaked common dolphins | Audio, observation tables, traced whistles, array geometry | 4,637 contours; 275 single-channel minute files; 117 array files | WAV, XLSX, JSON, CSV; icListen 512 kHz, four-channel TETRA also supplied | Wild group behavior and acoustic direction |
| [Madeira odontocetes](https://zenodo.org/records/17952229) | Seven species, including dolphins and sperm whales | Recordings and group/sighting metadata | 35 recordings; 2022–2025 | WAV + `Metadata.xlsx`; 288 kHz reported | Contextual comparison across species |
| [Sarasota whistle database](https://doi.org/10.3389/fmars.2022.923046) | Bottlenose dolphins | Known-individual whistles and longitudinal records | 2022 description: 926 sessions, 293 dolphins | Research database; raw access by request | Caller identity and familial/social context |
| [Watkins archive](https://www.whalingmuseum.org/research/digital/watkins-marine-mammal-sound-recording/) | Many marine-mammal species | Historical recordings, cuts, observation metadata | Large archive; counts depend on the selected collection | Audio + archive metadata; sample rates vary | Cross-species acoustic comparison |
| [Sperm-whale timing/dialogue tables](https://github.com/pratyushasharma/sw-combinatoriality) | Sperm whales | Click intervals, grouping and exchange timing | Actual CSVs: 8,719 coda rows; 3,840 dialogue rows | Two CSVs; about 1.25 MB combined | Rhythm, grouping, and dialogue geometry |
| [DCLDE orca annotations](https://doi.org/10.25921/15ey-mh50) | Orcas, humpbacks, and other sound classes | Audio-linked species/ecotype annotations | Current NOAA CSV re-counted: 207,574 rows / 50.48 MB; paper audio estimate about 1.6 TB | CSV + provider audio; rates vary | Detection and ecotype classification |
| [Killer-whale HFM](https://datadryad.org/dataset/doi:10.5061/dryad.8cz8w9h7f) | Killer whales | Audio and traced time/frequency/amplitude contours | 5.99 GB archive | Audio, CSV, location/specification workbook | Direct high-frequency sound-to-curve mapping |
| [SanctSound humpback DAC9](https://huggingface.co/datasets/cairninstitute/mmc-sanctsound-humpback-dac9) | Humpbacks | Audio-codec token arrays and quality scores | 488,320 arrays; 29 TAR shards | NPY in WebDataset; DAC 44.1 kHz, nine codebooks | DoLittle training and audio continuation |
| [Fin-whale DAS localization](https://doi.org/10.25921/v2vh-8w16) | Fin whales | Arrival picks, cable geometry, denoised/SNR detection products | 120 annotation CSVs / 1.45 MB; 120 NetCDFs / 103.10 GB; geometry / 10.20 MB | CSV headers inspected; NetCDF variables unverified | Association and localization |
| [Cape Cod Bay array audio](https://doi.org/10.25921/ab3a-c842) | North Atlantic right whales | Synchronized hydrophone recordings | Complete listing: 11,249 FLACs / 57.44 GB | Five channels; NOAA describes 2 kHz, 16 bit, normally 15-minute files | Cross-sensor call matching and abundance analysis |
| [Cape Cod Bay detections/aerial surveys](https://doi.org/10.25921/x68p-cj94) | North Atlantic right whales | Candidate detection tables, survey effort and aggregate sightings | 118 selection tables / 336.30 MB; aerial CSV / 21 rows | TSV + CSV; selected actual schemas inspected | Density/abundance modeling |

The first five schemas were inspected directly and saved in
[resources/audits](../resources/audits/). Actual-file inspections and primary
sources for the other releases are recorded in the
[dolphin report](dolphin-datasets.md) and [whale report](whale-datasets.md).

## 2. Labels, meaning, and position

**Annotation level matters:** a label may describe a whistle, a short window,
an entire recording, a group observation, or a whole corpus.

| Dataset | Explicit labels | Annotation level | Social / biological information | Position information |
|---|---|---|---|---|
| DSWP | No public per-clip labels | Species/region describe corpus | One clan/region; no exported behavior or caller | No per-clip positions |
| OpenWhistle Pretraining | None; year, duration, hydrophone, timing | Sequence | Longitudinal recording context | Channel ID; no animal coordinates |
| OpenWhistle CNN | `noise`, `whistle` | 0.4 s window | Whistle presence | Recording-relative onset/offset |
| OpenWhistle Classification | Named signature types and numbered non-signature types | Whistle clip | Associated whistle owner; actual caller not guaranteed | Session and clip timing |
| OpenWhistle Detection | Seven whistle-type decisions; binary presence | 0.5 s window | Which acoustic types are present | No exported source position |
| DOLPHINFREE | Foraging, travelling, socializing, milling, boat attraction | Visual group-minute percentages; separate whistle contours | Independently observed group activity | Array geometry supports estimating direction; no supplied individual trajectories |
| Madeira | Species, group behavior, group size, calves, call categories, vessels | Recording / sighting | Observed group composition and activity | Initial sighting GPS, not localized caller |
| Sarasota | Known caller records, signature types, age, sex, matrilineage, associations | Individual / session / longitudinal | Richest known-individual context in this shortlist | Separate site/observation context; access-dependent |
| Watkins | Species and variable observation fields | Recording or archive cut | Behavior/identity details vary by record | Recording location, not necessarily source localization |
| Sperm-whale tables | Coda type, clan, unit, identity codes, timing | Coda / exchange table | Social grouping and timing; some identity codes are unresolved | Date/recording information; no verified source tracks |
| DCLDE orcas | Broad sound class, ecotype, uncertainty | `Detection`, `Call`, or `File` | Population/ecotype; provider originals may contain finer labels | UTC and deployment context; spectral boxes are not spatial positions |
| Killer-whale HFM | Traced time, frequency, amplitude | Signal contour | Proposed function remains a hypothesis | Regional folders and recording locations |
| SanctSound DAC9 | Machine-derived detector and quality scores | Tokenized chunk | No human song-meaning labels | Source file and chunk provenance |
| Fin-whale DAS | Call/segment IDs, UTC, pick time/distance, call type, cable, SNR | Multiple arrival picks per call | Acoustic events rather than semantic labels | Inspected geometry locates sensors; source-coordinate reference not found in bucket |
| Cape Cod Bay audio | Synchronized recording channels | Multichannel recording | No individual identity or behavior labels verified | Sensor array; localization requires processing |
| Cape Cod Bay detections/aerial | Candidate call scores/timing and daily flight effort/counts | Detection candidate / survey flight | Calling rate not supplied; detections are not animal counts | No individual whale positions in inspected aerial CSV |

A signature whistle has experimentally supported identity-related function.
That does not make every named whistle a confirmed recording of its owner:
dolphins copy each other's signature whistles. Observed activity and signal
function also do not establish a particular call's intended message.
[Signature-whistle playback study](https://doi.org/10.1073/pnas.1304459110)

### Exact OpenWhistle class maps

Read labels through the selected config's schema: integer IDs are **local to
that config**. `SW` means signature whistle; `NSW` means non-signature whistle.

| ID | `balanced` / `balanced-review-sample` | `all`, `unbalanced`, and their review configs |
|---:|---|---|
| 0 | `NSW_1` | `NSW_3` |
| 1 | `SW_Luna` | `NSW_2` |
| 2 | `SW_Nana` | `NSW_1` |
| 3 | `SW_Neo` | `SW_Dana` |
| 4 | `SW_Nikita` | `SW_Luna` |
| 5 | `SW_Yosefa` | `SW_Nana` |
| 6 | — | `SW_Neo` |
| 7 | — | `SW_Nikita` |
| 8 | — | `SW_Shy` |
| 9 | — | `SW_Yosefa` |

CNN mapping: `0=noise`, `1=whistle`.

Detection-vector order: `SW_Neo`, `SW_Luna`, `SW_Nikita`, `SW_Nana`,
`SW_Yosefa`, `SW_Dana`, `NSW_1`. An all-zero vector means background.
[Saved classification schema](../resources/audits/OpenWhistle-Classification-Finetuning.json),
[saved detection schema](../resources/audits/OpenWhistle-Detection-Finetuning.json)

### Other useful label vocabularies

| Resource | Values / fields worth retaining |
|---|---|
| Madeira group behavior | `Erratic`, `Feeding`, `Feeding/Socialising`, `Resting`, `Resting/Travelling`, `Socialising`, `Socialising/Resting`, `Travelling`, `Travelling/Socialising` |
| DCLDE sound class | `HW`, `KW`, `UndBio`, `AB` |
| DCLDE ecotype | `SRKW`, `TKW`, `NRKW`, `SAR`, `OKW`, `NA`; Southern Resident, Transient/Bigg's, Northern Resident, Southern Alaskan Resident, Offshore, unknown |
| Coda table | `CodaType`, `Clan`, `Unit`, `UnitNum`, `IDN`, `nClicks`, `Duration`, `ICI1`–`ICI9`; preserve unresolved `IDN=0` |
| Dialogue table | `REC`, `Whale`, `TsTo`, `nClicks`, `Duration`, `ICI1`–`ICI28` |

## 3. Access, license, and first download

Dataset licenses are distinct from paper, software, and model-weight licenses.
“Unspecified” records an actual gap in the inspected release.

| Dataset | Access / packaging | Small first inspection | Data terms observed | Remaining check |
|---|---|---|---|---|
| DSWP | Public HF WAV files | One WAV, about 193 KB | CC BY 4.0 | Build a manifest; per-file annotations are absent |
| OpenWhistle Pretraining | Public HF configs | Schema; review sample is still about 793 MB | HF data license unspecified | Establish dataset terms for intended reuse |
| OpenWhistle CNN | Public HF configs | `review-sample`, 480 windows | HF data license unspecified | Dataset terms and exact spectrogram preprocessing |
| OpenWhistle Classification | Public HF configs | F0 rows; 480-row review config | HF data license unspecified | Dataset terms; compare tracks with spectrogram QC |
| OpenWhistle Detection | Public HF default config | Schema, then selected rows | HF data license unspecified | Dataset terms; preserve multi-label structure |
| DOLPHINFREE | One 39.9 GB ZIP | Descriptor and archive layout | CC BY 4.0 | Internal schemas not locally inspected |
| Madeira | Small metadata plus 2.3 GB audio ZIP | `Metadata.xlsx`, 36,345 bytes | CC BY 4.0 | Normalize taxonomy while preserving original values |
| Sarasota | Raw database by research request | Resource paper and access statement | Access/use terms need agreement | Request linked records needed for the chosen question |
| Watkins | Original archive and mirrors | One best-of cut with metadata | WHOI permits personal/academic use; commercial use prohibited | Check original and selected mirror terms |
| Sperm-whale tables | Public GitHub CSVs | Both tables, about 1.25 MB | No repository data license verified | Resolve reuse terms, filtering, and audio linkage |
| DCLDE orcas | Small author archive; NOAA combined CSV and provider audio | Annotation/code ZIP, about 4.9 MB | Author software MIT; NOAA license filename says CC BY but body is CC BY-SA 4.0 | Resolve license discrepancy; preserve provider provenance |
| Killer-whale HFM | One 5.99 GB ZIP | README, about 1.78 KB | CC0 1.0, per Dryad API | Inspect actual CSV headers and selected matched audio |
| SanctSound DAC9 | 29 token TAR shards | `chunk_scores.csv` and terms | Custom Project DoLittle Dataset Terms | Retain source attribution and token/audio provenance |
| Fin-whale DAS | CSV annotations/geometry + large detection NetCDFs | One annotation CSV, 23,550 bytes | Uniform data license not established | NetCDF schema, reference positions, coordinate system |
| Cape Cod Bay audio | Public multichannel FLACs | Metadata and one selected file | Uniform data license not established | Setup dates and channel/time alignment |
| Cape Cod Bay detections/aerial | Daily selection tables and aerial CSV | Aerial CSV, 1,335 bytes | Uniform data license not established; detailed sightings require agreement | False positives, call rate and visual detectability |

Source details: [Dolphin access audit](dolphin-datasets.md),
[whale access audit](whale-datasets.md),
[DoLittle data terms](https://huggingface.co/datasets/cairninstitute/mmc-sanctsound-humpback-dac9/blob/main/DATASET_TERMS.md).

## Connect datasets to models

| Dataset | Related model | Relationship |
|---|---|---|
| DSWP | WhAM | Public species-specific fine-tuning audio; additional evaluation annotations are separate |
| SanctSound DAC9 | DoLittle MMC | Tokenized humpback corpus for training and prompts |
| OpenWhistle Pretraining | OpenWhistle Wav2Vec2.0 | Self-supervised pretraining corpus |
| OpenWhistle CNN | OpenWhistle CNN-VGG16 | Supervised binary detector dataset |
| OpenWhistle Classification / Detection | OpenWhistle Wav2Vec2.0 + task head | Downstream fine-tuning/evaluation datasets |
| DOLPHINFREE / Madeira / Watkins / DCLDE | Candidate encoders in the model guide | New experiments; no automatic guarantee of transfer |
| DCLDE orcas | SPARROW orca detector + ecotype classifier; Perch + probe | Public trained task packages or a transfer-learning comparison; assess held-out providers |
| Fin-whale DAS | DAS4Whales + association/localization code | Physical spatial inference from arrival times and geometry |
| Cape Cod Bay | Candidate detection correction + abundance model | Requires cross-channel matching, detectability and calling-rate assumptions |

## Explore in this repository

The [metadata-only world map](world-map.md) covers **44 mapped species** and
**172 coordinate/region entries** across this catalogue. It combines published
deployment and sighting positions with clearly marked archive approximations
and regional anchors. The complete Watkins metadata mirror, Madeira spreadsheet,
SanctSound chunk-scores CSV, and NOAA deployment/cable geometry were inspected
without downloading audio. Eleven additional species have no coordinate join;
missing/withheld coordinates and overlapping dataset configurations remain explicit.

```bash
uv run main.py catalog
uv run main.py inspect dolphinteam/OpenWhistle-Classification-Finetuning
uv run --group viz main.py contours --limit 6
```

Further leads, with more limited access verification, are documented in the
focused reports: Oltremare activity labels, the HydroMoth metadata example, and
MBARI humpback song-unit categories. They are not counted in this guide's
16-resource inventory. DORI is an additional prerelease domain-adaptation lead
in the [DCLDE guide](dclde-2027.md#additional-data-that-may-help); it is not counted
as another fully audited corpus here.

## Possible extension: seals

The orchestra stays with whales and dolphins for now. Seals, sea lions and walruses could join
later. None of the DCLDE releases label pinnipeds. The Watkins metadata in the
[world map](world-map.md) covers 10 seal, sea-lion and walrus species with recording locations.
AWI's polar recordings on PANGAEA, the source of the orchestra's Antarctic blue whales and
bowheads, were also used to study Antarctic seals ([Van Opzeeland 2010, *Acoustic ecology of
marine mammals in polar oceans*](https://doi.org/10.2312/bzpm_0619_2010)), so the same archive
and loader would be the first place to look.
