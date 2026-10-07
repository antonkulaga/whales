# Artistic experiments from cetacean sound

Brainstorm revised **4 October 2026**, after generating and reviewing the first
experiments with Livia's jewelry photographs and real cetacean recordings.
[Artist brief](livia-experiment-brief.md) · [Model guide](models.md) ·
[Dataset guide](datasets.md) · [Run instructions](../README.md#next-experiments)

The **7 October investigation** extends this brainstorm with
[existing art and interaction projects](cetacean-art-precedents.md),
[five new ideas and their first experiments](2026-art-ideas.md), and
[a strict 2026 model audit](2026-art-models.md). It covers music accompaniment,
sound-operated drawing, the dolphin-image claim and map-linked listening.
The observations below describe the earlier runs; the new experiments are
proposals with explicit comparisons and success criteria.

The starting point is Livia's actual practice: digitally modeled, printed and
cast silver settings around natural materials. Mitoring combines amber with
folded silver; Mycelium addresses drainage around porous opal; Nanot explores
an open lattice. Livistone enlarges jewelry into inhabited spaces. Sound can
change a setting, select a material gesture, organize a sequence, or answer an
object acoustically. These are our proposed correspondences, not rules authored
by Livia or decoded animal meanings.

## What the first outputs taught us

| Experiment actually run | Observation | Consequence for the next experiment |
|---|---|---|
| Generic paper/thread/glass images | The visual vocabulary had little connection to Livia | Begin with an actual piece and its material or functional problem |
| CLAP → jewelry/pavilion prompts | Three winning descriptions gave only three directions; repeated winner/reference/seed combinations produced identical images | More recordings alone do not add expressive range to a three-way mapping |
| Bounded Mitoring edits | “Very subtle,” “subtle,” and “moderate” instructions produced changes the user found too small | Give the silver permission to change silhouette substantially; retain a no-sound comparison |
| Whole-recording silver/amber meshes | Duration, centroid and RMS visibly changed numerical geometry, but the ribs felt like imprisonment | Measurable influence is not sufficient artistic justification; use outward surfaces, growth, folds or relief when those suit the piece |
| Substantial CLAP-directed jewelry redesigns | Terraces, a crest and opening petals produced clear differences on both Mitoring and Mycelium | This is the current visual starting point; test richer controls and source fidelity next |
| The same substantial edits | Some results changed stone shape or details despite preservation instructions | A photograph is a reference, not a geometric constraint; distinguish concept images from faithful edits and fabrication models |
| Listening gallery | Quiet/high-frequency audio was difficult to hear; audio in the output column confused the relationship | Put jewelry and playable audio in Input; show scores/instructions in Schema; put generated images in Output |
| [Sound brush](sound-brush.md) (7 Oct) | Keyboard sounds measured from the emitted WAV gave legible, replayable effects. Bend added 44° of turn, hold doubled length, velocity widened the stroke, and a key switched fold to open. Recorded whistles were rejected as commands and drew thin continuous lines | Explicit contour controls make sound influence substantial and explainable. Next: a human performer, then a FLUX concept stage that swaps guides at a fixed seed |

The current `art jewelry` run contains **six sound-directed images and two
no-sound redesigns**, from two photographs and three selected recordings. The
no-sound redesign uses the same photo, seed, generation settings and substantial
edit template; only the operation text differs. It is a generated comparison,
not an unchanged copy of the original.

The implemented visual model is
[FLUX.2 klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B), through
`Flux2KleinPipeline`. Reuse this working reference-editing stack for initial
visual tests. SDXL-Turbo, SD 1.5 and their ControlNets are historical alternatives,
not prerequisites for the ideas below. Diffusers is the inference library;
the selected checkpoint determines the visual model.

### What CLAP does in our implementation

A recording is mixed to mono and anti-aliased to 48 kHz. The current analyzer
reads its first ten seconds at most; shorter inputs are repeat-padded by the
checkpoint's processor. Its log-mel frontend covers 50 Hz–14 kHz in 64 bands.
The model produces a projected audio embedding and compares it with embeddings
of supplied acoustic sentences. Cosine scores rank those candidates; they are
not probabilities, a free caption, or validated call labels.

Currently, the winning sentence selects one of three instructions:
**clicks → terraces**, **whistle → crest**, **wavering → petals**. FLUX receives
the jewelry photograph and the instruction text. It receives neither the
waveform nor the CLAP vector. Stronger edits changed the artistic instruction,
not this connection between models. A broader or temporal connection remains
future work. [CLAP interface](https://huggingface.co/docs/transformers/en/model_doc/clap)
· [Audited checkpoint frontend](https://huggingface.co/laion/clap-htsat-unfused/blob/main/preprocessor_config.json)

Longer actual inputs are already available locally: two OpenWhistle pretraining
recordings of **30.8 and 36 seconds at 96 kHz**. `art long-forms` analyzed their
whole waveforms and compared 5-second, 15-second and full prefixes. That does
not mean our CLAP analyzer now processes a whole recording. Its crop must be
replaced by an explicit windowing scheme for a temporal CLAP experiment.

## Revised shortlist

Effort is relative to our working environment: **S** reuses the current stack;
**M** adds a representation, renderer or interaction; **L** needs another model
or substantial geometry work. These are estimates, not completed runtime tests.

| Idea | Inputs and connection | First artifact | Status / effort |
|---|---|---|---|
| 1. A richer acoustic vocabulary | Sound → several CLAP axes → a substantial silver instruction | Same piece across a wider family of forms | Three-way baseline exists; extension S |
| 2. A piece substantially reimagined | Jewelry photo + sound → CLAP-selected operation → FLUX reference edit | Source, sound-directed redesign and no-sound comparison | Implemented; refinement S |
| 3. Sound chooses from Livia's own material library | Sound → CLAP scores for artist-tagged references → selected reference + edit | Retrieval/edit triptychs | Proposed; M |
| 4. A whistle leaves a silver gesture | Annotated F0/time → outline, relief or fold guide → rendered concept | Contour, guide and outward silver form | Contour baseline exists; next M |
| 5. Jewelry answers the recording | Source timing + recorded material sound → resynthesis or convolution | Original and a silver/wood/glass response | Proposed; next S/M |
| 6. A call becomes a written score | Onsets/intervals → artist's instrument mapping → rendered notes | Timeline, score and playable response | Proposed; S/M |
| 7. A whistle becomes an audible melody | Annotated F0 → declared register mapping → instrument guide | Original, mapped guide and optional accompaniment | Proposed; M |
| 8. A visitor changes the correspondence | Jewelry + sound + a word/gesture → controllable edit instruction | Small interactive gallery | Proposed; M |
| 9. Two representations disagree | Same audio → CLAP vs another encoder or explicit features → same design vocabulary | Explained diptychs | Proposed; M/L |
| 10. Real and imagined whale phrases | Real prompt → WhAM or DoLittle → separately labeled visual responses | Paired audio and storyboard | Proposed; L |
| 11. A recording unfolds through one piece | Long audio → windowed CLAP/feature trajectory → reference-anchored states | Synchronized six-state storyboard | Proposed; next M |
| 12. Jewelry becomes an inhabited sound space | Jewelry + Livistone context + sound → architectural operation | Ring/pavilion pair or room sequence | Pavilion baseline exists; refinement M/L |

Most first tests can use frozen neural weights. Feature ranges, retrieval tags,
windowing and artistic correspondences still need design. A learned direct
CLAP-to-image adapter would be a separate training project, not a parameter
we can switch on in the current pipeline.

## 1. A richer acoustic vocabulary

**Pipeline:** recording → CLAP scores within several acoustic candidate groups
→ explicit silver operations → FLUX edit of a source piece.

The current winner removes most distinctions between recordings. Instead, try
separate groups for temporal character, tonal movement and texture: for example
isolated/repeated/dense events, steady/rising/falling/wavering tones, and smooth/
rough/noisy sound. Keep the sentences acoustic; Livia's proposed design vocabulary
belongs in the following mapping layer.

A temporal choice could select plate spacing, tonal movement could select a
rising or falling sweep, and texture could select polished versus deeply worked
surfaces. Do not force an applicable label in every group: small score margins
should remain visible and can trigger a simpler instruction. Several similar
sentences may rank unstably. Score-derived blends would be artistic heuristics,
not measured proportions of acoustic properties.

**First test:** two photographs, six recordings, three small candidate groups.
Compare the richer instructions with the existing three-way mapping under the
same seed. A useful result is more variety that can still be explained by the
scores; a longer prompt alone is not success. **Not implemented yet.**

## 2. A piece substantially reimagined

**Pipeline:** actual jewelry photograph + recording → CLAP-selected substantial
silver transformation → FLUX reference-image editing.

This is the implemented `art jewelry` experiment. Terraces respond to the
click description; a continuous crest responds to the whistle description;
opening petals respond to the wavering description. The mapping asks the metal
to open outward and substantially change the silhouette. RMS no longer limits
these edits to subtle wording.

**Next test:** keep the same three recordings and compare two degrees of design
freedom, with two seeds per condition. Inspect the exposed stone, its inclusions,
the band and the setting's support as well as the silhouette. Stronger wording
is not a calibrated deformation strength. If faithful stone preservation is
required, test a real segmentation/compositing or geometry workflow; do not
assume this pipeline offers a hard mask or exact preservation.

Save the original alongside every comparison. The no-sound redesign distinguishes
the effect of the chosen operation from the model's general tendency to redesign
a ring. **Implemented baseline, proposed refinement.**

## 3. Sound chooses from Livia's own material library

**Pipeline:** recording → CLAP similarity to descriptions attached to Livia's
reference photographs → retrieved references → FLUX redesign.

Build a small library of whole pieces and details: a Mitoring fold, an exposed
opal, a Nanot joint, an Ammonite curve, a walnut/metal transition. Attach short
acoustic analogies chosen for the experiment to each reference. CLAP compares
audio with those descriptions; it does not inspect the photographs on this
route. The selected photographs then become consequential image-model inputs.

**First test:** 12–20 references, three recordings, top-three matches shown
before generation. Compare sound-selected references with randomly assigned
ones. A useful library should reveal relationships within Livia's work rather
than repeatedly selecting a generic ocean image.

Direct audio/image retrieval with ImageBind remains an optional alternative.
It adds another environment and a different learned correspondence; our
[model audit](models.md) records its setup. It is not needed for the tagged
library's first test. **Proposed.**

## 4. A whistle leaves a silver gesture

**Pipeline:** an existing F0 annotation with time coordinates → artist-defined
2D guide or geometric surface → rendered jewelry concept.

Let a rising contour lift a silver shoulder, a wavering contour shape the edge
of a broad petal, or a phrase leave a groove across a plate. Treat gaps as gaps
rather than bridging them with enclosing bars. The stone remains an exposed
reference anchor. This explores a surface or gesture instead of adding another
cage around the object.

Use the actual annotated pitch track when available. Spectral centroid measures
frequency-energy distribution and must not be presented as whistle pitch. An
encoder trajectory also has different provenance from an F0 annotation.

**First test:** three annotated contours, each mapped into a line engraving and
an outward fold. Show the source curve, clean guide and resulting object. Start
with deterministic SVG/surface previews; try a guide image as an additional
FLUX reference afterward. Whether it follows that guide closely is a test, not
a guaranteed ControlNet-style constraint. Parametric CAD is a separate route
when exact shape control matters. **Contour baseline exists; object mapping proposed.**

## 5. Jewelry answers the recording

**Pipeline:** recording's event times or amplitude envelope + material sound
samples/impulse responses → a constructed acoustic response.

Use taps on silver, rubbing glass or wooden resonance as a proposed sonic
counterpart to a piece. With actual material recordings, onset-triggered
resynthesis can retain event timing; convolution can give an existing signal a
recorded resonance. Without samples, a declared synthetic resonator is a useful
first baseline. It should not be presented as the measured sound of a jewel.

**First test:** three marine clips, one fixed material palette, three separate
response tracks. Present a timing-preserving version before adding a free
text-to-audio interpretation. The listener should be able to compare the
original and response, and identify which timing survived. A later generative
sound model needs a current inference check; the former AudioLDM2 suggestion
is not automatically the best next dependency. **Proposed.**

## 6. A call becomes a written score

**Pipeline:** verified annotations or proposed onset detections → intervals and
event groups → an artist-chosen instrumental score → rendered sound.

Repeated events can become percussive strikes with their original spacing;
pauses can remain silence. Livia chooses the timbre and whether the score is an
answer or an accompaniment. Save the detected events and allow inspection:
noise can also trigger an onset detector, and detection is not call annotation.

**First test:** one click-rich recording, its event timeline, one rhythm-preserving
score and a deliberately regularized score for comparison. This gives a concrete
contrast between source rhythm and composition. MusicGen or another music
model can later provide a freer response after its current loader is checked;
a text prompt alone does not impose the original intervals. **Proposed.**

## 7. A whistle becomes an audible melody

**Pipeline:** annotated F0/time → explicit register mapping → sine/instrument
guide, optionally followed by generated accompaniment.

Translate frequency into a declared musical register while retaining annotation
times and gaps. Show the mapping and octave changes rather than calling the
result an unmodified whistle. A playable guide and drawn score already form an
artifact; a music generator is optional.

**First test:** three contours, each with its original clip and two different
register mappings. Listen before selecting a melody-conditioned generator.
The earlier MusicGen-melody route is a comparison candidate, not a default:
its chroma conditioning may discard octave information or other guide details.
These are musical compositions, not translations of animal intention.
[Melody/chroma interface](https://huggingface.co/docs/transformers/en/model_doc/musicgen_melody)
**Proposed.**

## 8. A visitor changes the correspondence

**Pipeline:** visitor-selected jewelry photograph + sound + a word or gesture
→ an explicit editable correspondence → FLUX result.

A word such as “unfurl,” “erode,” or “step” can modify the sound-selected
operation. Keep separate controls for the sound, the visitor's instruction and
the amount of artistic freedom. Expose those choices in the gallery so a word
does not silently dominate the recording. The current model does not accept a
mixture of arbitrary audio/image/text embeddings as its editing input.

**First test:** one photo, three sounds and three words, then the same word with
sound disabled. Cache the nine combinations for a responsive installation.
Use buttons for real audio playback; source audio belongs with the inputs.
**Proposed.**

## 9. Two representations disagree

**Pipeline:** the same recording → two representations → the same artist-defined
vocabulary and visual generator → an explained diptych.

A useful first pair is CLAP's candidate description and a transparent acoustic
rule based on measured events or an annotated contour. This asks whether semantic
ranking loses a structure that remains visible in the source. A later encoder
comparison could use BioLingual or dolphin-oriented features after the loader
is verified. A feature encoder need not provide text similarity scores.

**First test:** three clips where the two methods choose different operations,
plus one agreement case. Hold the photograph, seed and instruction templates
fixed. Explain both choices, and compare within-model ranks rather than treating
raw scores from unrelated models as calibrated alike. **Proposed.**

## 10. Real and imagined whale phrases

**Two separate routes:** sperm-whale coda prompt → WhAM pseudocoda variation;
or compatible humpback codec-token prompt → DoLittle continuation.

The species and generation task matter. WhAM is the sperm-whale candidate;
DoLittle continues humpback material. Its current unified script documents
`--prompt-seconds` and `--max-new-seconds`, as well as token-count controls.
Neither generator has been run in our art pipeline. Test those duration controls
with the chosen checkpoint and codec before promising arbitrary output lengths;
a seconds option does not establish unlimited continuation. Looping or concatenating real
clips must not masquerade as a newly recorded long phrase.

**First test:** one real prompt and one synthetic response, with the boundary
clearly marked. Use the same jewelry reference and visual mapping for both.
Then compare sequences or durations supported by that generator; a storyboard
comes before a film. Longer sound is useful only if the visual bridge retains
its temporal development.

WhAM's published setup needs separate dependency work, and its weight terms
differ from its code terms. DoLittle needs compatible codec tokens and decoding.
See the [audited setup and terms](models.md#checkpoints-runtime-and-licenses),
[WhAM release](https://github.com/Project-CETI/wham) and
[DoLittle generation code](https://github.com/cairninstitute/cairn_marine_mammals_communication).
**Proposed; separate setup required.**

## 11. A recording unfolds through one piece

**Pipeline:** whole 30–40-second recording → declared overlapping analysis
windows → evolving CLAP choices and/or measured features → reference-anchored
jewelry states.

Start with the 30.8/36-second real recordings already downloaded. Use explicit
windows no longer than CLAP's current ten-second input, save start/end times,
and show the scores at each position. Shorter windows are a proposed artistic
timescale whose stability needs testing. Do not let repeat-padding imply that
a short event is a continuous ten-second phrase.

Let the metal expand, fold, unfurl or soften across the sequence. Use a common
reference range for numerical features. Duration determines how much of the
score we see, not automatically how many bars enclose a stone. Frames should
initially refer back to the original photo; test chained edits separately
because their errors may accumulate.

**First test:** six timestamped stills from each of two recordings, synchronized
with playback and a cursor over the control timeline. Compare against six
states driven by one constant instruction. This is a storyboard or slideshow;
independent diffusion edits do not establish coherent video. **Proposed; next visual experiment.**

## 12. Jewelry becomes an inhabited sound space

**Pipeline:** jewelry reference + Livistone scene + recording → a chosen spatial
operation → architectural concept or controlled room geometry.

Carry a specific setting gesture into a space: a silver crest can become a
roof opening, Mycelium's drainage can become a rain channel, or terraces can
organize a route. Sound might select that operation or unfold its arrangement
in time. Identify the source piece and the spatial function; a larger decorative
ring is not yet an inhabitable design.

**First test:** three sound-selected versions of one piece, each paired with a
small pavilion concept. Use the same scale cues, camera and Livistone reference.
Show a human-sized entrance, walkable ground and the material connection. A
second test can make the room acoustically answer its source via idea 5.
Rendered architectural images and direct CAD models are different outputs.
**Jewelry/pavilion baseline exists; these operations are proposed refinements.**

## What to explore next

1. **A recording unfolds through one piece (11):** use longer data we already
   have, and make time consequential without returning to rib cages.
2. **A whistle leaves a silver gesture (4):** use an actual contour to explore
   engraving, edges and folds; inspect the mapping before generative rendering.
3. **Jewelry answers the recording (5):** make an audible artifact whose source
   timing survives, then compare it with a freer generated response.

The richer vocabulary in idea 1 is a small parallel extension of our current
stack. It should earn its complexity through more useful, explainable outcomes.
The source-library and Livistone directions are worthwhile when selecting pieces
or changing scale becomes the main artistic question.

## A useful comparison for every new idea

Each first artifact should show **input → schema → output**, with the source
photo, playable recording, time range, actual measurements or scores, chosen
mapping and generated result. Preserve raw audio and put listening gain or
speed changes in separately labeled playback copies/modes. Audibility changes
must not silently change the evidence given to the encoder.

Compare different sounds with the same photo and seed, and compare the sound
mapping against a no-sound or constant-control condition. Add another seed when
assessing consistency, and shuffle mappings where that comparison is meaningful.
Check whether source shape, materials and the sound relationship survive; clear
visual difference alone does not demonstrate acoustic fidelity.

Save model revisions, exact prompts, reference hashes and time coordinates under
the existing [data layout](../data/README.md). Raw RMS includes recording gain
and distance; spectral centroid is not F0; CLAP scores compare supplied sentences.
These distinctions belong in the explanation of the artifact, not as hidden
implementation assumptions.
