# Dolphin datasets: labels, context, and what the sounds can mean

See the [dataset guide](datasets.md) for the combined comparison and exact label maps,
or the [model guide](models.md) for the corresponding trained systems.

Verified 2026-10-04. Inspection used public papers, Hugging Face schemas/cards and small Zenodo metadata files; no large audio or model downloads.

The strongest established interpretation is **individual identity and contact through signature whistles**. Playback experiments show dolphins respond to copies of their own signature whistles, supporting their use in addressing individuals. This does not provide a dictionary of dolphin sentences. Another dolphin can copy a signature whistle: its owner and its current caller are different annotation concepts. [Playback experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC3740840/), [observed copying between associates](https://pmc.ncbi.nlm.nih.gov/articles/PMC3619487/).

## Priorities for this repository

| Resource | Actual public annotation | Social/biological context | Position information | Best use |
| --- | --- | --- | --- | --- |
| OpenWhistle classification | Signature/non-signature whistle types, F0 contours | Signature-whistle owner association; additional family information in paper | Clip offsets; no public source coordinates | Identity-associated shapes and dolphin-specific embeddings |
| DOLPHINFREE | Whistle contours + visual group behaviour by recording minute | Foraging, travelling, socializing, milling, attraction to boat; net/context information | Four-channel TETRA + geometry for estimating directions | Wild dolphin behaviour-linked art and spatial experiments |
| Madeira odontocete dataset | Species, group behaviour, call categories, group size/calves | Observed group context, vessel/environment context | Initial sighting latitude/longitude | Small metadata-first comparison across species/behaviours |
| Oltremare controlled-environment dataset | Whistles and five-minute activity/count tables | Training, play, feeding procedure, free activity, night | Pool/device location; no per-animal trajectories | Activity-linked acoustics; restricted generalization |
| Sarasota Dolphin Whistle Database | Curated known-individual signature whistles | Known age, sex, matrilineage, associations | Separate listening-network/site context | Collaboration for richer social labels; raw database by request |

These behavioural annotations describe **what observers saw during recording**; they do not establish what each whistle says.

## OpenWhistle: accessible acoustic and identity-associated labels

`SW` means **signature whistle**; `NSW` means **non-signature whistle**, not noise. The numbered NSW categories are whistle types without known individual-specific meaning. The ten-class `all` configuration has 8,354 rows and labels:

`NSW_3`, `NSW_2`, `NSW_1`, `SW_Dana`, `SW_Luna`, `SW_Nana`, `SW_Neo`, `SW_Nikita`, `SW_Shy`, `SW_Yosefa`.

The balanced 3,000-row subset uses `NSW_1`, `SW_Luna`, `SW_Nana`, `SW_Neo`, `SW_Nikita`, `SW_Yosefa`. Class indices vary by configuration; decode through its `ClassLabel`, not a hardcoded universal mapping. Public columns are `audio`, `label`, `name`, `onset`, `offset`, `duration`, `recording_duration`, `whistle_type`, `whistle_name`, `f0_time`, `f0_hz`, `f0_conf`, `f0_ok`, `f0_bad_reason`, `f0_spectrogram`; `all` additionally has `snr_db`. The F0 arrays are ready for shape creation without an audio model. Splits are session-disjoint. [Classification card and schema](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Classification-Finetuning).

| Public component | Exact labels / metadata | Interpretation |
| --- | --- | --- |
| [Pretraining](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Pretraining) | No labels; `audio`, `start_time`, `end_time`, `duration`, `year`, `hydrophone` | 114.284 hours, 96 kHz; recording-relative timing and hydrophone channel IDs are not animal location |
| [CNN](https://huggingface.co/datasets/dolphinteam/OpenWhistle-CNN) | `noise=0`, `whistle=1`; `file_name`, `recording`, `onset`, `offset`, audio/spectrogram | Binary whistle presence; noise class is background/no-whistle, not an emotion or communication type |
| [Detection fine-tuning](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Detection-Finetuning) | Seven-element multi-label vector ordered `SW_Neo, SW_Luna, SW_Nikita, SW_Nana, SW_Yosefa, SW_Dana, NSW_1`; all-zero background; `binary_label` noise/whistle | Whistle types present in a 0.5-second window; overlapping types allowed |

The study was recorded at Dolphin Reef in the Gulf of Aqaba, 2019–2024. Its paper provides a family tree, sex, ages and signature-whistle associations. It explicitly shows signatures of dolphins absent during recording, reinforcing that **`SW_Dana` is a Dana-associated whistle type, not proof Dana emitted that clip**. Contextual and video data are described as available at the site for future integration; they are not columns in the public releases. The paper states CC BY 4.0, although the inspected HF dataset-info license field is empty. Record both facts instead of silently treating an absent Hub license as a declaration. [OpenWhistle paper, appendices A.2 and limitations](https://arxiv.org/html/2609.34839v1).

## DOLPHINFREE: first choice for open wild-dolphin behavioural context

[Data descriptor](https://essd.copernicus.org/articles/17/4495/2025/essd-17-4495-2025.html), [versioned data record](https://zenodo.org/records/14637675), [concept DOI](https://doi.org/10.5281/zenodo.14637674).

Short-beaked common dolphins, northern Bay of Biscay, summers 2020–2022. Public recordings include 275 one-minute single-channel icListen files at 512 kHz, plus 117 four-channel TETRA files totaling 162 minutes. **Behaviour annotations are visual group observations expressed as percentages per recording minute**: foraging, travelling, socializing, milling, attraction to boat; missing observations also occur. They are not per-whistle semantic labels or individual identities.

`Whistle_annotations` contains 4,637 manually verified contours as JSON dictionaries of time/frequency point lists. Observation XLSX files are separated by year/device and associated with audio files. Fishing-net context is retained; copyrighted DOLPHINFREE beacon sequences are excluded, while some other playback sequences remain. `Tetra/Hydro_coordinates` provides hydrophone geometry CSVs for time-difference/angle-of-arrival analysis. These are **sensor-relative directions to estimate**, not a released table of individual dolphin latitude/longitude or trajectories. Calibration audio containing the protected beacon is excluded. [Methods and data layout](https://essd.copernicus.org/articles/17/4495/2025/essd-17-4495-2025.html).

The [Zenodo API](https://zenodo.org/api/records/14637675) declares CC BY 4.0 and currently lists a single `DOLPHINFREE_public.zip` of 39,906,734,089 bytes. Internal XLSX/JSON schemas were described by the paper, not inspected locally. This archive packaging is a practical obstacle to a tiny first download; use OpenWhistle contours or Madeira metadata for the first prototype.

## Madeira: useful small, public biological/context metadata

[Scientific Data descriptor](https://www.nature.com/articles/s41597-026-07675-5), [Zenodo dataset](https://zenodo.org/records/17952229), [small metadata download](https://zenodo.org/api/records/17952229/files/Metadata.xlsx/content).

35 recordings, seven odontocete species, 2022–2025. The paper calls the metadata CSV, but the **actual inspected release contains `Metadata.xlsx` (36,345 bytes)**, `Dataset.zip` (2,317,060,377 bytes), and a technical-validation archive. [Current record API](https://zenodo.org/api/records/17952229).

Actual workbook headers: `Species`, `Common name`, `Species code`, `WAV file name`, `Duration (mm:ss.ms)`, `Date`, `Latitude`, `Longitude`, `Recording start (hh:mm:ss)`, `Recording end (hh:mm:ss)`, `Sea state`, `Hydrophone depth (meters)`, `Hydrophone sampling rate (kHz)`, `Group size`, `Calves`, `Group behaviour`, `Boat presence`, `Boat type`, `Boat activity`, `Call types`, `Notes`.

Actual `Group behaviour` values: `Erratic`, `Feeding`, `Feeding/Socialising`, `Resting`, `Resting/Travelling`, `Socialising`, `Socialising/Resting`, `Travelling`, `Travelling/Socialising`. These are predominant or combined **group/sighting behaviours**. Latitude/longitude represent the **initial sighting**, not localized caller positions. Call categories are recording-level tags, not annotated call onset/offset or decoded meanings. [Definitions](https://www.nature.com/articles/s41597-026-07675-5).

Species cover common dolphin, Risso's dolphin, short-finned pilot whale, sperm whale, rough-toothed dolphin, Atlantic spotted dolphin and bottlenose dolphin. Workbook species names include spelling errors (`Tursiop truncatus`, `Steno bredanesis`, `Globicephala macrorhyncus `); preserve originals and add normalized taxonomy separately. CC BY 4.0 is declared in the record API. This is a promising context-to-image pilot, but 35 clips do not establish a general behavioural classifier. [Inspected metadata file](https://zenodo.org/api/records/17952229/files/Metadata.xlsx/content).

## More socially informative resources, with access or inference limits

**Oltremare, 2025:** seven bottlenose dolphins recorded over one day; 3,111 extracted whistles and raw audio. `dataset_filtered.xlsx` associates five-minute blocks with vocalization counts, duration classes and activity. Activity codes include `ORD` (ordinary rewarded training), `PLAY` (toys/no food rewards), `FFR` (fish released near hydrophone), `NIGHT`, and `FREE ACT`. These are scheduled contexts; free activity is not reliably mapped to particular behaviours. No confirmed individual caller labels are described. Record access failed with HTTP 403 during this inspection, so the dataset license and exact downloadable workbook schema remain unverified; the paper's license does not establish the dataset's license. [Paper, sections 2.2 and 2.7](https://pmc.ncbi.nlm.nih.gov/articles/PMC12674578/), [dataset DOI](https://doi.org/10.17882/109081).

**Sarasota Dolphin Whistle Database:** the 2022 description reports 926 recording sessions of 293 dolphins, with most animals' ages, sexes, matrilineage and social associations known. Suction-cup hydrophones support attribution to known callers, a major advantage over stationary group recordings. Raw data requests are considered by the authors; this is not a fully open, bulk-download benchmark. The paper describes signature, non-signature and copied-whistle annotations and longitudinal recordings. A separate 2023 analysis of 19 mothers compares their signature whistles with/without dependent calves, finding higher maximum frequencies and wider ranges with calves. Its WHOAS deposit contains contour-extraction measurements; this is not a released full raw-audio training corpus. The deposit endpoint failed during inspection, so its file schema and license remain unverified. [Database paper and access statement](https://doi.org/10.3389/fmars.2022.923046), [mother–calf study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10318978/), [measurement deposit](https://hdl.handle.net/1912/66193).

**ICM/Associació Cetàcea HydroMoth example:** public small [Darwin Core workbook](https://zenodo.org/api/records/15658353/files/ICM-bioacustic_006_vf.xlsx/content) has event/occurrence/measurement/media tables, dates, coordinates and sound statistics. Some `behavior` text infers social/foraging activity from sound instead of documenting independently observed behaviour. `individualID` contains a human recorder's ORCID in inspected rows; it is not dolphin identity. Record API declares CC BY 4.0, while workbook rights/access fields say CC BY-NC and not-for-profit use. Resolve that contradiction before exhibition reuse; it is lower priority than Madeira/DOLPHINFREE. [Record](https://zenodo.org/records/15658353), [API license](https://zenodo.org/api/records/15658353).

## Proposal-ready framing

An evidence-grounded project could explore **identity, encounter, and movement through acoustic form**: signature-associated contours become recurring visual motifs; independently observed behaviours control visual transitions; estimated sound directions organize the space. Label the transformation as an artistic mapping and retain uncertainty. Emotion words, intentions, kinship of an unknown caller, and sentence translations are not supported by the public acoustic labels. Prefer metadata-first work, then a small licensed audio subset, before training a larger generator.
