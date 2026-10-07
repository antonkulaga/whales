# Novelty assessment

Checked **7 October 2026**. For each [proposal](novel-experimental-plans.md),
this report states the exact contribution claimed, the closest work found, and
how far the novelty has been verified. "Novel within the scoped search" means we
searched the sources and queries listed in the [search log](#search-log) and found
no prior instance; it is not proof that none exists. Precedents are detailed,
with pictures, in the [prior-art report](novel-prior-art.md).

| Proposal | Verdict | What remains new |
|---|---|---|
| [P1 Hardata II](#p1-hardata-ii-a-silver-inscription-that-keeps-the-whistle) | Novel within the scoped search; the pilot ran | Identity-preserving minimal inscription, scored by a species-trained encoder, coupled to casting resolution |
| [P2 Expectation in humpback song](#p2-expectation-in-humpback-song) | Novel within the scoped search | Per-token surprisal of a public humpback model against repetition; human-versus-model prediction |
| [P3 Population voices](#p3-population-voices-without-recorder-fingerprints) | Partly anticipated | Box-convention confound; site- and day-controlled test with 2026 encoders |
| [P4 Moveout](#p4-moveout-fin-whale-calls-drawn-by-a-fibre) | Science anticipated; artwork novel within search | Wearable and walkable DAS geometry |
| [P5 Census hourglass](#p5-calls-against-counts-a-right-whale-census-hourglass) | Partly anticipated | Seasonal stability of the calls-per-whale calibration on the public subset |
| [P6 Echo of a jewel](#p6-what-an-echo-sees-of-a-jewel) | Novel application; physics established | Echo simulation of actual jewellery meshes, tested predictions about lattices and amber |
| [P7 Whistle alphabet](#p7-a-whistle-alphabet-from-sparse-features) | Novel within the scoped search | Sparse-autoencoder features of a species-trained bioacoustic encoder |
| [P8 Day ring](#p8-a-day-ring-24-hours-of-seven-dolphins) | Likely partly anticipated | Cross-population transfer of the OpenWhistle encoder; the wearable day |

## Excluded or narrowed after checking

| Idea | Why it changed |
|---|---|
| Predicting one sperm whale's next coda from its partner's | Assayag et al. 2026, *Bioacoustics* ([DOI 10.1080/09524622.2026.2684665](https://doi.org/10.1080/09524622.2026.2684665)), WhaleLM and Sinha & Chavan 2026 already address cross-whale and context prediction. Dropped from P2 |
| "The first whale song stored in an object" | Voyager (1977) and National Geographic's 1979 humpback flexi-disc did this. P1 claims identity-preserving minimal inscription instead |
| Population classification failing across recorders as a new finding | Palmer et al. 2026 ([DOI 10.1111/mms.70126](https://doi.org/10.1111/mms.70126)) report degradation on a different hydrophone system. P3 narrows to the annotation-convention confound and controlled tests |
| Calibrating right-whale calls to aerial counts | Garcia, Tolkova et al. 2025 ([DOI 10.3354/esr01384](https://doi.org/10.3354/esr01384)) did this. P5 tests whether one calibration holds across the season |
| Any dependency on DolphinGemma | Its page still says "in development"; no weights were found. Not used |

---

## P1 Hardata II: a silver inscription that keeps the whistle

**Claimed contribution.** A rate–distortion measurement for a biological
category: bits per whistle against retention of signature-whistle type, scored
by a dolphin-trained encoder, for contour, spectrogram, amplitude and neural
codec inscriptions, and extended through a simulated casting channel into a
wearable object that stores the sound itself.

**Closest work and differences.**

| Closest | Difference |
|---|---|
| Janik et al. 2006 (identity in contour) | Tested dolphins with synthetic contours; P1 asks whether a 2026 encoder relies on the same property, and at what bit budget. P1 does not test dolphins |
| Miyaguchi et al. 2026 (codec collapses bird identification) | Birds, one codec, no fabrication channel; P1 compares four inscription families for dolphin whistle types |
| Voyager, NatGeo flexi-disc, Ghassaei | Full-bandwidth analog grooves needing fine resolution; P1 asks what minimal inscription survives casting at 0.3 mm |
| Soundwave Art, Skin Motion | Store a link, not audio |
| Livia's Hardata (2021) | Amplitude pattern with no decoder; P1 measures why that rule loses identity |

**Verification.** No artwork was found that encodes whale or dolphin sound to be
decoded from the object itself; no benchmark was found that measures cetacean
call-type retention under codec reconstruction. Both are scoped-search results.
The pilot's outcome is reported in [the pilot report](hardata-ii-pilot.md).

**Residual risk.** The encoder's judgement is not a dolphin's. Probe accuracy on
decoded audio could reflect encoder quirks; the CLAP comparison and controls only
partly address this. Dolphin perception needs a partnered playback study.

## P2 Expectation in humpback song

**Claimed contribution.** (a) Whether DoLittle's surprisal falls on repeated
phrases beyond a context-swap control; (b) whether surprisal peaks mark phrase
boundaries; (c) human listeners against the model in choosing real
continuations.

| Closest | Difference |
|---|---|
| Arnon et al. 2025; Kirby et al. 2026 | Transitional probabilities over human-labelled units; P2 uses a neural model's likelihood over unlabelled codec tokens |
| DoLittle blog | Reports only aggregate validation perplexity |
| WhAM listening test | Experts discriminate real from synthetic codas; P2 asks people and the model to *predict* continuations, with a model-likelihood baseline |
| Chambers et al. 2025 | Entropy of sequences, no neural model, no listener prediction |
| Sugar-Sugar | Same human-versus-model design for glucose; P2 transfers it to whale song |

**Verification.** No 2024–2026 humpback surprisal or language-model study and no
human-versus-model prediction study for cetacean sequences were found.

**Residual risk.** Codec tokens at ~11.6 ms per frame do not align with song
units; repetitions must be found by self-similarity and confirmed by ear. The
80 Hz–4 kHz band-pass of the token corpus removes some song energy.

## P3 Population voices without recorder fingerprints

**Claimed contribution.** Documenting that DCLDE provider box conventions
(SIO and SIMRES zero-bandwidth boxes; OrcaSound without bounds) are confounded
with population; testing SRKW/TKW separation within sites with day-held-out
probes on SPARROW, Perch 2.0 and AVES embeddings; and measuring provider
decodability.

| Closest | Difference |
|---|---|
| Palmer et al. 2026 | Out-of-distribution degradation and call-type balancing with BirdNET models; no annotation-convention audit in the abstract |
| Ruiz et al. 2026 | File-grouped splits, no provider holdout |
| Perch 2.0 whale transfer | Few-shot probes without site holdout |
| DORI | Low held-out ecotype accuracy; different label sources |

**Verification.** The confound numbers are reproduced by
[`dclde_opportunities.py`](../dclde_opportunities.py). Whether the challenge
organisers already handle the box conventions in their evaluation is unknown;
the challenge page states no metric.

**Residual risk.** Few days per population within each site; results may be
inconclusive. The artwork's value does not depend on a positive result.

## P4 Moveout: fin-whale calls drawn by a fibre

**Claimed contribution.** A transparent single- versus two-cable geometry
analysis from public picks, and the first wearable and walkable rendering of DAS
whale arrivals found in our search.

**Verification.** Goestchel et al. 2026 and Horne et al. 2025 already localize
and track fin whales on these cables, so the analysis is a reproduction. No DAS
whale artwork or OOI cetacean sonification was found. No DAS-based fin-whale
density paper was found, which leaves cue counting open but beyond a pilot.

## P5 Calls against counts: a right-whale census hourglass

**Claimed contribution.** A seasonal stability test of the calls-per-counted-whale
ratio on the public DCLDE subset, with explicit detector-threshold and
de-duplication sensitivity; the census hourglass.

**Verification.** Garcia & Tolkova 2025 is the anticipating study. Whether their
paper already reports seasonal variation of the ratio could not be read (the
journal page was blocked); check their supplement, included in the DCLDE bucket,
before claiming this test is new.

## P6 What an echo sees of a jewel

**Claimed contribution.** Simulated echoes of real jewellery meshes at dolphin
click frequencies, testing whether sub-wavelength lattices are resolved and
whether amber is acoustically faint beside silver; auralised "sonar portraits".

**Verification.** Echo physics and dolphin discrimination of material and wall
thickness are established (Au; DeLong et al. 2007). Simulated click–object echoes
exist (Wei et al. 2021). No simulation or artwork using jewellery meshes was found.
SpeakDolphin's 3D prints are a contested contrast, not a precedent for the method.

**Residual risk.** Material parameters for amber at ultrasonic frequencies need
a citable source or measurement; rigid-body BEM ignores elastic ringing.

## P7 A whistle alphabet from sparse features

**Claimed contribution.** Sparse-autoencoder features of a species-trained
bioacoustic encoder, tested against contour descriptors and nuisance variables
on session-held-out whistles, with a general-encoder comparison.

**Verification.** Searches of arXiv, Hugging Face papers and the web found SAE
work on speech models, audio codecs and singing, probing of bioacoustic
embeddings and prototype models for birds, but no SAE on AVES, BEATs, Perch,
NatureLM, animal2vec or a dolphin encoder.

**Residual risk.** A fast-moving area; repeat the search before writing up.

## P8 A day ring: 24 hours of seven dolphins

**Claimed contribution.** Context and time structure of whistle output in a
continuous captive recording, plus a cross-population transfer test of the
OpenWhistle encoder; the day ring.

**Verification.** The dataset authors built it for behavioural classification,
so context-versus-vocal-output analyses probably exist in their paper; we did
not read it in full. Cross-population transfer of the 2026 encoder was not found.

---

## Evidence ledger

E = established, P = probable, S = speculative; confidence H/M/L. Rows are
transfers into our setting, not published results, except where the pilot has
now measured them. Conflict marks a material contrary finding or constraint.

| Claim | Tier | Conf | Conflict | Modality | Source | Status | Verify |
|---|---|---|---|---|---|---|---|
| In OpenWhistle test whistles, a 272-bit contour retains more encoder type information than 528-bit relief or 728-bit codec inscriptions, measured by paired macro-F1 at pilot evaluation | E | M | N | In silico | [pilot](hardata-ii-pilot.md); DOI 10.1073/pnas.0509918103 | Measured: +0.107 and +0.412, intervals exclude 0 | Cast and scan real bands; second encoder |
| In SanctSound tokens, DoLittle surprisal falls on in-context phrase repeats more than under context swap | S | L | N | In silico | DoLittle release (no paper); DOI 10.1126/science.adq7055 | Cand | Swap-controlled surprisal |
| In DCLDE, within-site day-held-out SRKW/TKW accuracy is below pooled accuracy | P | M | Y | In silico | DOI 10.1111/mms.70126; local audit | Cand | Leave-one-day-out probes |
| On OOI cables, single-cable moveout fits recover along-cable position but not side | E | H | N | In silico | DOI 10.1121/10.0044257 | Cand | Fit vs batch-1 localizations |
| In Cape Cod Bay 2019, calls per counted whale differ between early and late season | S | L | Y | Observational | DOI 10.3354/esr01384 | Cand | Bootstrap over 21 flights |
| At 30–80 kHz, Nanot's lattice and its hull give echo spectra within a few dB | P | M | N | In silico | DOI 10.1121/1.400930; DOI 10.1121/1.1909055 | Cand | BEM with mesh refinement |
| OpenWhistle SAE features align more with contour descriptors than nuisance variables | S | L | N | In silico | arXiv:2606.12503; arXiv:2602.05027 | Cand | Session-held-out regressions |
| OpenWhistle embeddings transfer to Oltremare tags better than CLAP | S | M | N | In silico | arXiv:2609.34839; DOI 10.17882/109081 | Cand | Day-held-out probes |

## Search log

Searches ran on 7 October 2026 through five parallel verification passes (web
search and fetch, arXiv API and HTML, Crossref, Europe PMC, bioRxiv API,
Hugging Face Hub and datasets-server, GitHub API, Zenodo and SEANOE). Hit counts
were not recorded. R/E/P/V denote retraction, expression-of-concern,
preregistration and published-version checks; ✓ marks a check performed.

| Topic | Representative queries | Checks |
|---|---|---|
| Representations and interpretability | sparse autoencoder bioacoustic / AVES / BEATs / Perch / NatureLM; interpretable features animal vocalization encoder; prototype bioacoustic | ☐R ☐E ☐P ✓V |
| Codecs and identity | neural audio codec bioacoustics species classification reconstruction; DAC EnCodec whale bird evaluation | ☐R ☐E ☐P ✓V |
| Temporal models | humpback song language model surprisal; sperm whale coda dialogue prediction 2025 2026; human vs model prediction animal vocal sequence | ☐R ☐E ☐P ✓V |
| Physical sound objects and art | artwork encode whale sound playable object; whale song sculpture jewellery; 3D printed record; optical groove playback | ☐R ☐E ☐P ☐V |
| Echolocation and objects | dolphin echolocation material wall thickness discrimination; echo simulation object FEM BEM dolphin click | ☐R ☐E ☐P ✓V |
| DCLDE tracks | DCLDE 2027 tracks; Goestchel DAS fin whale; orca ecotype held-out provider; Cape Cod Bay right whale acoustic abundance | ☐R ☐E ☐P ✓V |
| Datasets | dolphin whistle dataset behaviour 2025 2026; humpback unit annotated dataset; killer whale call type dataset; Oltremare SEANOE | ☐R ☐E ☐P ☐V |

Published-version checks (V) used Crossref to confirm that cited preprints and
articles exist with matching titles; preprints remain marked as preprints.
