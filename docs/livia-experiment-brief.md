# Starting from Livia's objects

The first generic paper/thread/glass palette was a poor connection to Livia's
practice. The revised experiments use actual jewelry photographs from the
`livia` checkout and the town scene and source-backed catalogue from `livistone`.
The repeatable brief is [livia-profile.json](../resources/livia-profile.json).

Livia models, prints and casts metal settings around natural materials. The
setting is a geometric and practical problem: it must hold and reveal a stone,
protect an irregular tip, or allow drainage around porous opal. Her open silver
structures already connect biological forms, architecture and wearable objects.
Livistone develops the architectural reading by enlarging selected pieces into
inhabitable spaces.

| Actual source | Documented form / problem | Use in these experiments |
|---|---|---|
| Nanot of Power | Open cast-silver lattice; Livistone's science hall | Reference image 1 for open cells and repeated structural bays |
| Mitoring | Irregular amber within folded silver; Livistone's energy hall | Reference image 2 for metal/stone relation; original for the setting edits |
| Mycelium | Fungal-inspired silver setting permits drainage around porous opal | Brief context for open channels, rather than decorative surface texture |
| Livistone centre | Jewelry enlarged into buildings: amber, walnut, silver lattice | Reference image 3 for the pavilion's change of scale |

The connection comes from `livia/content/pieces.md`, `content/biography.md`,
the original exhibition photographs, and `livistone/src/game/piece-stories.ts`,
`src/game/jewelry-catalogue.json` and `README.md`. Each run records the local
source paths and document/image SHA-256 hashes. Portable copies of the photos
and the exact padded model inputs accompany the generated images.

## Two implemented experiments

1. **Sound → jewelry → inhabited form.** The same two jewelry photographs,
   acoustic vocabulary and seed are held fixed across six recordings. CLAP
   selects a descriptor; our proposed mapping selects open cells, continuous
   ribbons or undulating folds. FLUX generates a ring concept and a pavilion
   concept. The pavilion also receives the Livistone scene as a scale reference.
2. **Mitoring listens.** Four recordings spanning the shared RMS reference
   range vary one Mitoring photograph. The amber, camera and background are
   requested to stay fixed. The silver setting receives a bounded structural
   instruction. The gallery shows the original alongside the generated edits.

The sound-to-geometry correspondences are our hypotheses for this experiment,
not rules authored or approved by Livia. CLAP's three-way winner is coarse;
different clips with the same winner produce identical concepts at a fixed
seed. RMS also depends on recording gain and distance. None of this decodes
animal meanings. These are image concepts; wearability, structural integrity
and fabrication would require separate geometric work and artist review.

Run both with `uv run --group art main.py art livia`. The sibling checkout roots
can be overridden with `--livia-dir` and `--livistone-dir`. Results appear in
`data/output/index.html`, with Listen buttons, original references, scores,
geometry choices, actual prompts and JSON provenance.

## Longer recordings and explicit controls

The three CLAP winners are a coarse bottleneck: their image prompts differ
little while the references strongly determine the result. Longer input alone
would not solve that bottleneck, especially with a ten-second preprocessing
crop. The follow-up `art long-forms` reads whole 30.8/36-second, 96 kHz
OpenWhistle pretraining sequences and compares 5s/15s/full prefixes.

An explicit silver/amber cocoon now has three numeric controls: prefix duration
sets rib count, frame spectral centroid sets mid-height rib radius, and local
RMS sets rib diameter. Shared reference ranges are fitted to both whole source
recordings and remain fixed for the prefix comparisons. The mesh is generated
directly from those values. The gallery supplies diagrams, the measured curves,
matching audio and OBJ files, making the acoustic influence inspectable before
any subsequent image model adds its own interpretation.
