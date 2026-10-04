# Artistic experiments from cetacean sound

**Small experiments using public audio models with existing visual or sound models.**

Prepared **4 October 2026** for Livia's marine residency exploration.
[Model guide](models.md) · [Dataset guide](datasets.md) · [Research context](research.md)

Yes: there are useful combinations that need **no neural-network training**.
My first choices are **CLAP → descriptions → images**, **audio features → edits
of Livia's artwork**, and **audio features → drawn forms → ControlNet images**.
The connecting step can be a vocabulary, an image, or a few numerical controls.
We can choose that correspondence ourselves and make it part of the work.

**Implementation update, 4 October 2026:** ideas 1 and 2 now run through
`uv run --group art main.py art`. Following the preference for current models,
the implementation uses [FLUX.2 klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
(released January 2026) instead of SDXL-Turbo. Idea 1 keeps the CLAP-to-material
mapping; idea 2 uses a jewelry photo as the reference, with CLAP-selected material
instructions and shared-reference RMS mapped to bounded edit wording. FLUX's
native reference editing has no denoising-strength argument, so the actual edit
prompt varies while its template, reference image and seed stay fixed. The
earlier SDXL designs below remain proposals for comparison. See the
[run instructions](../README.md#next-experiments) and [data layout](../data/README.md).

The revised [Livia brief](livia-experiment-brief.md) uses her actual Nanot and
Mitoring photographs as model inputs. Idea 1 now compares silver/amber jewelry
with pavilion concepts at Livistone's architectural scale; idea 2 changes the
silver setting of Mitoring. The HTML includes Mycelium's drainage rationale
and Livistone's source scene, so the acoustic geometry choices are visibly
connected to her practice. The earlier generic paper/thread/glass trial is
preserved under ignored `data/interim/superseded-generic/`.

These are proposed artworks and engineering designs. Model capabilities and
loading routes are grounded in the linked releases. Beyond the two implemented
prototypes above, these combinations have not been run in this repo. “Low effort” assumes that the chosen checkpoints load
successfully. It does not mean a tiny download or real-time CPU generation.

## Shortlist

Effort: **S** = standard inference plus simple mapping; **M** = an extra
representation, retrieval bank, or custom rendering step; **L** = a legacy or
multi-generator stack. All ideas below use frozen weights. PCA and artist-set
reference ranges may be fitted, but no new neural model is required.

| Idea | Audio model + non-marine model | Optional extra input | Artifact | Effort / first-test priority |
|---|---|---|---|---|
| 1. Acoustic material studies | CLAP + SDXL-Turbo or SDXL | Livia's material vocabulary and style prompt | Print series: sound interpreted as glass, thread, ink, stone | S · **Start here** |
| 2. A painting listening to the sea | CLAP or AVES + SDXL image-to-image | One of Livia's paintings or photographs | Variations of one work driven by different clips | S · **Start here** |
| 3. A gallery chosen by sound | ImageBind + SDXL image-to-image | Small library of her images | Retrieved image, altered counterpart, listening gallery | M · Good for a personal visual language |
| 4. Whistle forms become objects | AVES or OpenWhistle + scribble ControlNet + SD 1.5 | Existing F0 tracks, object/material prompt | Ceramic-like forms, textile motifs, imagined sculptures | M · Strong link to the repo's contour baseline |
| 5. Acoustic counterparts on land | CLAP + AudioLDM2 | Artist-chosen environmental sound vocabulary | Paired whale/dolphin and invented terrestrial sound pieces | S/M · First sound experiment |
| 6. A score selected by a call | CLAP + MusicGen-small | Instrument palette or short written score | Short music studies accompanying source recordings | S/M · Simple bridge, loose acoustic preservation |
| 7. A whistle becomes a melody | OpenWhistle/AVES + MusicGen-melody | Annotated F0 track, instrument prompt | Mapped whistle melody and generated musical response | M · More experimental |
| 8. Sound, image, and one word | ImageBind + SDXL image-to-image | A personal image + a word such as “thread” | Interactive three-input collage or print grid | M · No adapter training |
| 9. Two models disagree | CLAP + BioLingual + SDXL | Shared descriptor palette | Diptychs comparing two machine interpretations | M · Interesting research/art interface |
| 10. An imagined song and its landscape | DoLittle + CLAP + SDXL | Real humpback token prompt, visual theme | Real/synthetic audio with associated image sequences | L · Later, after simpler pipelines work |

For ideas 1, 2, 5, and 6, replace CLAP with BioLingual only after its loading
path is checked. CLAP is a general audio model; we do not need a marine-specific
encoder for every first experiment. For dolphin structure, AVES or OpenWhistle
offers a separate comparison, with the bandwidth limits in the [model guide](models.md).

## 1. Acoustic material studies

**Pipeline:** recording → CLAP scores against acoustic descriptions → explicit
artist mapping → SDXL-Turbo text prompt → image.

Give CLAP descriptions such as “a series of short dry clicks,” “a sustained
high-pitched whistle,” and “a slowly wavering tonal sound.” Associate those
descriptions with Livia's chosen visual materials: perforated paper, drawn
threads, layered translucent glass. CLAP ranks the acoustic descriptions;
the material association is our design. It is not evidence that CLAP understands
glass as the biological meaning of a call.

Keep composition and random seed fixed across clips. Produce a contact sheet
with the source sound, chosen description, mapping, and image. Optional input:
one short instruction from Livia, such as “everything should resemble an ink
study.” **First test:** six distinct clips, three descriptors, two visual styles.
Compare with randomly assigned descriptions to see whether sound adds a useful
structure.

[CLAP similarity interface](https://huggingface.co/docs/transformers/en/model_doc/clap) ·
[SDXL-Turbo text/image inference](https://huggingface.co/stabilityai/sdxl-turbo)

## 2. A painting listening to the sea

**Pipeline:** recording → CLAP scores or AVES features → bounded controls →
SDXL image-to-image with Livia's original image.

Start with one painting. Use an explicitly selected audio feature to control
the amount of alteration; use another to select a material prompt. With AVES,
pool features and project them onto a small fixed PCA basis. Scale the controls
using the same reference clips, rather than normalizing each clip independently.
The coordinates are artistic controls, not named biological attributes.

Hold the original image, prompt template, and seed constant. **First test:**
four clips and a deliberately narrow edit-strength range. Output an original
plus four variations, with their audio and control values. Higher image-to-image
strength generally permits larger changes; there is no guarantee that a chosen
control yields a smooth or monotonic visual effect.

[AVES features](https://github.com/earthspecies/aves) ·
[SDXL image-to-image interface](https://huggingface.co/docs/diffusers/main/en/using-diffusers/sdxl#image-to-image)

## 3. A gallery chosen by sound

**Pipeline:** recording + Livia's image collection → ImageBind audio/image
similarity → selected image → SDXL image-to-image.

ImageBind already compares audio and images in one learned space. Encode perhaps
20–50 images once, retrieve a few for each recording, and let Livia select a
match before generating its altered counterpart. No paired training corpus is
needed. The personal collection supplies the visual vocabulary.

**First test:** ten clips, twenty images, top-three retrieval per clip; generate
only the selections she finds interesting. Artifact: a small web gallery or
printed triptychs of source image, retrieved association, and altered image.
ImageBind's general training may favor literal marine imagery or fail on abstract
art. Try a collection of textures and drawings as well as figurative work.

[Official ImageBind retrieval example](https://github.com/facebookresearch/ImageBind#usage) ·
[SDXL image-to-image](https://huggingface.co/docs/diffusers/main/en/using-diffusers/sdxl#image-to-image)

## 4. Whistle forms become objects

**Pipeline:** recording → AVES/OpenWhistle features → drawn geometry → scribble
ControlNet + compatible Stable Diffusion 1.5 → image of an imagined object.

Render a two-dimensional trajectory from projected framewise features, or use
an existing annotated F0 contour for the outline and the encoder for additional
controls. Feed a clean drawing to ControlNet with prompts such as “a porcelain
vessel,” “a folded paper sculpture,” or “woven linen.” The encoder does not
itself extract a validated whistle contour; these two inputs have different
provenance.

**First test:** the six contours already used by `main.py contours`, without axes,
text, or a plot legend. Compare contour-only images with encoder-controlled
variants. Artifact: six contour prints and six imagined objects. The supplied
ControlNet is for SD 1.5; it cannot simply be attached to SDXL. This creates
images of objects, not watertight 3D models for printing.

[OpenWhistle backbone](https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0) ·
[Scribble ControlNet](https://huggingface.co/lllyasviel/control_v11p_sd15_scribble) ·
[Compatible SD 1.5 weights](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5)

## 5. Acoustic counterparts on land

**Pipeline:** recording → CLAP ranking of terrestrial sound descriptions →
artist-selected prompt → AudioLDM2 → generated sound.

Compare the marine clip with descriptions such as rustling paper, rubbing glass,
or repetitive wooden knocks. Generate the selected counterpart with AudioLDM2
and present it beside the original. Livia can add a material or place: “inside
a resonant wooden room.” This makes a sonic analogy rather than an attempted
reconstruction of the animal signal.

**First test:** three recordings and three short generated counterparts. Keep
the originals available as separate tracks, then make a stereo dialogue or a
listening installation. The standard AudioLDM2 pipeline receives **text**;
we are not inserting an arbitrary CLAP audio vector into its text-conditioning
slots. Timing and pitch contours will not automatically survive this bridge.

[AudioLDM2 weights](https://huggingface.co/cvssp/audioldm2) ·
[Documented text-to-audio pipeline](https://huggingface.co/docs/diffusers/en/api/pipelines/audioldm2)

## 6. A score selected by a call

**Pipeline:** recording → CLAP acoustic descriptions → written musical mapping
→ MusicGen-small → music.

For example, repeated clicks can select a prompt for sparse wooden percussion;
a sustained whistle can select bowed strings. Livia supplies the instrument
palette and decides whether the music is a response, an accompaniment, or a
deliberate contrast. The musical interpretation comes from that mapping.

**First test:** four clips, one instrument palette, short pieces at a consistent
duration. Artifact: an EP of paired recordings, or a projection with a musical
response. MusicGen-small is the smaller starting checkpoint. This text bridge
does not impose the original rhythm; if exact event timing matters, render
notes/percussion from annotations and compare that baseline separately.

[MusicGen-small weights and loading](https://huggingface.co/facebook/musicgen-small) ·
[AudioCraft source](https://github.com/facebookresearch/audiocraft)

## 7. A whistle becomes a melody

**Pipeline:** recording → OpenWhistle/AVES similarity → chosen musical treatment;
annotated F0 → musical-register resynthesis → MusicGen-melody + treatment prompt.

Use an available F0 track to render a simple musical guide, explicitly mapping
the whistle's frequency range into an audible instrument register. Preserve
the annotation's time coordinates and gaps in the guide. An encoder can compare
the clip with artist-chosen reference sounds to select the instrument prompt;
it is optional, and does not supply the F0 annotation.

**First test:** three contours, each with a sine-wave guide and one generated
musical response. Artifact: original whistle, mapped guide, generated music,
and a drawn score. MusicGen-melody uses chroma conditioning, which folds octave
information; it may ignore details of the guide. Feeding raw ultrasonic dolphin
audio into it is a much less controlled starting point. This is experimental
musical composition, not dolphin-to-music translation.

[Melody checkpoint](https://huggingface.co/facebook/musicgen-melody) ·
[Melody/chroma input documentation](https://huggingface.co/docs/transformers/en/model_doc/musicgen_melody)

## 8. Sound, image, and one word

**Pipeline:** audio + image + text → normalized ImageBind embeddings → weighted
retrieval from an image library → SDXL edit.

Let a visitor choose a recording, a drawing, and a word. Combine the three
normalized embeddings with user-set weights, normalize the result, and retrieve
an image from Livia's collection. Use that retrieved image as the visual model's
starting image. A weighted blend is our heuristic; the library and weights
determine whether it produces interesting matches.

**First test:** a fixed grid of three sounds × three words with one drawing.
Artifact: nine images, or an interactive installation with sliders. ImageBind
supports comparable modality representations, but the blended vector is used
for **retrieval**, not assumed to be SDXL's conditioning format. This keeps all
neural models frozen while making the extra input artistically consequential.

[ImageBind modalities and embedding arithmetic](https://github.com/facebookresearch/ImageBind) ·
[SDXL image editing](https://huggingface.co/docs/diffusers/main/en/using-diffusers/sdxl)

## 9. Two models disagree

**Pipeline:** the same recording → CLAP and BioLingual → rank the same acoustic
descriptions → identical visual mapping and SDXL seed → diptych.

Use a general audio model and a bioacoustic model as two ways of organizing the
same sound. The interest is in their divergence: one print might become a dense
field of marks, another a thin thread. Display both chosen descriptions alongside
the clip. Optional extra input: a single painting used as both initial images.

**First test:** six clips, a shared vocabulary, paired outputs with fixed seeds.
Compare ranks rather than raw scores across models, because their score scales
need not be calibrated alike. Both models are related to CLAP, so this is not
a comparison of wholly independent architectures. BioLingual's card has a
checkpoint-ID issue described in the [model guide](models.md); verify loading
before treating this as a quick extension.

[BioLingual weights](https://huggingface.co/davidrrobinson/BioLingual) ·
[BioLingual paper](https://arxiv.org/abs/2308.04978)

## 10. An imagined song and its landscape

**Pipeline:** humpback DAC9 prompt → DoLittle continuation → decoded audio →
CLAP descriptions → SDXL images, using the same mapping for real and synthetic audio.

Make a short passage in which the recording becomes a generated continuation,
and the visual world develops with it. Optional extra input: one recurring
material or a drawing from Livia. Clearly mark the boundary between source
recording and synthetic continuation in the accompanying material.

**First test:** one compatible token prompt, one checkpoint, one short
continuation, and three representative stills. Assemble the stills and audio
into a storyboard before attempting a film. This is a later experiment because
DoLittle adds tokenization, codec decoding, and a separate generator setup.
Independent diffusion stills may flicker and do not establish video coherence.

[DoLittle public weights](https://huggingface.co/cairninstitute/mmc-humpback-dac9-models) ·
[Generation/codec code](https://github.com/cairninstitute/cairn_marine_mammals_communication)

## Models needed beyond the marine catalogue

| Model / checkpoint | What it accepts | Why choose it | Loading route / dependencies | Access and terms from release |
|---|---|---|---|---|
| [SDXL-Turbo](https://huggingface.co/stabilityai/sdxl-turbo) | Text; optionally an initial image | Rapid visual iteration, 1–4 denoising steps | Diffusers, PyTorch, Transformers, Accelerate; official text/image pipelines | Public weights; card lists `sai-nc-community` and separate commercial-use guidance |
| [SDXL base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) | Text; optionally initial image through img2img | More flexible image studies; base can run without refiner | Diffusers, PyTorch, Transformers, Accelerate, Safetensors | Public weights; Open RAIL++-M |
| [Scribble ControlNet](https://huggingface.co/lllyasviel/control_v11p_sd15_scribble) + [SD 1.5](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) | Drawing + text | Explicit geometry input for idea 4 | Diffusers ControlNet pipeline; both compatible checkpoints needed | Public weights; CreativeML OpenRAIL-M terms on linked releases |
| [AudioLDM2](https://huggingface.co/cvssp/audioldm2) | Text | Non-marine sound generation for idea 5 | Diffusers `AudioLDM2Pipeline`, PyTorch, Transformers, Accelerate, SciPy for WAV export | Public weights; CC BY-NC-SA 4.0 |
| [MusicGen-small](https://huggingface.co/facebook/musicgen-small) | Text; supports audio continuation in documented workflows | Smaller first music model; 300 M music decoder | Transformers MusicGen or AudioCraft; PyTorch and audio I/O | Public weights; CC BY-NC 4.0; AudioCraft code MIT |
| [MusicGen-melody](https://huggingface.co/facebook/musicgen-melody) | Text + audio-derived melody conditioning | Actual musical guide input for idea 7 | Transformers MusicGen Melody or AudioCraft; preprocessing of guide audio | Public weights; CC BY-NC 4.0 |

This is a public-checkpoint shortlist, not a claim that these are the newest or
best generators. Run audio analysis and generation sequentially and cache the
features; there is no need to keep both large models on the GPU simultaneously.
Exact download size, memory use, and runtime for these new combinations have
not been audited. Few sampling steps do not imply small GPU memory requirements.

## What I would prototype first

1. **Six acoustic material studies:** CLAP + SDXL-Turbo, with a fixed vocabulary,
   explicit material mapping, and one seed. This is the clearest first
   two-model demonstration.
2. **One painting, four sounds:** reuse the visual stack for image-to-image;
   vary bounded controls, keeping the painting and prompt fixed.
3. **Three land/sea sound pairs:** reuse CLAP descriptors with AudioLDM2, adding
   an auditory artifact without training a marine generator.

If Livia prefers geometry over verbal descriptions, move **idea 4** ahead of
the first two. The existing contour output gives us a head start. Render a
condition image from its raw annotations rather than feeding the full plotted
figure into ControlNet.

Use a handful of actual clips from [DSWP](https://huggingface.co/datasets/orrp/DSWP)
and [OpenWhistle](https://huggingface.co/datasets/dolphinteam/OpenWhistle-Classification-Finetuning),
or Livia's recordings. An annotation-only contour demo does not yet run an
audio encoder. Small clip downloads and model inference are separate next steps;
this brainstorm did not download recordings or checkpoints.

## Make the contribution of sound visible

For every artifact, save the source clip/offset, preprocessing, model revision,
descriptor scores or feature controls, artist mapping, optional input, prompt,
seed, and output. Three quick comparisons are useful: same audio with different
seeds, different audio with the same seed, and shuffled audio-to-control
assignments. They show whether the audio makes a consistent contribution.

Keep prompts materially specific if the aim is abstract work; repeatedly adding
“whale” or “ocean” may make the visual model's familiar marine imagery dominate
the differences between recordings. Optional time, location, or observed group
behavior can shape a separate visual layer when the dataset actually supplies
those fields. Keep that metadata separate from anything inferred from sound.

The residency framing could be: **an encounter between animal acoustic structure,
machine representations, and an artist's material vocabulary**. Labels may
support comparison of recurring forms or observed contexts. These experiments
do not establish the intention, emotion, or per-call meaning of the animal.
