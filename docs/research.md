# Cetacean audio for Livia's marine residency

Start with the [dataset guide](datasets.md) and [model guide](models.md) for
comparison tables; this overview connects them to the artistic questions.
The [artistic experiment brainstorm](artistic-experiments.md) records implemented
prototypes, observations and proposed sound-to-form experiments.
The **7 October investigation** connects [existing art and interaction projects](cetacean-art-precedents.md)
to [five further ideas](2026-art-ideas.md), with a [2026 model and evidence audit](2026-art-models.md).
It covers music following animal phrases, sound-operated drawing, echo/image
claims and map-linked annotations; these extensions remain proposed experiments.
The [DCLDE 2027 guide](dclde-2027.md) adds a concrete route into orca population
classification, fin-whale spatial experiments, and right-whale abundance data,
with inspected download contents and public model baselines.
[Eight further proposals](novel-projects.md) are ranked against these resources,
with a [label audit for DCLDE](dclde-opportunities.md) and a completed
[Hardata II pilot](hardata-ii-pilot.md).

Verified 4 October 2026. Scope: public data, explicit annotations, available
model releases, and feasible sound-to-form experiments. The focused reports
document their primary sources; the inventory distinguishes observations from
unverified fields. This is a starting survey, not an exhaustive literature review.

## What the labels mean

Keep these levels separate when selecting a dataset or designing the artwork:

| Level | Example | What it supports |
|---|---|---|
| Acoustic presence | `noise` / `whistle` | Detecting whistles in a window |
| Acoustic category | signature or non-signature whistle type | Comparing recurring sound patterns |
| Identity association | `SW_Luna` | A whistle type associated with Luna; caller still needs attribution |
| Biological attributes | age, sex, mother–calf relationship | Studying individuals when linked records are available |
| Observed behavior | group foraging/travelling/socializing | Relating sound to observed activity at the annotation's time scale |
| Recording position | hydrophone/deployment GPS | Locating the instrument, not automatically the vocalizing animal |
| Source position | localized call coordinates/bearing | Studying movement when localization is actually supplied |
| Communicative function | identity signaling supported by playback experiments | Interpreting a signal class with experimental evidence |
| Per-call meaning | “come here”, fear, attraction | Requires independent evidence; not provided by these binary labels |

OpenWhistle's `noise` class is the negative class for **whistle detection**.
It is not an annotated biological sound category. A negative label alone cannot
tell us whether a window contains background machinery, water noise, or another
kind of vocalization. [Dataset card](https://huggingface.co/datasets/dolphinteam/OpenWhistle-CNN)

## What we know about social function

Playback experiments show that bottlenose dolphins recognize identity from
signature-whistle frequency contour even after voice features are removed.
This gives a biological basis for a visual portrait derived from the shape of
a whistle. It does not make the portrait a literal image of what the dolphin
communicated. [Identity study](https://doi.org/10.1073/pnas.0509918103)

Dolphins can respond to copies of their signature whistles, supporting their
use as learned labels to address one another. Copies also mean whistle-owner
identity and actual caller identity must be recorded separately.
[Addressing experiment](https://doi.org/10.1073/pnas.1304459110),
[copying study](https://doi.org/10.1098/rspb.2013.0053)

Social context can alter acoustics: a study of 19 mothers found increased
maximum frequency and a wider frequency range in their signature whistles
when their own dependent calves were present. That is evidence from a
context-linked study, not a rule for assigning a “mother–calf” label to an
arbitrary high-pitched clip. [Mother–calf study](https://doi.org/10.1073/pnas.2300262120)

The OpenWhistle paper describes family metadata for resident dolphins and
contextual/video data at the site, with multimodal integration left for future
work. Those resources are not the same thing as behavioral fields in the
released Hugging Face tables. Non-signature whistle function remains less
understood. [OpenWhistle paper](https://arxiv.org/html/2609.34839v1)

## Choose a question before training

For **identity and recurring form**, start with OpenWhistle's classification
contours and named signature types. For **sound and observed group behavior**,
start with DOLPHINFREE; Madeira's 36 KB metadata workbook is a much smaller
first inspection of recording-level behavior and sighting GPS. For **rhythm and interaction**, inspect sperm-whale
timing/dialogue tables. For **geographic/ecological differences**, compare
Watkins recording metadata or DCLDE ecotypes, retaining recording-domain
differences as possible confounders. See the dataset reports for access and
precise annotation scope.

The smallest working baseline already implemented here fetches six OpenWhistle
F0 tracks and draws them alongside a radial mapping. It makes the audio-to-form
connection explicit, preserves uncertainty gaps, and supplies vector output
Livia can alter. It is an illustrative mapping, not a classifier or a trained
generative model.

Next compare it with embeddings from a frozen dolphin encoder and
CLAP/BioLingual. Evaluate whether each representation preserves whistle type,
contour similarity, or an observed behavior label across separate recording
sessions. Check whether apparent clusters instead follow hydrophone, year,
site, background noise, or duration. Do not treat a two-dimensional embedding
plot as evidence of social meaning.

If Livia creates paired audio/visual examples, fit a small mapping to her visual
parameters (curvature, density, repetition, color, deformation), rather than
immediately training a full image generator. Her annotations describe artistic
choices; keep them distinct from biological annotations. With an image model,
start with contours as structural controls or text-mediated conditioning; the
model report explains why CLAP vectors need an adapter for direct conditioning.

Keep original sample rates and band limits in the manifest. Downsampling a
96 kHz recording to 16 kHz discards frequencies above 8 kHz; that transformation
can materially change the signals available to an encoder. An encoder's mel
filter range can narrow the band further.

## Residency framing

An application direction: **“Acoustic portraits and relationships: translating
cetacean vocal identity, rhythm, and observed interaction into evolving visual
forms.”** Start with documented signal structure and let collaborations with
marine researchers determine which contextual layers can responsibly guide the
work. A useful output could let a viewer move between the recording, its
annotation, and alternative visual interpretations.

The linked residency listing emphasizes exchange with scientists, new artistic
work, and presentations at both institutions. It lists 11 October 2026 as the
application deadline; the official HIFMB call was inaccessible during this
check, so the deadline is a directory claim pending official confirmation.
[TransArtists listing](https://www.transartists.org/en/air/helmholtz-institute-functional-marine-biodiversity-hanse-wissenschaftskolleg-institute-advanced)
