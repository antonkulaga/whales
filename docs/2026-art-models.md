# 2026 models: capabilities, evidence and unresolved checks

Audited **7 October 2026** for the [five proposed experiments](2026-art-ideas.md).
The [existing-project review](cetacean-art-precedents.md) covers the art and
interaction precedents. The broader [model inventory](models.md) and
[audio-model audit](audio-models.md) retain dataset and inference details.

**Assumed:** cetaceans, recorded audio and a human-operated art demo, endpoints
of controllable drawing, audible musical correspondence and traceable sound
annotations. If wrong, conclusions may change. Availability checks are research
evidence; these models have not been newly installed or benchmarked for this
investigation.

## What counts as a 2026 model

The relevant trained model or checkpoint family must have a verified 2026
release. A 2026 paper or wrapper around unchanged older checkpoints does not
meet that criterion. Architecture age is a separate question: new domain
training can make an older architecture a relevant new model.

Track three dates independently: first paper submission, public code and public
weights. A paper can precede its usable checkpoint; a conference year does not
establish a new model release. Preprints below have unverified peer-review status
unless a source explicitly establishes otherwise. Documentation may describe
examples or speed on hardware different from ours.

## Shortlist and release evidence

| Candidate | Verified 2026 evidence | What it supplies | What it does not establish |
|---|---|---|---|
| [DoLittle MMC humpback DAC9](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models) | Weight-bearing [24 July commit](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models/commit/2facc80de2eec736f5470931f11203bdb191e7a1) | Continuation of tokenized humpback recordings | A dolphin generator, semantic dialogue or biological authenticity of generated phrases |
| [ACE-Step 1.5](https://arxiv.org/abs/2602.00744) | January report; [XL announced 2 April](https://github.com/ace-step/ACE-Step-1.5) | Music generation, source-audio transformation and base-model arrangement tasks | Fidelity to out-of-domain animal audio |
| [Stable Audio 3](https://stability.ai/research/stable-audio-3) | [Released 20 May](https://stability.ai/news-updates/meet-stable-audio-3-the-model-family-built-for-artistic-experimentation-with-open-weight-models); arXiv:2605.17991 | Source-audio generation, inpainting and continuation | Preservation of particular cetacean calls without testing |
| [OpenWhistle Wav2Vec2](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0) | Weight-bearing [4 May commit](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0/commit/1b92224edab2059633d11e49daa10bf53c309394); September paper arXiv:2609.34839 | Dolphin-whistle embeddings for analysis and downstream tasks | Waveform generation or translation |
| [Dolph2Vec](https://arxiv.org/abs/2606.12503) | Paper submitted 10 June; [analysis code](https://github.com/chiarasemenzin/Dolph2Vec) | Learned representations and quantized/codebook analysis | An audited one-command reproduction with the separately published OpenWhistle checkpoint |
| [FLUX.2 klein 4B](https://bfl.ai/blog/flux2-klein-towards-interactive-visual-intelligence) | Released 15 January | Photo-guided jewelry concept rendering | Native audio input or a fabrication-ready geometry model |
| [Lyria 3.5](https://blog.google/innovation-and-ai/models-and-research/google-labs/lyria-3-5/) | July release; [Gemini API availability 4 September](https://blog.google/innovation-and-ai/products/gemini-app/better-tracks-lyria-gemini/) | Hosted music generation | Verified raw cetacean-reference conditioning in the reviewed material |
| [Soundwich](https://arxiv.org/abs/2610.00691) | First submission 30 September; revision 2 October; [code](https://github.com/CodyNing/Soundwich) | Framework for layered, timed audio with joint video generation | A newly trained cetacean model or validated whale-audio control |

WhAM's released weights are from 2025 and therefore excluded from this strict
shortlist. It remains relevant background in the [broader audit](audio-models.md).
The current [DolphinGemma page](https://deepmind.google/models/gemma/dolphingemma/)
describes development and a future release ("currently in development. On release,
it will be openly available"). On 7 October 2026 there was no public checkpoint on
Hugging Face (dolphingemma/dolphin-gemma and Google-owned repositories) or on Kaggle
(`google/dolphingemma` returns 404). Vertex Model Garden was not checked. Do not make
it a required dependency.
The [CHAT report](chat-sound-interface.md#how-dolphingemma-relates) includes the
official earlier generation figure and explains how a sound model differs
from the field interaction interface.

## Music model interfaces

### ACE-Step: distinguish style reference from structural source

The [official tutorial](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/Tutorial.md)
distinguishes two important inputs:

- `reference_audio` becomes a global timbre/style condition through temporal
  averaging. It cannot be assumed to retain the ordering of whale phrases or
  a dolphin contour's melody.
- `src_audio` provides source structure for transformation, including cover
  strength controls. Use it when testing melodic or timing correspondence.
- `lego` adds a track and `complete` adds accompaniment; these require a base
  or XL-base variant. SFT/turbo support differs, so choosing the fastest model
  can remove the task we actually need.

The useful experiment is a separately rendered pitch/onset guide passed into
an arrangement task, alongside a direct-animal-audio comparison. A musical guide
makes the intended correspondence explicit; it still does not guarantee that
the generated track follows it. Keep the original animal track independently.

The [repository](https://github.com/ace-step/ACE-Step-1.5) includes a uv setup.
Inspect the selected task/checkpoint requirements before adding it to our
environment; model variants have different memory and task support.

### Stable Audio 3: source audio, inpainting and continuation

The [official implementation](https://github.com/Stability-AI/stable-audio-3)
accepts source waveform/sample-rate pairs through `init_audio`, with
`init_noise_level` controlling how much of the source is disturbed. Inpainting
accepts time masks, which also support continuation beyond the source region.
These are actual audio interfaces, unlike conditioning music with a caption
about whales.

For this project, compare a source transformation with an accompaniment or
continuation around a measured guide. Inspect the isolated result for loss of
the contour, invented events and masking of the original. Neither the API nor
general music demos prove that the model will preserve high-frequency dolphin
acoustics. Small and Medium open releases provide different deployment choices;
runtime on our machine remains unmeasured.

Code is MIT-licensed; the weights use Stability's Community License rather than
inheriting the code license. Verify the selected model's terms and dataset terms
separately before a release of an installation.
[Medium model card](https://huggingface.co/stabilityai/stable-audio-3-medium).

### DoLittle: synthesize a whale phrase before arranging it

This humpback model continues DAC9 codec tokens. It requires tokenization of
audio into its expected codec format; a raw WAV is not itself the token prompt.
Its released context options are 10k, 32k and 128k tokens, corresponding to
approximately 13, 42 and 169 seconds of combined prompt and continuation at the
documented codec rate. A larger context is not evidence of meaningful song
structure over arbitrarily long recordings.
[Model card](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models),
[implementation](https://github.com/cairninstitute/cairn_marine_mammals_communication).

Use continuation as a labelled synthetic input to a music experiment. A guide
rendered from that continuation can go to an arranger; the generator alone does
not produce accompaniment. Model and source-corpus reuse terms differ; the
[audio audit](audio-models.md) records this distinction.

### Lyria: newer hosted music does not settle the input question

Lyria 3.5 is a current 2026 hosted candidate. The reviewed announcements establish
music generation and API availability, but not the direct raw-whale conditioning
needed for our comparison. Keep it as a hosted alternative until its current
input schema is inspected. A descriptive prompt about dolphins would evaluate
prompt-driven composition, not measured correspondence to a particular clip.

## Dolphin representations and explanatory visuals

The OpenWhistle checkpoint is a 95.1M-parameter encoder with 768-dimensional
representations at a documented 44.1 kHz input rate. Its license field is not
specified in the reviewed model card. It supplies embeddings; it does not supply
a vocoder or sound generator. Resampling for it must be recorded separately
from preservation of the original high-rate input.
[Checkpoint card](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0).

- **Training data:** about 114 hours of whistles from five bottlenose dolphins (*T. truncatus ponticus* and one *T. aduncus*) at Dolphin Reef, Eilat. This is a different population from WDP's Atlantic spotted dolphins ([paper](https://arxiv.org/abs/2609.34839), v1 28 September 2026, NeurIPS 2026 Datasets & Evaluations spotlight).
- **Loading:** the config names a custom `Wav2vec2ForPreTraining_randommask` class. `AutoModel` still loads it locally as `Wav2Vec2Model` with no missing weights; only the quantizer and projection heads go unused.
- **Measured locally ([sound brush](sound-brush.md#the-2026-dolphin-encoder-as-a-second-layer)):** with 36 enrolled synthetic examples and nearest centroids, time-averaged embeddings were at chance for rise versus fall. Order-preserving chunks of layer 9 reached 13/16 clean, 9/16 transposed and 13/24 in pool noise. Measured contour DTW scored 16/16, 16/16 and 24/24. The encoder accepted most natural whistles as commands; the contour layer accepted 2 of 13.

Dolph2Vec reports category structure in embeddings and partial codebook
specialization. The following are actual paper figures, not artwork generated
for this report:

![Dolph2Vec embedding and representational-similarity analysis](https://arxiv.org/html/2606.12503v1/figures/UMAP_RSA_matrices.png)

![Dolph2Vec codebook analysis](https://arxiv.org/html/2606.12503v1/figures/codebook_analysis_final.png)

[Figure source and methods](https://arxiv.org/html/2606.12503v1).
Clustering and selective codebook activation can guide a motif vocabulary.
They do not establish decoded words, intentions or a universal brush alphabet.
The study's limited animals/context and omitted behavioral/environmental
variables constrain transfer.

Before promising reproduction, audit the exact model revision, quantizer
configuration and preprocessing expected by the
[Dolph2Vec analysis scripts](https://github.com/chiarasemenzin/Dolph2Vec).
The separately available OpenWhistle weights are not automatically proof of
compatibility. Compare learned controls with the directly measured contour and
onset baseline; do not discard the baseline simply because it has no neural
model.

## Image and video candidates

FLUX.2 klein 4B is already the project's working photo-editing model. Its
January 2026 release and Apache-2.0 4B license qualify it for this shortlist.
The 9B variant has different terms. The announced speed is a vendor measurement;
use a fast vector/mesh preview for continuous drawing until local latency is
measured. Explicit audio-derived controls still have to reach the visual model
through a guide or instruction.
[Release and licensing](https://bfl.ai/blog/flux2-klein-towards-interactive-visual-intelligence).

Soundwich can be paired with the 2026 LTX-2.5 or MiniMax H3 backbones. Its Ovi
path uses a 2025 backbone, so exclude that path under our restriction. Layered
audio/video control is interesting for a saved performance, but introduces
substantial inference dependencies and does not establish real-time drawing.
[Paper](https://arxiv.org/html/2610.00691v2),
[included implementations](https://github.com/CodyNing/Soundwich).

![Soundwich overview: video with separate editable audio stems](https://raw.githubusercontent.com/CodyNing/Soundwich/main/assets/teaser.png)

[Author's project/demo page](https://soundwich.avdemo.workers.dev/) ·
[Direct full-length demo video](https://pub-238c8a4431a4476c8eb0f5bd97a3846e.r2.dev/media/demo/20260926/video.mp4) ·
[Repository-linked demonstration](https://github.com/user-attachments/assets/abda9d46-dbcc-4728-9311-83ea6d1ce177).
These links and the figure come from the author's README. They demonstrate the
generic audiovisual method, not conditioning on actual cetacean recordings;
remote playback was not verified in this investigation.

AudioCanvas is a useful methodological comparison, not our modern deployment
choice: its 2026 paper's public implementation uses SD 1.4 and an older CLAP,
and its README still lists uploading trained weights as a to-do.
[Author repository](https://github.com/gdx012/A2I-Generation).
A 2026 paper date does not make those components 2026 models.

## Checks before implementation

1. Pin a weight-bearing revision and verify the actual input/output contract.
2. Reproduce one official example for the chosen task before substituting animal
   audio; compare the result with the transparent guide baseline.
3. Keep model, code and recording licenses as separate provenance fields.
4. Measure latency and memory on our hardware; no new runtime claim is made here.
5. Preserve original recordings and distinguish generated continuations,
   transpositions and rendered musical guides in every saved demo.

See [the implementation sequence and acceptance criteria](2026-art-ideas.md#implementation-sequence-and-first-artifacts)
for the proposed first outputs. The ledger below concerns untested transfers
into our art setting, not a claim that these experiments have already passed.

## Evidence ledger

E = established, P = probable, S = speculative; H/M/L = confidence.
Rows concern proposed transfers into our art setting. `Cand` means they have
not been verified in our demo; published model capabilities are documented
above. Conflict flags identify material contrary findings or constraints.

| Claim | Tier | Conf | Conflict | Modality | Quality | Source | Status | Verify |
|---|---|---|---|---|---|---|---|---|
| In the proposed whale-music demo, source-audio arrangement improves timing correspondence versus prompt-only generation, measured by event alignment at first evaluation | S | L | Y | In silico | Cetacean transfer untested; global references average time | arXiv:2602.00744; ACE-Step tutorial | Cand | Source swaps and timing perturbations |
| In the proposed dolphin keyboard demo, waveform-linked controls improve reproducibility versus seed-only image edits, measured by repeatable stroke paths during replay | E | M | N | In silico | Local: stroke hash identical 3/3 across copy, fresh process and re-render; velocity −1 control changes it; phrase-level latency measured | [sound-brush.md](sound-brush.md#replay) | Measured | Human performer session with a physical keyboard |
| In the sound brush, frozen OpenWhistle embeddings with few-shot centroids improve command recognition versus measured contour DTW, measured by held-out accuracy and false accepts | E | M | Y | In silico | Local, 109 items: not supported; encoder weaker under transposition and noise and rarely rejects; synthetic sines out of domain | [sound-brush.md](sound-brush.md#the-2026-dolphin-encoder-as-a-second-layer); arXiv:2609.34839 | Measured | Trained head, negative enrollment, real mimics |
| In a dolphin feedback experiment, contingent drawing feedback improves control versus shuffled feedback, measured by learned target responses after training | S | L | Y | Animal in vivo | Vocal control evidence does not show artistic intent; CHAT field sessions found imitation without functional label use | PMID:8375147; PMID:42772609; DOI:10.26451/abc.11.02.02.2024 | Cand | Contingent versus delayed feedback |
| In controlled echoes, target-labelled training improves shape inference versus unrelated whistle input, measured on held-out targets at evaluation | S | L | Y | In silico | No reviewed validated 2026 communicated-image decoder | DOI:10.3758/BF03199007; DOI:10.4172/2155-9910.1000202 | Cand | Held-out paired echo and shape data |
| In the proposed map, recording/deployment joins improve event traceability versus location-only aggregates, measured by linked audio/annotation consistency at audit | S | M | Y | In silico | Regional anchors cannot support caller localization | Local world-map.md; DOI:10.1038/s41597-025-05281-5 | Cand | Round-trip event and coordinate provenance audit |
| In the proposed brush vocabulary, learned codebook units improve motif stability versus random units, measured under audio perturbations at evaluation | S | L | Y | In silico | Partial specialization; domain/context limits | arXiv:2606.12503 | Cand | Random-unit baseline and noise/pitch perturbations |

## Search log

Representative discovery and contrary-evidence queries, not an exhaustive
systematic review. Counts are intentionally not estimated. R/E/P/V denote
retraction, expression-of-concern, preregistration and published-version checks;
unchecked cells are not completed integrity audits. Recent-source searches
covered July through 7 October 2026, including Lyria 3.5 and Soundwich.

| Database | Query | Date | Hits | Screened | Included | Checks |
|---|---|---|---|---|---|---|---|
| Web / official model sources | 2026 open source music generation audio conditioning ACE Step 1.5 reference audio | 2026-10-07 | TBD | TBD | TBD | ☐R ☐E ☐P ☐V |
| Web / primary publications | dolphin vocal operant conditioning computer cursor whistle control experiment | 2026-10-07 | TBD | TBD | TBD | ☐R ☐E ☐P ☐V |
| Web / primary publications | 2026 sonar audio image reconstruction neural dolphin echoes -MRI -echocardiography -radar | 2026-10-07 | TBD | TBD | TBD | ☐R ☐E ☐P ☐V |
| Web / primary publications | dolphins images CymaScope replication criticism | 2026-10-07 | TBD | TBD | TBD | ☐R ☐E ☐P ☐V |
| Web / official model sources | 2026 music generation audio reference model release Lyria Stable Audio | 2026-10-07 | TBD | TBD | TBD | ☐R ☐E ☐P ☐V |
| Web / project primary sources | site.gatech.edu CHAT dolphin whistle recognition underwater computer Herzing Starner | 2026-10-07 | TBD | TBD | TBD | ☐R ☐E ☐P ☐V |
| Web / project primary sources | site.wilddolphinproject.org CHAT 2026 communication whistle interface | 2026-10-07 | TBD | TBD | TBD | ☐R ☐E ☐P ☐V |
