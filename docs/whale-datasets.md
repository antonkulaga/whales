# Whale datasets: labels, context, and visual mappings

See the [dataset guide](datasets.md) for the combined comparison and access table,
or the [model guide](models.md) for generation and representation models.

Verified 4 October 2026 against primary sources and small public files. An acoustic class, a population identity, an observed behavior, and a translated message are different kinds of evidence. None of these releases supplies a general whale-language dictionary.

## Sperm whales: two different DSWP releases

**WhAM's Hugging Face audio release** contains 1,501 isolated coda recordings, approximately 45 minutes. The dataset card explicitly says there is no behavioral context or per-file metadata; all recordings come from one clan and region. The viewer exposes audio, not caller, coda type, behavior, or position labels. It is CC BY 4.0. A tiny starting sample is [`1.wav`](https://huggingface.co/datasets/orrp/DSWP/resolve/main/1.wav), 193,192 bytes according to the repository API. [Dataset card](https://huggingface.co/datasets/orrp/DSWP).

**The contextual/combinatorial paper's GitHub release** is much richer for social structure, but contains timing tables rather than the Hugging Face waveforms. I downloaded and inspected the two CSVs:

| Public file | Actual released rows | Exact columns / values of interest |
|---|---:|---|
| [`DominicaCodas.csv`](https://github.com/pratyushasharma/sw-combinatoriality/blob/main/data/DominicaCodas.csv) | 8,719 | `codaNUM2018`, `Date`, `nClicks`, `Duration`, `ICI1`–`ICI9`, `CodaType`, `Clan`, `Unit`, `UnitNum`, `IDN` |
| [`sperm-whale-dialogues.csv`](https://github.com/pratyushasharma/sw-combinatoriality/blob/main/data/sperm-whale-dialogues.csv) | 3,840 | `REC`, `nClicks`, `Duration`, `ICI1`–`ICI28`, `Whale`, `TsTo` |

The first table contains clan values `EC1` (7,770 rows) and `EC2` (949), 13 `Unit` values and 35 `CodaType` values, including `1+1+3`, `5R1`, `5R3` and noise categories. `IDN` has 36 distinct values but 5,705 rows contain `0`; do not treat zero as an identified animal without resolving its convention. The dialogue table has 219 distinct `REC` values and 11 `Whale` codes. These codes are not verified global individual IDs. Both CSVs together are only about 1.25 MB. [Repository and analysis notebooks](https://github.com/pratyushasharma/sw-combinatoriality).

**Paper/file discrepancy:** the paper describes 8,719 EC1 codas in 21 previously defined types and a second, temporally ordered DTag set of 3,948 codas. The public files inspected here instead have two clan codes, 35 type values and 3,840 dialogue rows. The correspondence/filtering that resolves these differences is not documented in the repository README; keep actual-file counts separate from published analytic counts. [Paper and methods](https://www.nature.com/articles/s41467-024-47221-8).

Biological interpretation: coda structure relates to identity and vocal culture; exchanges exhibit context-dependent timing modulation and ornamentation. The files provide rhythm and social grouping, not a meaning such as “food” or “greeting.” No verified join maps these table rows to the numbered Hugging Face audio. No LICENSE file was present in the inspected GitHub tree; public availability alone does not establish the timing tables' reuse terms.

**Art prototype:** draw clicks as points, inter-click intervals as spacing, duration as scale, and verified clan/unit as visual families. Use dialogue timing for overlapping paths; obtain the table-to-audio linkage from the researchers before claiming a synchronized social conversation.

## Killer whales: DCLDE, now the 2027 workshop

The release historically named DCLDE 2026 is now used for the 2027 workshop. The authors' [Zenodo v1.0.0 archive](https://zenodo.org/records/15743034) is just 4.9 MB compressed and includes both processing code and the collated annotation CSV; this is the best metadata-first starting sample. The audio corpus is much larger. [Current challenge and download entrypoint](https://www.dclde.org/challenges-and-data-sets).

**Actual collated CSV inspection:** 207,574 rows, rather than the paper's over-225,000 total for contributed annotations. Exact columns are an unnamed row index followed by `Soundfile`, `Dataset`, `LowFreqHz`, `HighFreqHz`, `FileEndSec`, `UTC`, `FileBeginSec`, `ClassSpecies`, `KW`, `KW_certain`, `Ecotype`, `Provider`, `AnnotationLevel`, `FilePath`, `FileOk`.

| Field | Values actually present / implications |
|---|---|
| `ClassSpecies` | `HW` (124,977), `KW` (59,107), `UndBio` (11,821), `AB` (11,669). Broad biological/abiotic classes; the processing code collapses finer provider labels. |
| `Ecotype` | `SRKW` (20,908), `TKW` (12,707), `NRKW` (8,266), `SAR` (8,078), `OKW` (2,698), `NA` (154,917). Southern/Northern/Southern Alaskan Residents, Transient/Bigg's and Offshore. These are population/ecotype labels, not call meanings. |
| `AnnotationLevel` | `Detection` (169,282), `Call` (37,624), `File` (668); do not assume every row delimits a discrete call. |
| `KW_certain` | `1`, `0`, `NA`: distinguish uncertainty from absence. |
| Timing/frequency | Seconds relative to audio, Hz bounds, UTC timestamps. Boxes mark spectrogram regions; they are not whale coordinates. |
| `FilePath`, `FileOk` | Author-side Windows paths and file-existence checks; reconstruct download paths using provider/site/file identifiers. |

Original provider annotations can contain matriline, pulsed-call type, buzz/rasp and other biological or vessel/noise labels that were not consistently retained in the combined table. Sensor coordinates and deployments describe recording location; they are not a caller's precise location. Annotation completeness differs by provider. [Dataset descriptor](https://www.nature.com/articles/s41597-025-05281-5).

The current NOAA `Annotations.csv` was independently re-counted on 4 October 2026: **207,574 rows**, the same class totals as above, in a 50,484,452-byte file. The [DCLDE 2027 guide](dclde-2027.md) documents all three tracks, current access paths, model candidates, and the [file/package audit](../resources/audits/dclde-2027.json).

The Zenodo **software** metadata lists MIT. NOAA's orca folder now contains a [file named `CC-BY-4.0.txt`](https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/CC-BY-4.0.txt), but its contents are **Attribution-ShareAlike 4.0 International** legal text. Preserve that discrepancy; the filename does not establish a uniform CC BY 4.0 audio license. The article license is separate.

**Art prototype:** preserve frequencies and durations as curves/rectangles, color by known population, and allow an explicit unknown state. Join finer call-type labels only within the providers that actually supply them.

## Killer-whale HFM signals: directly usable contours

The [Dryad HFM release](https://datadryad.org/dataset/doi:10.5061/dryad.8cz8w9h7f), published 23 April 2026 for Simonis et al.'s 2012 study, provides audio and manually traced time/frequency/amplitude CSV contours. Folders distinguish Aleutians, FLIP, Gulf of California, Hoke, Southern California and Washington Coast; an Excel file describes recording locations/specifications. The Dryad API reports **CC0 1.0** for the dataset.

These brief high-frequency downsweeps may serve echolocation, but the proposed function is a hypothesis, not a per-signal behavioral or semantic label. The archive is 5.99 GB; the README is 1.78 KB. This pass inspected the README/API, not the archive's CSV headers or individual contours. Start with the README and plan selective archive access rather than downloading the entire package immediately. The contour representation is especially suitable for shape generation; high frequencies also require careful choice of audio sample rate.

## Watkins: diverse species and historical observation context

WHOI verifies common/scientific species names, date, geographic recording location and researchers' notes. Its database manual also describes behavior, interaction, age/sex, animal identity, sound type and hydrophone/recording fields. Availability and detail vary by record; these are observation metadata, not uniformly annotated event-level meanings. [WHOI archive announcement and explicit terms](https://www.whoi.edu/press-room/news-release/historic-marine-mammal-sound-archive-now-available-online/); [original database manual](https://cis.whoi.edu/science/B/whalesounds/WHOI-92-31.pdf).

WHOI says personal/academic download is free, **commercial use is prohibited**, and specifies credit to “Watkins Marine Mammal Sound Database, Woods Hole Oceanographic Institution.” A third-party mirror does not automatically supersede those terms. Start with one best-of sound cut and its metadata via the [WHOI database](https://whoicf2.whoi.edu/science/B/whalesounds/) or [museum collection](https://www.whalingmuseum.org/research/digital/watkins-marine-mammal-sound-recording/).

## Humpback song and actual position data

MBARI's [2016 song-unit study](https://docs.mbari.org/hbwasa2020/methods/) describes 5,470 manually segmented units in 22 classes from one whale and a 4.5-hour session. Its eight-class analytic subset uses `A`, `Bm`, `C`, `E`, `F`, `G2`, `I3`, `II`. Those are acoustic unit categories, not meanings. A downloadable annotation/audio package and its dataset terms were not verified here, so this is a collaborator/source lead rather than a ready-to-train promise.

For a *spatial* artwork, inspect the [DCLDE fin-whale DAS release](https://doi.org/10.25921/v2vh-8w16). A complete listing found **120 arrival-pick CSVs (1.45 MB)**, **120 detection NetCDFs (103.10 GB)**, and **two cable-geometry CSVs (10.20 MB)**. An inspected annotation file contains `call_id`, `segment_id`, `utc_time`, `time`, `dist`, `call_type`, `cable`, `snr`, `filename`. Geometry coordinates locate cable sensors. No standalone whale-position reference table was found in that bucket; the authors' research repository provides an additional localization CSV. See the [DAS access and schema notes](dclde-2027.md#das-arrival-picks-are-not-source-coordinates) before interpreting coordinates. NetCDF variables and uniform data terms remain unverified.

## Right whales: Cape Cod Bay abundance challenge

The [array audio release](https://doi.org/10.25921/ab3a-c842) and [detections/aerial release](https://doi.org/10.25921/x68p-cj94) support the DCLDE density/abundance track. A complete audio listing contains **11,249 FLACs / 57.44 GB**; the separate release contains **118 candidate detection tables / 336.30 MB** and a tiny **21-row aerial survey CSV / 1,335 bytes**. Start with that CSV rather than the audio corpus.

NOAA describes synchronized five-channel, 2 kHz / 16-bit recordings. The aerial table supplies survey effort and aggregate individual counts; it has no individual whale coordinates. Candidate detections can include false positives and repeated reception across sensors. Calling rates and detectability must enter an abundance model separately. See the [DE schema and modeling notes](dclde-2027.md#right-whales-detections-do-not-directly-count-animals) and [Garcia & Tolkova et al.](https://doi.org/10.3354/esr01384).
