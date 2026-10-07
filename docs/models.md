# Cetacean audio models

**Inference readiness, papers, code, weights, release dates, dependencies, and artistic use.**

Checked **4 October 2026** · [Dataset guide](datasets.md) · [Research plan](research.md)

Models are trained systems; [datasets](datasets.md) are the recordings and
annotations used to train or evaluate them. This guide separates audio
generation, representation learning, detection, and cross-modal alignment.
The specifications below are from released cards, code, and metadata. Model
inference and VRAM requirements have not been benchmarked in this repo.

For challenge work, use the [DCLDE 2027 model shortlist](dclde-2027.md#models-and-methods-worth-testing).
It adds pretrained orca detection/ecotype packages, Perch transfer evidence,
and DAS association/localization code to the artistic models below.

[Setup readiness](#which-models-can-we-set-up-quickly) ·
[Papers, code, dates](#papers-repositories-and-release-dates) ·
[Dependencies](#dependency-and-environment-comparison) ·
[Capabilities](#capabilities-and-training-context) ·
[Inputs and model sizes](#input-bandwidth-and-representations) ·
[Download sizes and licenses](#checkpoints-runtime-and-licenses)

## Which models can we set up quickly?

**Start with CLAP for audio/text similarity or AVES for audio features.** For
dolphin-specific embeddings, try OpenWhistle Wav2Vec2 next. For generated whale
audio, DoLittle is the more modern setup candidate, but it needs the project
scripts, a token prompt, and a separate codec. These are setup assessments from
the released artifacts and instructions, not measured installation times.

| Model | Public weights? | Inference readiness | First usable result without training | Setup route / remaining obstacle | Locally tested? |
|---|---|---|---|---|---|
| CLAP: `laion/clap-htsat-unfused` | Yes; ungated HF download | **Quick setup candidate** | Audio/text embeddings and similarity | Standard Transformers `ClapModel` + `ClapProcessor`; resample to 48 kHz | No |
| AVES base | Yes; direct download + config | **Quick setup candidate** | Framewise audio features | `esp-aves` TorchAudio loader, or maintained AVEX; use matching checkpoint/config, mono 16 kHz, batch size 1 | No |
| BioLingual | Yes; ungated HF download | **Likely quick; check loading example** | Bioacoustic audio/text similarity | CLAP-compatible HF files; card examples incorrectly name LAION's checkpoint, so use `davidrrobinson/BioLingual` and check loading diagnostics | No |
| OpenWhistle Wav2Vec2.0 | Yes; ungated HF download | **Quick candidate for backbone features** | Dolphin whistle representations | Card supplies `AutoModel` loading; verify backbone keys. Exact pretraining uses custom code; no trained task head in this release | No |
| Perch 2.0 | Yes; official Kaggle release | **Quick candidate in a separate TF environment** | Embeddings and released species logits | Choose `perch_v2_cpu` for CPU; current `perch_v2` requires TensorFlow ≥2.20 and GPU. Cetacean-specific tasks need a suitable probe | No |
| ImageBind | Yes; direct official download | **Complete route; heavier setup** | Audio/image/text retrieval | Official `imagebind_huge(pretrained=True)` loader; 4.80 GB download and older dependency stack; choose separate environment | No |
| DoLittle MMC | Yes; HF checkpoints + configs | **Project setup required** | Humpback token continuation, then decoded audio | Clone repo; install codec extra; obtain a compatible DAC9 `.npy` prompt; generation scripts default to CUDA | No |
| WhAM | Yes; Zenodo weights | **Legacy setup required** | Pseudocodas and audio transformation | Python 3.9 instructions, editable VampNet, legacy NumPy pin, `madmom`, ffmpeg, and multiple checkpoints | No |
| OpenWhistle CNN-VGG16 | Yes; PyTorch checkpoint | **Not ready from weights alone** | Binary whistle/noise only after reconstructing inference pipeline | Need exact VGG16 definition, spectrogram frontend, normalization, and output mapping; code URL not verified in linked release | No |
| NatureLM-audio | Public audio/adapter weights; **gated base LLM** | **Conditional; access and heavier setup** | Prompted English descriptions | Official uv project exists, but requires authenticated, approved access to Llama-3.1-8B-Instruct plus its weights | No |

“Quick” means that weights, preprocessing, and a documented standard loader are
available without training a new model. It does not establish dolphin call
meaning, performance on our recordings, or license suitability. A public
backbone can be ready for **features** while still needing training for
**classification**. No ready-to-run dolphin audio generator was verified.

Readiness evidence:
[Transformers CLAP loader](https://huggingface.co/docs/transformers/model_doc/clap),
[AVES loading examples and batching caveat](https://github.com/earthspecies/aves),
[BioLingual card](https://huggingface.co/davidrrobinson/BioLingual),
[OpenWhistle encoder card](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0),
[OpenWhistle CNN card](https://huggingface.co/dolphinteam/OpenWhistle-CNN-VGG16),
[Perch model variants](https://www.kaggle.com/models/google/bird-vocalization-classifier),
[ImageBind example](https://github.com/facebookresearch/ImageBind#usage),
[DoLittle scripts](https://github.com/cairninstitute/cairn_marine_mammals_communication),
[WhAM installation](https://github.com/Project-CETI/wham#installation),
[NatureLM installation and Llama access requirement](https://github.com/earthspecies/NatureLM-audio#requirements).

## DCLDE detection and localization candidates

These address monitoring tasks rather than audio generation. Availability was
checked separately from model quality. On 7 October 2026, both SPARROW ONNX
models were downloaded, hash-verified, and exercised with synthetic inputs on
CPU. The [local evidence](../resources/audits/dclde-orca-local-models.json) records
input/output shapes and runtime version. Real-audio preprocessing and accuracy
remain untested.

| Candidate | Inputs and outputs | Setup assessment |
|---|---|---|
| SPARROW `orca-detector-dclde2026-v5` | 24 kHz / 3 s through the specified dB-mel frontend; binary orca score | Public MIT ONNX package; external frontend and sigmoid required |
| SPARROW `orca-ecotype-dclde2026-v1` | 24 kHz / 3 s waveform plus original sample-rate input; five ecotype scores | Public MIT ONNX package; embedded mel/temperature scaling, external softmax and abstention |
| Perch 2.0 + fitted probe | Frozen embeddings to species/population labels | DCLDE transfer studied; downstream classifier still needs fitting |
| DORI `whisper-tiny-mm-cpu` | Marine-mammal presence/absence | Quantized ONNX screening candidate; does not identify orca ecotypes |
| DAS4Whales + Goestchel scripts | DAS arrival picks, sensor geometry, association and physical localization | Scientific-code route; confirm coordinate conventions and download only a small batch first |

The [DCLDE guide](dclde-2027.md#models-and-methods-worth-testing) has exact
package links, download sizes, class order, environment limits, and evidence
about transfer failures. The [package audit](../resources/audits/dclde-2027.json)
saves the inspected manifests and declared ONNX hashes. The public SPARROW
exports provide a more concrete DC starting point than a generic audio encoder;
they still require held-out site/provider evaluation.

## Papers, repositories, and release dates

Paper dates are **first arXiv submissions**, not conference dates. HF dates are
the **first recorded weight-bearing commit** in the inspected repository, not
repository creation or the most recent edit; historical public visibility is
not recorded. Other release dates explicitly name their evidence. An unknown
date or missing GitHub link remains unknown.

| Model | Paper / research writeup | GitHub code | HF / official weights | Paper v1 date | Weight release date / evidence |
|---|---|---|---|---|---|
| WhAM | [WhAM paper](https://arxiv.org/abs/2512.02206) | [Project-CETI/wham](https://github.com/Project-CETI/wham) | [Zenodo 17633708](https://zenodo.org/records/17633708); no official HF model verified | 2025-12-01 | **2025-12-02**, Zenodo publication date |
| DoLittle MMC | No research paper verified; [technical release blog](https://www.cairninstitute.com/blogs/DoLittle/marine_mammals_training_blog_post.html), dated 2026-08-04 | [CAIRN code](https://github.com/cairninstitute/cairn_marine_mammals_communication) | [HF: MMC humpback DAC9](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models) | Not established | **2026-07-24**, [HF weights commit](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models/commit/2facc80de2eec736f5470931f11203bdb191e7a1) |
| OpenWhistle Wav2Vec2.0 | [OpenWhistle paper](https://arxiv.org/abs/2609.34839) | Codebase named in cards; public URL not verified | [HF: Wav2Vec2.0](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0) | 2026-09-28 | **2026-05-04**, [HF weights commit](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0/commit/1b92224edab2059633d11e49daa10bf53c309394) |
| OpenWhistle CNN-VGG16 | [OpenWhistle paper](https://arxiv.org/abs/2609.34839) | DolphinWhistleExtractor named in card; public URL not verified | [HF: CNN-VGG16](https://huggingface.co/dolphinteam/OpenWhistle-CNN-VGG16) | 2026-09-28 | **2026-05-04**, [HF weights commit](https://huggingface.co/dolphinteam/OpenWhistle-CNN-VGG16/commit/6b2eca4e139fbf5f12006ffb89f56962259af00e) |
| LAION CLAP | [Feature fusion / keyword-to-caption paper](https://arxiv.org/abs/2211.06687) | [LAION-AI/CLAP](https://github.com/LAION-AI/CLAP) | [HF: HTS-AT unfused](https://huggingface.co/laion/clap-htsat-unfused) | 2022-11-12 | **2023-02-16**, [selected HF weights commit](https://huggingface.co/laion/clap-htsat-unfused/commit/25c14ec96c0ce7a0740dd55a2e877f3b755228e1); other CLAP releases differ |
| BioLingual | [BioLingual paper](https://arxiv.org/abs/2308.04978) | [david-rx/BioLingual](https://github.com/david-rx/BioLingual) | [HF: BioLingual](https://huggingface.co/davidrrobinson/BioLingual) | 2023-08-09 | **2023-07-24**, [HF weights commit](https://huggingface.co/davidrrobinson/BioLingual/commit/32b47d1291a1d09544e63a93bd4a3a390e006395) |
| AVES base | [AVES paper](https://arxiv.org/abs/2210.14493) | [earthspecies/aves](https://github.com/earthspecies/aves); [maintained AVEX](https://github.com/earthspecies/avex) | [Official checkpoint/config table](https://github.com/earthspecies/aves#pretrained-models) | 2022-10-26 | First weights date not established; package v1.0.0 announced **2025-04-11**, a separate event |
| ImageBind | [ImageBind paper](https://arxiv.org/abs/2305.05665) | [facebookresearch/ImageBind](https://github.com/facebookresearch/ImageBind) | [Official huge checkpoint](https://dl.fbaipublicfiles.com/imagebind/imagebind_huge.pth) | 2023-05-09 | First weights date not established; server modification time is not treated as release |
| Perch 2.0 | [Perch 2.0 paper](https://arxiv.org/abs/2508.04665); [underwater transfer](https://arxiv.org/abs/2512.03219) | [perch-hoplite tooling](https://github.com/google-research/perch-hoplite) | [Official Kaggle variants](https://www.kaggle.com/models/google/bird-vocalization-classifier) | 2025-08-06; transfer paper 2025-12-02 | **2025-08-07**, [official release announcement](https://deepmind.google/blog/how-ai-is-helping-advance-the-science-of-bioacoustics-to-save-endangered-species/); dates of later variants differ |
| NatureLM-audio | [NatureLM paper](https://arxiv.org/abs/2411.07186), ICLR 2025 | [earthspecies/NatureLM-audio](https://github.com/earthspecies/NatureLM-audio) | [HF: NatureLM-audio](https://huggingface.co/EarthSpeciesProject/NatureLM-audio); [required Llama base](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) | 2024-11-11 | **2025-04-24**, [first recorded HF weights commit](https://huggingface.co/EarthSpeciesProject/NatureLM-audio/commit/8d6eb55493984186c4aceec22d03f09e8101d8da) |

The [release audit](../resources/audits/model-releases.json) saves exact bytes,
revisions, and HF date evidence. Dates identify the specific artifacts linked
here; they do not imply all model variants were released together.

## Dependency and environment comparison

This table lists the main inference requirements, not every training,
benchmarking, or notebook dependency. Published version pins describe upstream
environments and have not been resolved together in this repo. Keep incompatible
stacks in separate uv environments; the base project currently installs no ML
framework.

| Model / route | Python evidence | Core dependencies | Extra setup / compatibility issue | Dependency source |
|---|---|---|---|---|
| CLAP via HF | Use repo Python 3.12; upstream Python floor not audited | `torch`, `transformers`, audio loader/resampler such as `soundfile` + `librosa` | Selected weights are `.bin`; use a current compatible PyTorch/Transformers pair. Full LAION training stack is unnecessary for HF inference | [HF loader](https://huggingface.co/docs/transformers/model_doc/clap); [LAION requirements](https://github.com/LAION-AI/CLAP/blob/main/requirements.txt) |
| AVES via `esp-aves` | ≥3.10; AVEX route ≥3.11,<3.14 | `torch>=2.0`, `torchaudio>=2.0`, `soundfile>=0.13`; packaged requirements also include `onnxruntime>=1.20.1` | Download matching TorchAudio weights/config; use batch size 1 due to documented padding effects | [AVES manifest](https://github.com/earthspecies/aves/blob/main/pyproject.toml); [AVEX manifest](https://github.com/earthspecies/avex/blob/main/pyproject.toml) |
| BioLingual via HF | HF route can use Python 3.12; original stack has 2023 pins | HF: `torch`, `transformers`, audio loader/resampler. Original stack: `torch==2.0.0`, `torchaudio==2.0.0`, `transformers==4.27.4`, `numpy==1.24.4` | Avoid copying original training pins into the current base environment; verify actual BioLingual repo ID | [HF card](https://huggingface.co/davidrrobinson/BioLingual); [original requirements](https://github.com/david-rx/BioLingual/blob/main/requirements.txt) |
| OpenWhistle Wav2Vec2.0 | No Python version pinned in inspected card; 3.12 is a candidate | `torch`, `transformers`, `safetensors`, audio loader/resampler | 44.1 kHz mono normalization; custom pretraining class may be needed for exact reproduction | [Encoder loading card](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0) |
| OpenWhistle CNN-VGG16 | Not specified | `torch`; project VGG16/image/spectrogram preprocessing dependencies not fully specified | `torch.load` reads a checkpoint, but does not establish a complete runnable model; exact project pipeline still needed | [CNN card](https://huggingface.co/dolphinteam/OpenWhistle-CNN-VGG16) |
| Perch 2.0 via current Hoplite | ≥3.10,<3.15 for tooling | `perch-hoplite[tf]`, `tensorflow>=2.20`, `kagglehub`; tooling also uses NumPy ≥2 and librosa ≥0.11 | Explicit CPU vs GPU variant; GPU extra is `tf-cuda`. Keep TensorFlow stack separate | [Tooling manifest](https://github.com/google-research/perch-hoplite/blob/main/pyproject.toml); [model registry](https://github.com/google-research/perch-hoplite/blob/main/perch_hoplite/zoo/model_configs.py) |
| ImageBind | README recommends 3.10 | `torch>=2.0`, `torchvision`, `torchaudio`, `timm`, `einops`, `ftfy`, `iopath`, pinned Git revision of `pytorchvideo` | Install official repo; older frontend/dependency compatibility needs a smoke test | [Requirements](https://github.com/facebookresearch/ImageBind/blob/main/requirements.txt) |
| DoLittle MMC | ≥3.10 | `torch>=2.5`, `torchaudio>=2.5`, `numpy>=1.26`, `librosa>=0.10`, `soundfile>=0.12`, `pyyaml` | `[audio-codec]` adds `dac>=0.4`, Git `lac`, and Git `descript-audiotools`; codec download separate | [Project manifest](https://github.com/cairninstitute/cairn_marine_mammals_communication/blob/master/pyproject.toml) |
| WhAM | README uses 3.9 | `torch`, `transformers`, `soundfile`, `argbind`; bundled VampNet pins `numpy<1.24` and `pydantic==2.10.6` | Editable WhAM/VampNet installs, Git codec/audio dependencies, `madmom`, system ffmpeg, Gradio; legacy pins conflict with several modern stacks | [WhAM setup](https://github.com/Project-CETI/wham/blob/main/setup.py); [VampNet setup](https://github.com/Project-CETI/wham/blob/main/vampnet/setup.py) |
| NatureLM-audio | ≥3.10; GPU wheel in manifest targets CPython 3.10/Linux/CUDA 11.8 | `torch>=2.2.2`, `torchaudio>=2.2.2`, `transformers[sentencepiece]>=4.44.2`, `peft>=0.11.1`, Git `beans-zero` | HF authentication + approved Llama access; GPU group adds a platform-specific FlashAttention wheel and `bitsandbytes`; `uv sync --no-group gpu` is documented for CPU/macOS | [Project manifest](https://github.com/earthspecies/NatureLM-audio/blob/main/pyproject.toml); [installation](https://github.com/earthspecies/NatureLM-audio#installation) |

## Capabilities and training context

| Model / release | Model kind | Animals / domain | Architecture | Training context / related dataset | Output | Role in Livia's project |
|---|---|---|---|---|---|---|
| [WhAM](https://github.com/Project-CETI/wham) | Audio generator + encoder | Sperm-whale codas | VampNet-derived transformer; masked acoustic tokens | General/animal audio adaptation, then DSWP coda fine-tuning | Synthetic pseudocodas, audio style transfer, embeddings | Coda variations and rhythm/texture controls |
| [DoLittle MMC](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models) | Audio generator | Humpback song | Autoregressive codec-token transformer; attention + MoE | SanctSound humpback DAC9 corpus | Audio-token continuation, decoded through DAC | Evolving song fragments and temporal visual sequences |
| [OpenWhistle Wav2Vec2.0](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0) | Audio encoder | Dolphin whistles | Wav2Vec2-style self-supervised transformer | OpenWhistle Pretraining; supervised sets support task heads | Framewise audio representations | Whistle similarity and visual trajectories |
| [OpenWhistle CNN-VGG16](https://huggingface.co/dolphinteam/OpenWhistle-CNN-VGG16) | Binary detector | Bottlenose dolphin whistles | VGG16-based PyTorch CNN | OpenWhistle CNN windows; session-separated evaluation | `whistle` / `noise` classification | Find candidate whistle windows in longer recordings |
| [LAION CLAP](https://huggingface.co/laion/clap-htsat-unfused) | Audio/text encoder | General audio | HTS-AT audio encoder + text encoder; contrastive alignment | Paired general audio and natural-language descriptions | Audio/text embeddings and candidate similarity | Match acoustic descriptions to artist-defined visual controls |
| [BioLingual](https://huggingface.co/davidrrobinson/BioLingual) | Audio/text encoder | Bioacoustics | CLAP-style contrastive audio/text model | AnimalSpeak bioacoustic audio/text training | Audio/text embeddings and similarity | Biological sound retrieval and descriptor experiments |
| [AVES](https://github.com/earthspecies/aves) | Audio encoder | Animal and general sounds | HuBERT-derived self-supervised transformer | `core`, `bio`, `nonbio`, and `all` training variants | Audio representations; separate probes classify | Compare acoustic structure with a bioacoustic baseline |
| [ImageBind](https://github.com/facebookresearch/ImageBind) | Multimodal encoder | General multimodal data | Modality-specific encoders in an aligned space | Image-centered alignment across six modalities | Comparable audio/image/text embeddings | Retrieve or select Livia's images using sound |

**Audio generation:** WhAM and DoLittle produce animal-like sound. **Text
alignment:** CLAP and BioLingual compare audio with supplied descriptions.
**Image alignment:** ImageBind can compare audio and image embeddings. None of
these releases by itself is a complete sound-to-image generator.

Training and architecture sources: the linked releases above,
[BioLingual training repository](https://github.com/david-rx/BioLingual),
and the [detailed model audit](audio-models.md).

## Input, bandwidth, and representations

Sample rate and retained frequency range are different properties. A 48 kHz
waveform does not imply a model uses all frequencies below 24 kHz.

| Model / audited variant | Actual input | Sample rate | Retained band / important limit | Window / context | Representation size | Parameters / architecture size |
|---|---|---|---|---|---|---|
| WhAM | Audio context through its codec pipeline | 16 kHz in published pipeline | At most 8 kHz after resampling | Published tokenizer input: 10 s | Embedding choice depends on extraction layer; not standardized here | Total count not verified |
| DoLittle MMC | DAC9 token array (`.npy`); raw audio needs tokenization | 44.1 kHz codec | At most 22.05 kHz before codec reconstruction effects | 10,240 / 32,768 / 131,072 interleaved tokens | Nine codec codebooks; not a CLAP-style semantic vector | 10k: 479 M reported; medium counts inconsistent in release blog, not verified |
| OpenWhistle Wav2Vec2.0 | Normalized mono waveform | 44.1 kHz | At most 22.05 kHz; narrower than its 96 kHz source archive | Sequence input; no maximum duration established here | 768-dimensional hidden states | 95.05 M released parameters; 12 layers, 8 heads |
| OpenWhistle CNN-VGG16 | Normalized RGB spectrogram image | No raw-waveform input | Depends on the project spectrogram frontend | 224 × 224 pixels; dataset windows 0.4 s | Binary classifier output | Exact parameter count not inspected |
| CLAP: `clap-htsat-unfused` | Waveform and/or text | 48 kHz | Audited mel frontend: 50–14,000 Hz | 10 s preprocessing window | 512-dimensional projected embeddings | Total count not verified |
| BioLingual: `davidrrobinson/BioLingual` | Waveform and/or text | 48 kHz | Audited mel frontend: 50–14,000 Hz | 10 s preprocessing window | 512-dimensional projected embeddings | Total count not verified |
| AVES base variants | Mono waveform | 16 kHz | At most 8 kHz after resampling | Variable audio length; no maximum established here | 768-dimensional base-model states | About 95 M per original README; exact release count not inspected |
| ImageBind released audio loader | Waveform, converted to mel features | 16 kHz | At most 8 kHz after resampling | Three 2 s clips by default; 128 mel bins | Shared modality representation; dimension not audited here | Released huge checkpoint; count not verified |
| Perch 2.0 | Mono waveform | 32 kHz | At most 16 kHz before frontend processing | 5 s | 1,536-dimensional embeddings | About 12 M encoder + 91 M classification head, per official card |
| NatureLM-audio | Audio + text prompt | Use official loader; input rate not audited here | Selected audio frontend still needs inspection | Official CLI defaults to 10 s windows; configurable | English text; internal features are not a standardized output here | 665.38 M in released audio/adapter file **plus** Llama-3.1-8B base |

Specifications:
[WhAM methods](https://arxiv.org/html/2512.02206v1#A5.SS2),
[DoLittle tokenizer](https://github.com/cairninstitute/cairn_marine_mammals_communication/blob/master/src/tokenizer/dac_tokenizer.py),
[OpenWhistle encoder](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0),
[OpenWhistle detector](https://huggingface.co/dolphinteam/OpenWhistle-CNN-VGG16),
[CLAP processor](https://huggingface.co/laion/clap-htsat-unfused/blob/main/preprocessor_config.json),
[BioLingual processor](https://huggingface.co/davidrrobinson/BioLingual/blob/main/preprocessor_config.json),
[AVES input documentation](https://github.com/earthspecies/aves),
[ImageBind audio loader](https://github.com/facebookresearch/ImageBind/blob/main/imagebind/data.py).
Additional specifications:
[DoLittle size report](https://www.cairninstitute.com/blogs/DoLittle/marine_mammals_training_blog_post.html),
[Perch official card](https://www.kaggle.com/models/google/bird-vocalization-classifier),
[NatureLM inference](https://github.com/earthspecies/NatureLM-audio#run-inference-on-a-set-of-audio-files-in-a-folder).
DoLittle's blog lists 205 M for the 32k preset but refers to a 375 M medium model
elsewhere; these are not treated as an exact audited checkpoint count.

### DoLittle checkpoint choices

| Family | Attention / architecture | Context tokens | Approximate total audio context | Inference checkpoint | Resume checkpoint available? |
|---|---|---:|---:|---:|---|
| 10k | Sliding-window attention + MoE | 10,240 | 13.2 s | 1.92 GB | Yes |
| 32k | Sliding-window attention + MoE | 32,768 | 42.3 s | 1.50 GB | Yes |
| 128k | Compressed attention + MoE | 131,072 | 169 s | 1.50 GB | No resumable checkpoint in the audited release |

Audio duration is calculated as `tokens / (9 × 44100 / 512)`. Context is shared
by prompt and continuation. File size is disk download size, not GPU memory.
[Release and configs](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models),
[saved file metadata](../resources/audits/model-releases.json)

## Checkpoints, runtime, and licenses

`Released` means an artifact is available. It does not mean its inference path
has been tested locally. GPU requirements below describe documented usage or
an unmeasured CPU option; no minimum VRAM figures are claimed.

| Model | Released checkpoint / disk size | Loading path and environment | Compute evidence | Weight license / code license | Readiness for this repo |
|---|---|---|---|---|---|
| WhAM | Zenodo coarse/fine/codec/beat files; about 3.09 GB total | Legacy Python 3.9 instructions; VampNet, `madmom`, ffmpeg, Gradio | CUDA browser example; paper uses NVIDIA A10 | Weights **CC BY-NC-ND 4.0**; code MIT | Separate environment and inference check needed |
| DoLittle MMC | `best_model.pt`: 1.50–1.92 GB; codec required separately | Repo scripts; Python ≥3.10, PyTorch/Torchaudio ≥2.5, DAC | Generation defaults to CUDA; decoder loads DAC on CPU | Weights/configs/docs Apache-2.0; dataset custom terms | One checkpoint + compatible token prompt is a small first run |
| OpenWhistle Wav2Vec2.0 | `model.safetensors`: 380 MB | HF/Transformers; exact pretraining behavior may require project-specific code | CPU/GPU inference path not benchmarked here | Weight license unspecified | Backbone released; task head and loading smoke test needed |
| OpenWhistle CNN-VGG16 | `model_vgg_final_best.pt`: 63.9 MB | PyTorch + exact project VGG16 reconstruction and normalization | Card shows CPU checkpoint loading; throughput unmeasured | Weight license unspecified | Detector released; reconstruct frontend/model before use |
| CLAP, audited HF variant | `pytorch_model.bin`: 615 MB | HF/Transformers; LAION implementation also available | CPU/GPU inference not benchmarked here | HF weights Apache-2.0; LAION upstream code CC0 | Candidate baseline; preserve the audited preprocessing |
| BioLingual | `pytorch_model.bin`: 615 MB | HF/Transformers and official BioLingual implementation | CPU/GPU inference not benchmarked here | HF weight license unspecified | Candidate bioacoustic baseline; inference and terms unresolved |
| AVES | Selected `aves-base-bio.torchaudio.pt`: 378 MB; other variants/formats differ | Original AVES or AVEX wrappers; AVEX requires Python ≥3.11,<3.14 | Official examples include CPU extraction | Original AVES/AVEX code MIT; checkpoint terms need separate check | Quick features candidate with matching config |
| ImageBind | Official `imagebind_huge.pth`: 4.80 GB | Official PyTorch code; README uses Python 3.10 | Official example supports CPU or CUDA; local resource needs unmeasured | LICENSE says CC BY-NC-SA 4.0; README says CC BY-NC 4.0 | Complete retrieval example; heavier separate environment |
| Perch 2.0 | Kaggle GPU variant shows 410.28 MB package; CPU package size not separately audited | Hoplite + TensorFlow; choose CPU/GPU variant explicitly | Card says current `perch_v2` requires GPU; `perch_v2_cpu` supports CPU | Official model Apache-2.0 | Quick embeddings candidate; separate TensorFlow environment |
| NatureLM-audio | Audio/adapter `model.safetensors`: 1.56 GB **plus** Llama-3.1-8B-Instruct | Official uv project; Python ≥3.10; gated Llama access | CPU/macOS install route documented; full inference resource needs unmeasured | Audio/adapter CC BY-NC-SA 4.0; base Llama has separate terms | Conditional on base-model access; substantially larger stack |

Sizes are decimal MB/GB from file metadata, excluding dependencies, caches,
additional codecs, and training-resume state. The
[model-release snapshot](../resources/audits/model-releases.json) records
exact HF file bytes and revisions for six repositories, Zenodo file sizes, and
HTTP `Content-Length` for the selected AVES and ImageBind files. Perch's size
is the package size displayed by Kaggle, rather than a byte-level file audit.
Neither parameter counts nor file sizes establish minimum RAM/VRAM.

License/runtime sources:
[WhAM weights](https://zenodo.org/records/17633708),
[WhAM installation](https://github.com/Project-CETI/wham#installation),
[DoLittle dependencies](https://github.com/cairninstitute/cairn_marine_mammals_communication/blob/master/pyproject.toml),
[CLAP weight card](https://huggingface.co/laion/clap-htsat-unfused),
[CLAP code LICENSE](https://github.com/LAION-AI/CLAP/blob/main/LICENSE),
[AVEX dependencies](https://github.com/earthspecies/avex/blob/main/pyproject.toml),
[ImageBind LICENSE](https://github.com/facebookresearch/ImageBind/blob/main/LICENSE).
OpenWhistle and BioLingual license gaps are stated in their linked cards or
recorded in Hub metadata.

## What labels do model outputs actually provide?

| Model | Labels / outputs available directly | What requires additional training or evidence |
|---|---|---|
| WhAM | Generated audio and extracted representations | Its reported rhythm/social-unit/“vowel” tasks use downstream classifiers and partly unavailable annotations |
| DoLittle | Predicted audio-codec tokens and decoded waveform | Behavior, caller identity, or meaning is not an output category |
| OpenWhistle Wav2Vec2.0 | Learned audio features | A classification/detection head must be trained on the relevant labeled dataset |
| OpenWhistle CNN-VGG16 | Binary `whistle` vs `noise` | Whistle type, owner, caller, behavior, and emotion are outside the binary target |
| CLAP / BioLingual | Similarity between audio and supplied text candidates | Candidate scores are not a transcription, confirmed behavior annotation, or measured emotion |
| AVES | Audio features | Species/type/identity decisions need a trained probe or task head |
| ImageBind | Cross-modal similarity / retrieval | Visual generation needs a separate generator; retrieved imagery is an aesthetic association |
| Perch 2.0 | 1,536-dimensional features and released species logits; vocabulary in `assets/labels.csv` | Cetacean call type, individual identity, or behavior requires task-specific validation/training |
| NatureLM-audio | Generated English answers to audio + text prompts | Answers need verification; they are not ground-truth dolphin social labels |

The OpenWhistle detector card reports test **F1 0.9725** and recall **0.9799**
on its session-separated benchmark. Those results apply to that binary task
and recording domain; they are not comparable to a generator's realism or an
encoder's identity-classification score.
[Detector evaluation](https://huggingface.co/dolphinteam/OpenWhistle-CNN-VGG16)

## Routes from sound to visual form

| Route | Model needed | Visual result | Data / training needed | Main evaluation question |
|---|---|---|---|---|
| Contour or click timing → geometry | None | Curves, radial forms, spacing, repetition | Existing F0/contour/click annotations and an explicit mapping | Does the shape preserve the chosen acoustic feature? |
| Audio embedding → visual parameters | OpenWhistle, AVES, CLAP, or BioLingual | Curvature, density, color, deformation controls | Livia's chosen mapping; optional small paired training set | Do intended controls change consistently across recordings? |
| Audio → text descriptors → image prompt | CLAP/BioLingual; separate image generator | Generated or altered image | Candidate vocabulary, artistic prompt design | Are chosen descriptors stable and useful to the artist? |
| Audio → image retrieval | ImageBind | Selection from Livia's image library | Her images; no new adapter required for similarity retrieval | Do retrieved images express a useful aesthetic connection? |
| Audio embedding → image-generator adapter | Frozen audio encoder + compatible visual model | Direct audio-conditioned generation/editing | Paired sound/visual examples and adapter training | Does the adapter preserve the intended relation on held-out sound? |

CLAP and CLIP have different learned coordinate spaces. Matching embedding
dimensions does not make CLAP a replacement for an image generator's text
conditioning. A direct route needs a compatible adapter and training objective;
a text-mediated route makes the correspondence explicit.
[CLAP architecture](https://github.com/LAION-AI/CLAP),
[ImageBind architecture](https://github.com/facebookresearch/ImageBind)

## Additional models and supporting software

| Resource | Kind | Input → output | Why consider it | Access / limits | Audit depth |
|---|---|---|---|---|---|
| [Perch 2.0](https://www.research.google/blog/how-ai-trained-on-birds-is-surfacing-underwater-mysteries/) | Bioacoustic embedding/classification model | 32 kHz, 5 s audio → representations/species logits | Google's evaluation includes underwater transfer | Official Apache-2.0 Kaggle weights; CPU and GPU variants; cetacean probe still needed | Card, registry, dependencies and release announcement inspected |
| [NatureLM-audio](https://huggingface.co/EarthSpeciesProject/NatureLM-audio) | Audio-language model | Audio + prompt → English answers/captions | Descriptive interface for exploratory annotation | BEATs + Llama-3.1-8B; CC BY-NC-SA; adapter/audio weights 1.56 GB **plus** base LLM | Card and HF file metadata inspected |
| [AVEX](https://github.com/earthspecies/avex) | Model-loading/training library | Wraps different audio backbones and probes | Shared inference and transfer-learning tools | MIT library; Python ≥3.11,<3.14; model terms vary | Library, not a single model |
| [Perch Hoplite](https://github.com/google-research/perch-hoplite) | Embedding and modeling tools | Manages embedding workflows | Current tooling for Perch experiments | Tooling terms differ from selected model terms | Supporting software |

NatureLM's card says individual identification was not tested, and call-type
and life-stage classification were evaluated on birds. Its generated answers
should therefore not become verified dolphin social labels without independent
evidence. [NatureLM scope](https://huggingface.co/EarthSpeciesProject/NatureLM-audio)

## First experiments

1. Use the implemented F0-to-shape baseline and retain its source annotations.
2. Compare a frozen OpenWhistle encoder with acoustic features on session-separated data.
3. Add the audited CLAP checkpoint for text-mediated controls; inspect lost frequency content.
4. If synthetic sound belongs in the work, try one DoLittle checkpoint and one token prompt.

The [detailed audio-model audit](audio-models.md) contains generation controls,
frequency tradeoffs, and source-specific installation notes. All mappings to
visual form here are proposed artistic/engineering designs. They are not claims
that the models decode animal intent.
