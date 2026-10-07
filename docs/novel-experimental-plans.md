# Eight new science-and-art proposals: experimental plans

Prepared **7 October 2026**. This report gives every proposal the same eight
parts: scientific question, artistic proposition, closest precedents, potential
contribution, enabling advance, data and implementation, minimal experiment and
first artifact. Read it with:

- [Overview, ranking and the recommended pilot](novel-projects.md)
- [Prior art, with pictures and videos](novel-prior-art.md)
- [Novelty assessment and search log](novel-novelty-assessment.md)
- [Hardata II pilot: method and results](hardata-ii-pilot.md)
- [DCLDE label audit behind P3–P5](dclde-opportunities.md)

Each proposal keeps three kinds of statement apart, marked where they meet:
**acoustic pattern** (what is measured in the signal), **biological
interpretation** (what published evidence says the signal does) and **artistic
correspondence** (a mapping we choose). A correspondence is never offered as a
decoded meaning.

Readiness codes used throughout: **local** = already on this machine;
**public** = downloadable without agreement; **partner** = needs a researcher or
an access agreement.

---

## P1 Hardata II: a silver inscription that keeps the whistle

**Scientific question.** How many inscribed bits does a dolphin whistle need,
and in which representation, before a dolphin-trained encoder can no longer
tell its type? Playback studies show that bottlenose dolphins recognise identity
from the frequency contour of a signature whistle with voice features removed
([Janik et al. 2006](https://doi.org/10.1073/pnas.0509918103)). If the 2026
OpenWhistle encoder represents type the same way, a few hundred bits of contour
should retain most of the type information that thousands of codec bits do not.

*Falsifiable predictions* (written into the code before the first run):

1. A 32-point, 8-bit contour (272 bits) keeps at least 70% of original-audio macro-F1.
2. Near 0.5 kbit, contour beats spectrogram relief and a 1-codebook DAC codec.
3. The 2021 Hardata rule, amplitude only, stays within 10 points of chance.
4. Time-reversed contours and flat tones lose most of the contour's advantage.
5. A simulated cast groove keeps 90% of the digital contour's score at 0.1 mm blur.

What we could learn: which acoustic properties a species-trained model relies on
for a biologically meaningful category, and what the material resolution of cast
silver permits. Either outcome is informative. If contour fails, the encoder is
using something other than shape, which matters for anyone reading its
embeddings as identity.

**Artistic proposition.** Livia's *Hardata* (2021, first prize at Hyper Form,
Timișoara) engraved a sound-amplitude pattern on a cylinder and noted that it
"has, for the moment, no way of being played". Hardata II is a ring band or
pendant cylinder whose groove *is* the whistle: time runs around the band,
log frequency across it. A phone camera or macro scan reads the groove back into
sound. One band per whistle type turns the five signature types and one shared
non-signature type into a set, close to Livia's *Paths. Memories. Guides*
(2022), where "memories record what lies inside us … a sound wave". Amberear's
listening ears and the *Sound of Stars* bells (2025) are the related pieces that
already make sound part of a setting. The groove changes depth and width, not
just decoration: it must survive printing, casting and polishing.
[Hardata on Livia's site](https://liviazaharia.com/art-design/hardata-timi-oara-2021).

**Closest precedents.** Voyager's Golden Record (whale song in a playable
object), National Geographic's 1979 humpback flexi-disc, Ghassaei's 3D-printed
records, IRENE optical playback and First Sounds, commercial "soundwave" tattoos
that only link to cloud audio, Miyaguchi et al.'s codec test on bird species.
See [prior art for P1](novel-prior-art.md#p1-hardata-ii-a-silver-inscription-that-keeps-the-whistle).

**Potential contribution.** A rate–distortion curve for a biological category,
measured with a species-trained model and coupled to a fabrication constraint.
The object carries the sound itself rather than a link. Novelty status:
[verified within a scoped search](novel-novelty-assessment.md#p1-hardata-ii-a-silver-inscription-that-keeps-the-whistle);
whale song has been put into playable objects before, so the claim is about
identity-preserving minimal inscription, not about playability.

**Enabling advance.** OpenWhistle (2026): 8,354 expert-labelled whistles with
~5 ms F0 tracks, confidence values and session-disjoint splits, plus a
dolphin-trained Wav2Vec2 encoder (weights May 2026; paper September 2026)
reporting 81.1% linear-probe accuracy on the balanced task. Earlier whistle
corpora rarely published F0 tracks and labels together under open access.
The DAC codec is the tokenizer family behind the 2026 DoLittle whale model, so
the codec arm asks how much of a whistle survives that tokenization.

**Data and implementation.** Local and implemented:
`experiments/inscription.py`, run with
`uv run --group art main.py inscription fetch` and `… inscription run`.
Inputs: OpenWhistle `balanced` parquet at a pinned revision (1.2 GB:
2,100/450/450 whistles, 44.1 kHz). Models: OpenWhistle Wav2Vec2 (cached),
CLAP as a general-audio comparison, `descript/dac_44khz`. Compute: one 16 GB GPU,
27 minutes for the full run, most of it Griffin-Lim; `… inscription matched`
adds an exploratory probe trained on decoded audio. Missing: no physical casting
or scanning yet.

**Minimal experiment.** Linear probe trained on original training whistles,
layer and regularisation chosen on validation originals only, then applied to
decoded test whistles under 20 encodings and 6 simulated casting blurs.
Baselines: original audio (ceiling), chance (floor), amplitude-only (Hardata
2021). Controls: reversed contour and flat tone (shape versus range), a shared
sea-noise bed (domain shift without per-whistle bits), CLAP probe (is the effect
specific to the dolphin encoder?). Paired bootstrap on identical clips.
**Success:** predictions 1, 3, 4 and 5 hold. **Failure that teaches:** if the
contour fails while relief succeeds, the encoder uses texture or harmonics, and
the artwork must inscribe more than a line. Results:
[pilot report](hardata-ii-pilot.md).

**First artifact.** Done in silico: a playable gallery
(`data/output/inscription/index.html`) with each whistle, its decoded versions,
the probe's answers, an unrolled band heightmap and an STL ring band per type.
All five predictions held: a 272-bit contour kept 0.62 of 0.82 macro-F1;
reversed and flat controls fell to 0.23–0.26; amplitude-only to 0.10.
Next: cast three bands, scan them, decode, and listen.

---

## P2 Expectation in humpback song

**Scientific question.** Does the 2026 DoLittle humpback model expect song
structure, or only local texture? Humpback song is hierarchically repetitive:
units form phrases repeated into themes
([Arnon et al. 2025](https://doi.org/10.1126/science.adq7055)). A model that has
learned song should become less surprised by the second occurrence of a phrase
inside its context window.

*Falsifiable predictions:*

1. Mean per-token surprisal over a repeated phrase is lower on its second
   occurrence than on its first, by more than when the first occurrence is
   replaced with a phrase from another recording (context-swap control).
2. Surprisal peaks align with phrase boundaries better than energy change
   points do, measured against boundaries found by self-similarity of the
   recording or by a listener's annotation.
3. Listeners shown 10 s of song predict which of three continuations is real
   (real, DoLittle, shuffled real) above chance; the model's own likelihood
   ranks them better or worse than people do.

What we could learn: whether the 2026 generator's long context (up to 169 s)
captures song-level repetition, which would make its continuations musically
meaningful rather than texture, and how human listening compares, the question
Livia's GlucoseDAO study asks about glucose forecasting.

**Artistic proposition.** *Sugar-Sugar for songs.* Livia founded GlucoseDAO and
its Sugar-Sugar game, where people predict glucose curves and are scored against
ML models ([sugar-sugar.study](https://sugar-sugar.study/)). The same design
becomes an installation kiosk: listen to a humpback phrase, choose the real
continuation, see how you compare with the model and with other visitors. The
material counterpart is a *surprise ribbon*: a folded silver band where fold
depth follows the model's surprisal across a phrase, so repetitions flatten into
calm folds and novelty rises into crests, a direct relative of Mitoring's
cristae folds. In Livistone, the Glucose Commons could host the game.

**Closest precedents.** Arnon et al. 2025 and its birdsong replication
(Kirby et al. 2026), Youngblood 2025, Zeh et al. 2026 (song locked to dives),
WhAM's expert listening test, DoLittle's own perplexity-only evaluation,
Whale FM, Pattern Radio, Bird Song Hero, Which Face Is Real, Sugar-Sugar.
[Prior art for P2](novel-prior-art.md#p2-expectation-in-humpback-song).

**Potential contribution.** The first per-token surprisal analysis of a public
humpback language model against song repetition, and a human-versus-model
prediction benchmark for cetacean sequences. Sperm-whale cross-whale prediction
is excluded: Assayag et al. (2026) already report it.
[Novelty assessment](novel-novelty-assessment.md#p2-expectation-in-humpback-song).

**Enabling advance.** DoLittle (CAIRN Institute; weights 24 July 2026):
10k/32k/128k-token contexts (13/42/169 s) over DAC tokens of SanctSound Hawaii
humpback song, plus the 488,320-array token corpus. Before 2026 no public humpback model offered likelihoods over
minutes of song.

**Data and implementation.** Public. Start with shard `00028` of
`cairninstitute/mmc-sanctsound-humpback-dac9` (55 MB, 625 chunks of ~25–28 s)
and the 10k or 32k checkpoint (1.5–1.9 GB). The repository has no scoring
script; calling the model without targets returns logits, so a small wrapper
computes per-token surprisal (chunk at long contexts). Decode tokens with DAC to
listen. Gaps: the repository's `src/data` is missing (training and loader
evaluation fail; generation works); audio was band-passed to 80 Hz–4 kHz; no
unit or phrase labels exist for these tokens. Compute: one GPU, minutes per
chunk at 10k context. Human study: consent and an anonymous design; GlucoseDAO's
ethics experience is relevant but does not cover this study.

**Minimal experiment.** 20 chunks with clear repetition (found by DAC-frame
self-similarity, then confirmed by listening). Compare surprisal on first and
second phrase occurrences; control by swapping the first occurrence with an
unrelated phrase and by shuffling phrase order. Baselines: unigram token
frequency, and a model given only the last 2 s. **Success:** a context effect
larger than the swap control in most chunks. **Failure:** no repetition effect,
meaning DoLittle continuations should be presented as texture, not song.
Pilot listening game: 12 volunteers, 20 trials, three-alternative choice.

**First artifact.** A web page with surprisal ribbons under spectrograms and
playable phrases, and a three-choice listening game that logs anonymous answers.

---

## P3 Population voices without recorder fingerprints

**Scientific question.** When Southern Resident and Bigg's killer whales are
recorded by the same hydrophone, do frozen 2026 encoders still separate them,
and is the recorder more decodable than the population? The audit found that
provider annotation conventions alone separate the populations in pooled data:
SIO and SIMRES use zero-bandwidth boxes, and SIO supplies 54% of call-level TKW
labels ([DCLDE audit](dclde-opportunities.md)).

*Falsifiable predictions:*

1. Within the same dataset, leave-one-day-out SRKW/TKW accuracy is significantly
   lower than pooled random-split accuracy.
2. A probe predicts provider from the same embeddings more accurately than it
   predicts population across providers.
3. Separation within a site shrinks when the probe sees one call type per
   population at a time (DORI S-calls), showing that much of the signal is
   repertoire, which is itself biological: resident pods share discrete call
   repertoires ([Ford 1991](https://doi.org/10.1139/z91-206)).

What we could learn: how much DC-2 performance reflects population, repertoire,
site or annotation practice; which encoder generalises.

**Artistic proposition.** *A lattice of voices.* Nanot of Power's open silver
lattice becomes a graph: each node a call, each strut a nearest-neighbour link.
The same calls form two lattices, one grown by population and one by recorder,
cast as a pair of pendants or shown as a switchable 3D form in Livistone's
Ministry of Science (the hall already built inside Nanot). Where the lattices
agree, the voice is population; where they diverge, it is the instrument. The
work makes a methodological trap visible and audible.

**Closest precedents.** Palmer et al. 2025 (dataset) and 2026 (degradation on a
new hydrophone system; call-type balancing), Ruiz et al. 2026 (file-grouped
splits), Perch 2.0's whale transfer (no site holdout), DORI (33.6% ecotype
accuracy on held-out data), Ford 1991, Deecke et al. 2005.
[Prior art for P3](novel-prior-art.md#p3-population-voices-without-recorder-fingerprints).

**Potential contribution.** Partly anticipated. Cross-site degradation is known.
New: the box-convention confound, a site- and day-controlled test with frozen
2026 encoders, and an explicit provider-decoding baseline.
[Novelty assessment](novel-novelty-assessment.md#p3-population-voices-without-recorder-fingerprints).

**Enabling advance.** DCLDE 2027's public orca release (2025 descriptor; CSV
updated March 2026); SPARROW detector/ecotype ONNX models (August 2026, local);
Perch 2.0 (2025) with published DCLDE probes; DORI's call-type labels (2026).

**Data and implementation.** Annotations local; audio public but not
downloaded. Needed: about 100 provider files from JASCO_VFPA_ONC
StraitofGeorgia (22 SRKW + 9 TKW files), ONC BarkleyCanyon (23 + 25) and SIO
Cpe_Elz (5 + 41); file sizes still to be listed. Windows: fixed 3 s windows at
call start, never box crops. Encoders: SPARROW ecotype (local ONNX), Perch 2.0
CPU (separate TensorFlow environment), AVES-bio, OpenWhistle as an
out-of-domain control. Compute: CPU-feasible.

**Minimal experiment.** Per site: leave-one-day-out logistic probes for
population; across sites: leave-one-provider-out; provider probe on the same
embeddings. Controls: shuffled population labels within day; time-of-day and
SNR matched subsets. **Success:** within-site separation above chance with
confidence intervals over days, and a quantified gap to pooled accuracy.
**Failure:** within-site separation at chance would mean pooled results mostly
measure recording conditions.

**First artifact.** An interactive two-state lattice (population ↔ recorder)
with playable calls at each node, then a pair of printed resin lattices.

---

## P4 Moveout: fin-whale calls drawn by a fibre

**Scientific question.** How much of a fin whale's position does one cable's
arrival-time curve constrain, and what does a second cable add? A call recorded
along a straight fibre arrives first at the nearest point and later elsewhere,
tracing a moveout curve. Its apex gives the along-cable position; its curvature
gives range; one straight cable cannot tell left from right.

*Falsifiable predictions:*

1. A constant-speed moveout fit to single-cable picks recovers the authors'
   along-cable position within their reported spread for batch-1 calls.
2. Range estimates from one cable are biased and widely spread compared with
   two-cable localizations of the same calls.
3. Distinct apex clusters over the 18 h indicate at least two concurrently
   calling whales; verifiable only where the authors' associations exist.

What we could learn: a transparent account of DAS localization geometry, and a
first step towards counting simultaneously calling whales, the cue-counting
building block of acoustic density estimation. No DAS-based fin-whale density
paper was found.

**Artistic proposition.** *Fibre necklace.* Each call's moveout is a
hyperbola-like curve; scaled down, it becomes a silver chain whose lowest point
marks the whale's nearest approach. Two cables give two necklaces worn together;
their intersection is where the whale could be. At Livistone's Vittoria Lake,
silver walkways already cross water: one could become the cable, with each call
arriving at the visitor's position along the walkway at the true relative delay,
transposed upwards so the 20 Hz pulse is audible. Livia's *Inline* ring and
woven pieces are the formal precedents.

**Closest precedents.** Goestchel et al. 2026; Horne et al. 2025 (two-hour
fin-whale track); DAS4Whales; spatial listening works by Jana Winderen,
Yolande Harris and Marshmallow Laser Feast.
[Prior art for P4](novel-prior-art.md#p4-moveout-fin-whale-calls-drawn-by-a-fibre).

**Potential contribution.** Scientifically modest: a reproducible teaching
analysis. The artwork, a wearable and walkable DAS geometry, was not found.
[Novelty assessment](novel-novelty-assessment.md#p4-moveout-fin-whale-calls-drawn-by-a-fibre).

**Enabling advance.** DCLDE 2027's DAS release (arrival picks for 794 calls on
two OOI cables) and the JASA 2026 association/localization code with a
published batch-1 localization table.

**Data and implementation.** Local: 120 pick CSVs, cable geometry (lat/lon/
depth per channel), 176 research localizations. Missing: raw strain (OOI RAPID),
the official scoring reference, units of `deltax`, and a validated sound-speed
model. Compute: laptop.

**Minimal experiment.** Fit t(x) = t₀ + √((x − x₀)² + r²)/c per call
(c ≈ 1,480 m/s fixed, then free); compare x₀ and r with the batch-1
localizations projected onto each cable. Baseline: apex = earliest pick.
Control: fits on picks with distances shuffled. **Success:** apex error well
below the median 16 km pick span; clear one-cable range ambiguity shown.
**Failure:** large disagreement would point to coordinate or association
mismatches that must be resolved before any visual claim.

**First artifact.** An interactive map of both cables with each call's moveout
drawn as a curve and its sound placed in time; STL of one necklace.

---

## P5 Calls against counts: a right-whale census hourglass

**Scientific question.** Is the ratio of detected right-whale calls to whales
counted from the air stable through the season? Garcia & Tolkova (2025)
calibrated acoustic cue counts against aerial surveys. If calls per whale change
from February to May, a single calibration misstates trends.

*Falsifiable prediction:* calls per counted whale per survey hour differ by more
than a factor of two between February–March and April–May flights, beyond
bootstrap uncertainty, after cross-channel de-duplication and a fixed detector
score threshold. With 21 flights the interval will be wide; a null result is
also reportable.

What we could learn: whether calibration needs seasonal terms, and how much
detector thresholds alone move the ratio.

**Artistic proposition.** *Census hourglass.* Livistone's Timeface Tower is
already a spiral gallery around a silver hourglass. Here, the upper chamber
holds calls (one grain per de-duplicated detection), the lower chamber holds the
whales seen from the air that day; 21 hourglasses for 21 flights, with the
grain size fixed. The visible mismatch between chambers is the calling rate:
the quantity abundance estimation cannot see directly.

**Closest precedents.** Garcia, Tolkova et al. 2025; Marques et al. 2013 on
cue-based density; acoustic spatial capture-recapture with machine-learning
false positives (Wang et al.); Ryan et al. 2025 (song tracks foraging).
[Prior art for P5](novel-prior-art.md#p5-calls-against-counts-a-right-whale-census-hourglass).

**Potential contribution.** Partly anticipated: the calibration exists; the
seasonal stability test on the public challenge subset and the hourglass do not
appear in the sources reviewed.
[Novelty assessment](novel-novelty-assessment.md#p5-calls-against-counts-a-right-whale-census-hourglass).

**Enabling advance.** The 2026 DCLDE DE release made the daily detection tables,
aerial survey and five-channel audio public together.

**Data and implementation.** Local: aerial CSV. Public: 118 daily selection
tables (336 MB) and, for spot checks, the 2 kHz FLAC audio (57 GB in total;
download only survey days). Missing: calling rate, detectability, per-whale
aerial positions (agreement with the Center for Coastal Studies). Compute: laptop.

**Minimal experiment.** For each flight window: count detections above three
score thresholds; merge detections within the inter-sensor travel time across
channels; divide by aerial count and hours. Control: shuffled flight dates; a
night/day split to separate diel from seasonal effects. **Success:** a seasonal
difference whose interval excludes one. **Failure:** a stable ratio supports the
published calibration for this season.

**First artifact.** An animated or printed set of 21 hourglasses with each
day's calls playable as a time-compressed audio "pour".

---

## P6 What an echo sees of a jewel

**Scientific question.** At dolphin echolocation frequencies, which parts of
Livia's pieces would an echo reveal? Wavelengths in seawater are about 5 cm at
30 kHz and 1 cm at 150 kHz, comparable to a ring, so these objects scatter in the
resonance regime where echo structure depends on shape and material.

*Falsifiable predictions:*

1. Sub-wavelength lattice cells (Nanot) are not resolved: a solid shell with the
   same envelope produces an echo spectrum within a few dB of the lattice below
   ~80 kHz, diverging only near the top of the click band.
2. In Mitoring, the silver setting dominates the echo and the amber contributes
   much less. This inverts the human view, where the stone is the centre. The
   prediction depends on amber's acoustic impedance, which must be measured or
   sourced, not assumed.
3. A simple classifier identifies pieces from simulated echoes across
   orientations held out in training better than from the human-visible
   silhouette alone.

What we could learn: how echo information relates to form at jewellery scale,
with predictions that a tank measurement can test. Dolphins discriminate
material and wall thickness from echoes
([Au & Turl 1991](https://doi.org/10.1121/1.400930);
[DeLong et al. 2007](https://doi.org/10.1121/1.2400848)).

**Artistic proposition.** *Sonar portraits.* For each piece, an auralised echo:
a dolphin-like click reflected by the actual mesh, slowed and transposed into
human hearing, presented beside the photograph. Visitors click a button
(or a hand clicker) and hear what Mitoring, Nanot and Mycelium return. A second
work engraves each echo's highlight structure back onto the piece's own band, so
the object carries a record of how it sounds to a different sense.

**Closest precedents.** Au's target-echo studies, DeLong et al. 2007 (people
listening to echoes), Harley et al. 2003, Wei et al. 2021 (FEM click–object
simulation), Christman et al. 2025, SpeakDolphin's contested 3D prints, BEML-sonar
2026. [Prior art for P6](novel-prior-art.md#p6-what-an-echo-sees-of-a-jewel).

**Potential contribution.** Applied physics with an artistic outcome. No echo
simulation of jewellery was found; the biological claims stay within what
echolocation studies support.
[Novelty assessment](novel-novelty-assessment.md#p6-what-an-echo-sees-of-a-jewel).

**Enabling advance.** Livia's STL archive analysed in October 2026 (695 files,
93 works; Mitoring 0.98 M and Nanot 2.25 M triangles local), maintained BEM
solvers (bempp-cl; JAX-BEM, April 2026, differentiable on GPU).

**Data and implementation.** Local meshes in the Livistone checkout (never
committed; ask before publishing derived geometry). Decimate to element size
below λ/6 (≈1.7 mm at 150 kHz). Rigid and fluid-filled models first; elastic
coupling later (Hickling 1962 shows it matters). Missing: amber and silver
material parameters at ultrasonic frequencies from a citable source; a
water tank, transducer and hydrophone for validation. Compute: hours per piece
on GPU at the top frequencies.

**Minimal experiment.** Rigid-sphere and cylinder benchmarks against analytic
solutions; then Nanot versus its convex hull, and Mitoring with and without
amber, over 36 orientations and 30–150 kHz. **Success:** benchmarks within 1 dB;
predictions 1–2 tested with error bars from mesh refinement. **Failure:**
benchmark mismatch stops interpretation.

**First artifact.** A listening page with three pieces, their echoes at two
orientations, and echo spectrograms, labelled as simulation.

---

## P7 A whistle alphabet from sparse features

**Scientific question.** Do sparse features learned from a dolphin-trained
encoder correspond to contour primitives (upsweep, downsweep, inflection, loop,
harmonic presence) more than to recording conditions (hydrophone, year, SNR)?
And more so than features learned the same way from a general audio encoder?

*Falsifiable predictions:*

1. Among the 200 most active features of a sparse autoencoder on OpenWhistle
   layer activations, more are explained by contour descriptors (R² > 0.5) than
   by nuisance variables.
2. The same procedure on CLAP yields a lower fraction.
3. Feature activations change predictably under controlled edits of synthetic
   contours (reverse, transpose, stretch).

What we could learn: whether 2026 species-trained representations contain
human-interpretable acoustic units, the step between embeddings that classify
and units that can be inspected. Dolph2Vec found partial codebook specialisation;
no sparse-autoencoder study of a bioacoustic encoder was found.

**Artistic proposition.** *A cast alphabet.* Each validated feature becomes a
small cast module, its shape drawn from the mean contour of the whistles that
activate it most, with those whistles playable beside it. Livia's practice
already works in repeated modules with controlled variation (Blooming pins,
Nanot cells). A recording becomes a necklace: modules strung in the order the
features fire. The alphabet is explicitly an acoustic one; it does not claim
words.

**Closest precedents.** Dolph2Vec codebooks, AudioSAE (speech), SAE studies on
audio codecs, ESP's probing of bioacoustic embeddings, AudioProtoPNet (birds),
ARTwarp contour categorisation, Tessa Campbell Fraser's eidographs.
[Prior art for P7](novel-prior-art.md#p7-a-whistle-alphabet-from-sparse-features).

**Potential contribution.** First sparse-autoencoder analysis of a
species-trained bioacoustic encoder, within the scoped search.
[Novelty assessment](novel-novelty-assessment.md#p7-a-whistle-alphabet-from-sparse-features).

**Enabling advance.** OpenWhistle's 114 h of unlabelled audio plus labelled F0
tracks and session splits (2026); the OpenWhistle encoder; 2025–2026 SAE
training practice for audio models.

**Data and implementation.** Local: encoder, classification whistles and F0.
Public: the pretraining `review-sample` (0.79 GB, 480 sequences, year and
hydrophone fields) and later the full 79 GB. Nuisance labels: hydrophone, year,
`snr_db` (`all` config). Model: TopK SAE on frame states of the layer the
Hardata pilot selected, 8× expansion. Compute: one GPU, about an hour for a
first SAE.

**Minimal experiment.** Train SAEs on OpenWhistle and CLAP frames; for each
feature, regress activation on contour descriptors and on nuisance variables
using session-held-out whistles. Control: SAE on a randomly initialised encoder.
**Success:** predictions 1–3. **Failure:** features dominated by hydrophone or
noise mean the alphabet would describe the recording rig, not the dolphins.

**First artifact.** An interactive feature atlas (module drawing, activation
plot, top whistles playable) and five printed modules.

---

## P8 A day ring: 24 hours of seven dolphins

**Scientific question.** In a continuous 24-hour recording, do whistle rate
and whistle-type mixture differ between scheduled contexts (training, play, fish
release, free activity, night) beyond time of day? And does an encoder trained on
the Eilat dolphins transfer to a different population?

*Falsifiable predictions:*

1. Whistle rate differs between contexts after controlling for hour, with
   effect sizes larger than between the two recording days.
2. A probe trained on Oltremare's per-vocalisation tags using OpenWhistle
   embeddings exceeds a CLAP probe under day-held-out evaluation.

What we could learn: how context and time structure vocal output in a small
captive group, and whether 2026 dolphin representations generalise across
populations. Context here means a scheduled activity, not an inferred intent.

**Artistic proposition.** *Day ring.* A band divided into one segment per
five-minute file: relief height follows whistle count; the segment's texture
marks the scheduled activity. Night is a smooth stretch, training a dense one. Livia's
Timeface pendant and its tower in Livistone already treat time as form; this ring
is one day of seven animals, worn as a diary. Two rings for two days invite
comparison.

**Closest precedents.** The Oltremare data paper (2025), DOLPHINFREE (per-minute
behaviour), Madeira (per-recording behaviour), Ryan et al. 2025 (long-term song),
data-to-wearable works including Livia's *Cry, Dance, Repeat*.
[Prior art for P8](novel-prior-art.md#p8-a-day-ring-24-hours-of-seven-dolphins).

**Potential contribution.** Likely partly anticipated by the dataset authors'
own analysis of activity and vocal counts; cross-population encoder transfer is
the newer element.
[Novelty assessment](novel-novelty-assessment.md#p8-a-day-ring-24-hours-of-seven-dolphins).

**Enabling advance.** The Oltremare dataset on SEANOE (13 October 2025): recordings from the park's 24-hour sessions on 20–21 November 2021, split
into five-minute files, with per-vocalisation tags and an activity schedule
(tags and sample rate reported by our dataset check, not yet opened locally);
OpenWhistle encoder.

**Data and implementation.** Public, about 19 GB zipped across day-part
archives; download one archive first and count files per day before fixing the
ring's segment count. Missing: individual caller identity (not recorded), verified whistle
counts (secondary sources only), behaviour beyond the schedule. Compute: CPU
for counts, GPU for embeddings. Captive-animal context: interpretation limited to
this facility.

**Minimal experiment.** Count tagged whistles per five-minute file; model with
context and hour terms; leave-one-day-out probe comparison. Control: permuted
context labels within day. **Success:** prediction 1 with intervals; transfer
result either way. **Failure:** no context effect beyond hour, which shapes the
ring as pure time rather than activity.

**First artifact.** A circular day plot with every five-minute segment playable,
then the ring as an STL.

---

## Shared implementation rules

All proposals reuse the repository conventions: `uv` dependency groups (add
separate environments for TensorFlow/Perch and any DoLittle dependencies),
`pathlib` paths anchored to the repository, Typer commands, and the data layout:

| Directory | Holds |
|---|---|
| `data/input/` | Downloaded sources with manifests and SHA-256 hashes |
| `data/interim/` | Embeddings, decoded tokens, fitted probes, heightmaps |
| `data/output/` | Playable galleries, figures, meshes, results JSON |
| `resources/audits/` | Small, committed audits such as the DCLDE label audit |

Every gallery follows **input → schema → output**: playable source with its
provenance; the mapping, bits, model revision and parameters; and the decoded
sound, image or mesh. Original recordings stay separately playable from any
transformation, and playback gain or speed changes are labelled as listening
aids. Generated outputs stay Git-ignored.
