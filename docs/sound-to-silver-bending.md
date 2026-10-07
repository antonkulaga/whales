# Sound to silver: bending a real ring without breaking it

Can a recorded whistle reshape one of Livia's cast-silver rings while the ring
stays wearable and castable? This study takes two of her stoneless pieces at
print resolution, bends them with dolphin and whale recordings, and measures
how far each sound may push before the casting would fail.

Code: [`experiments/silver.py`](../experiments/silver.py), viewer template
[`experiments/silver_page.html`](../experiments/silver_page.html), settings
[`resources/sound-silver.json`](../resources/sound-silver.json), tests
[`tests/test_silver.py`](../tests/test_silver.py).

```bash
uv run --group art --group mesh main.py art silver   # ~3 min; STLs from ~/Downloads/drive-folder
# → data/output/silver/index.html (live 3D viewer), results.json, stl/*-safe.stl
```

## The pieces

| Piece | Print file | Why |
|---|---|---|
| **Inline Ring**, silver, 2022 | `06_PARAM 2022/sound manipulation/INLINE/+2inline.stl`, 200,252 triangles, one watertight shell | Silver only. It comes from Livia's own 2022 "sound manipulation" Grasshopper folder, whose definition records microphone level with *Sound Capture* and moves points along a curve. A lattice band between two rails; thinnest rungs 0.62 mm, a quarter of its openings under 0.5 mm. |
| **Roots Ring**, silver, 2019 | `03_PARAM 2019/roots/ciopercute.stl`, 212,626 triangles after removing 57 two-triangle specks | Silver only, slender and adjustable, with three cups at the open end. Livia wrote that she would "geometrically reinforce it" for future castings, so it tests fragility. |

Both are open rings. The originals stay in the Drive export; nothing derived
from them is committed except the three renders below.

## Input → schema → output

**Input.** Five recordings: three OpenWhistle test-set whistles (SW_Nana, SW_Neo,
NSW_1), a DSWP sperm-whale coda (clicks only) and the art brush's synthesized
*wave* key. From each waveform the brush's ridge analysis gives, per 5 ms frame:

- **pitch:** octaves from the whistle's median, ±0.5 octave = full scale;
- **level:** dB above the recording's 20th-percentile floor, 0–1;
- **pitch slope:** octaves per second, ±4 = full scale.

**Schema.** The ring gets its own frame: the finger axis (largest moment of
inertia), a circle fitted to the innermost metal, the finger-hole radius per
angle, and the opening (the largest empty arc: 11° on Inline, 17° on Roots).

- **Time → position along the metal**, from one end of the open ring to the other
  (about 65 mm of metal on both rings).
- **Pitch → lift:** each cross-section slides along the finger.
- **Level → swell:** outer metal moves away from the finger. It is weighted 0.4,
  because it adds silver and closes openings fastest.
- **Slope → lean:** outer metal tilts along the finger, also weighted 0.4.

Each frame's value is spread by a Gaussian over 4 mm of metal and normalised, so
a value held over a long stretch reaches exactly that value. The bend is then

```
θ' = θ
r' = r + g · 0.4 · swell(θ) · w(r)              swell ≥ 0, w: 0 at the finger hole → 1 at 1.5 mm out
h' = h + g · lift(θ) + g · 0.4 · lean(θ) · (r − bore(θ)) / 3 mm
```

with *g* the push in mm at full scale.

**Why it cannot break apart.** Every point keeps its angle around the finger.
At a fixed angle, r' grows strictly with r, and h' grows strictly with h. So two
points can never meet: the surface cannot tear, fold through itself, or close the
finger hole. The bore radius `bore(θ)` is a smooth upper envelope of the
innermost metal, so `w = 0` on the whole finger-hole surface. The measured
finger-hole change was 0.000 mm in all 20 runs.

**What can still fail is the casting.** Rays are re-cast from every vertex of
the full print file after bending, and they measure two things:

- **walls:** inward along the normal. A wall fails below 0.6 mm, but only if it
  also lost more than 10% of its own original thickness.
- **openings:** outward. An opening fails below 0.4 mm, with the same 10% rule.

A test point just outside the surface also checks for passing through itself.
Tips and concave creases are set aside, because a single ray cannot measure them
(walls under 0.3 mm, openings under 0.1 mm). The **safe limit** is the largest
*g* that leaves at most 0.1% of the surface past a limit, found by bisection
between 0 and 8 mm. The 0.6 and 0.4 mm thresholds are assumed lost-wax sterling
limits; the caster should confirm them.

**Output.** For every piece × sound × gesture set:

- the safe limit, with checks at ½×, 1× and 2× that limit;
- the usual audio-reactive contrast, which pushes along the surface normal by the
  same amount;
- a full-resolution STL at the limit;
- one self-contained viewer page.

## Results

| Piece | Sound | Gestures | Safe limit | Moves up to | Silver | 2× limit | Live estimate at 2× | Naive push at limit |
|---|---|---|---:|---:|---:|---|---|---|
| Inline | SW_Nana | lift + swell + lean | 1.00 mm | 1.11 mm | +7.8% | fails (0.31%) | casts | fails: 27% too thin, 11% through itself |
| Inline | SW_Nana | lift only | 2.22 mm | 2.15 mm | 0.0% | fails (0.73%) | fails (0.23%) | |
| Inline | SW_Neo | lift + swell + lean | 3.64 mm | 1.24 mm | +9.6% | fails (0.21%) | casts | fails: 18% too thin, 6% through itself |
| Inline | SW_Neo | lift only | 8.00 mm+ | 1.93 mm | 0.0% | fails (0.47%) | casts | |
| Inline | NSW_1 | lift + swell + lean | 1.33 mm | 0.59 mm | +7.5% | fails (0.25%) | casts | fails: 9% too thin, 7% through itself |
| Inline | NSW_1 | lift only | 2.73 mm | 1.20 mm | 0.0% | fails (0.67%) | fails (0.23%) | |
| Inline | Sperm whale coda | lift + swell + lean | 8.00 mm+ | 0.51 mm | +10.4% | fails (0.16%) | casts | fails: 7% too thin, 7% through itself |
| Inline | Brush key F: wave | lift + swell + lean | 1.34 mm | 0.62 mm | +15.1% | fails (0.17%) | casts | fails: 13% too thin, 11% through itself |
| Inline | Brush key F: wave | lift only | 6.42 mm | 1.50 mm | 0.0% | fails (1.09%) | fails (0.20%) | |
| Roots | SW_Nana | lift + swell + lean | 3.70 mm | 4.05 mm | +12.6% | fails (0.29%) | casts | fails: 28% too thin, 18% through itself |
| Roots | SW_Nana | lift only | 4.28 mm | 4.15 mm | 0.0% | fails (0.28%) | casts | |
| Roots | SW_Neo | lift + swell + lean | 8.00 mm+ | 2.56 mm | +11.7% | casts | casts | fails: 7% too thin, 4% through itself |
| Roots | NSW_1 | lift + swell + lean | 3.66 mm | 1.66 mm | +9.6% | fails (0.23%) | casts | fails: 16% too thin, 13% through itself |
| Roots | NSW_1 | lift only | 4.12 mm | 1.83 mm | 0.0% | fails (0.22%) | casts | |
| Roots | Sperm whale coda | lift + swell + lean | 8.00 mm+ | 0.51 mm | +5.9% | casts | casts | fails: 2% too thin, 2% through itself |
| Roots | Brush key F: wave | lift + swell + lean | 8.00 mm+ | 3.64 mm | +42.5% | casts | casts | fails: 3% too thin, 2% through itself |

The table omits lift-only rows for the coda, which has no pitch and so no lift, and for Roots with SW_Neo and the wave, which never reached a limit.
"8.00 mm+" means the search range ended first. Percentages in brackets are the
share of the surface past a limit.

![Inline, lift only, SW_Nana at its 2.22 mm limit, original as a ghost](figures/silver-inline-lift.png)

*Inline with lift only, at the 2.22 mm limit for SW_Nana. The band follows the
whistle's slow rise along the finger. The original is the grey ghost. Silver
weight and finger hole are unchanged.*

![Roots, all gestures, SW_Nana at its 3.70 mm limit](figures/silver-roots-all.png)

*Roots with all three gestures, at the 3.70 mm limit for SW_Nana. The cups lift
and lean by up to 4 mm.*

![Roots, naive push along the surface normal at the same 3.70 mm](figures/silver-roots-naive.png)

*The usual audio-reactive move at the same push. Where the pitch is below the
median, the shank erodes to a sliver and the cups pass through themselves (red).*

## Findings

1. **A real piece can change by millimetres without tearing.** The finger hole
   stays exactly the same in every run. Roots moves by up to 4 mm. Inline moves
   by about 2 mm with lift alone, and lift keeps the silver's weight exactly.
2. **The limit is the casting, and it differs by piece.** Inline is already at
   the edge: rungs of 0.62 mm and openings near 0.4 mm. Any shear that flattens a
   round rung, or slides two rungs together, uses up the margin, so all three
   gestures stop at about 1 mm. Roots has 1.15 mm wires and stops at 3.7 mm, or
   later. In nearly every failing case, an opening narrows first; walls rarely do.
3. **Swell is the costly gesture.** It thickens the band outward from the
   finger, adding 6–43% silver, and closes openings fastest. Lift moves whole
   cross-sections and keeps the weight.
4. **The usual approach breaks the piece at the same push.** Pushing along the
   normal fails on every piece and sound: 2–28% of the surface becomes too thin,
   and 2–18% passes through itself.
5. **Clicks alone barely move the metal.** The coda has no pitch, so it only
   swells, by at most 0.5 mm. Whistles carry the change.

## The viewer

`data/output/silver/index.html` is one self-contained page, about 3.5 MB. It shows:

- a 60,000-triangle version of each ring, with the original as a ghost;
- the recording's pitch and level, above the lift and swell they write along the metal;
- a push slider marked at the verified limit, gesture toggles and the naive contrast;
- a live assay, with colour modes for movement and casting risk.

*Play and bend* plays the recording and bends the ring as it plays. A loaded
audio file is measured in the browser. *Whistle live* records 6 s from the
microphone in the local copy; the published artifact cannot use the microphone.

The browser runs the same map as Python. On 640 reference vertices it agrees to
0.0005 mm, the uint16 quantisation of the stored positions.

The live assay pairs each vertex with the point straight across its wall and
its opening on the print file, and moves both ends together. That is cheap but
**optimistic**: it cannot see new near-contacts. At twice the limit it still
said "casts" in 10 of the 13 cases where the full file fails. So the page treats
anything past the verified limit as failing, whatever the estimate says.

## Moving versions

A cast bend is frozen. These studies keep the piece moving after casting, and
each one is built from Livia's print-and-cast pipeline plus hobby electronics,
with under €200 in parts per prototype. The page animates them on her real
models with the measured whistles:

```bash
uv run --group art --group mesh main.py art silver-motion   # → data/output/silver/motion.html
```

| Study | Follows a whistle | Worn | Parts, roughly | Livia adds |
|---|---|---|---|---|
| **Ferrofluid stones** in Roots' three cups (start here) | Live | Yes; moves on its stand | €80–150: display ferrofluid, glass or resin domes, a 12 V electromagnet, ESP32 board, microphone, driver | Cups for sealed domes; a stand with the coil |
| **Hinged Inline + nitinol**: 12 cast segments, Flexinol wire along both rails | At ¼–⅛ speed (about 1 s to pull, 0.2 s to relax) | Yes, with a battery | €60–120: 0.003″ Flexinol (≈ $2.50 per foot), crimps, ESP32 board, microphone, MOSFETs, small LiPo | Hinged segments |
| **Magnetic fins**: silicone fins, a 1 mm magnet in each, two coil pairs in the stand | Live | Yes; moves on its stand | €80–150: silicone, magnets, four small coils, H-bridge, ESP32 board | Fin moulds; slots in the rail |
| **Memory cells**: bistable domes written by a head on a turntable stand | One write per sound, then holds | Yes, no electronics | €50–120: snap domes with tiny magnets, one coil, ESP32 board | Dome seats along the band |

The cup centres in Roots are found from the print file: points in the air that
are about half enclosed by metal and at least 1.5 mm from it. The animations
are schematics with first-order lags, not material simulations.

## Next

- Prototype the ferrofluid stones: they are the cheapest and fastest of the
  moving studies. Buy display-grade ferrofluid, since plain ferrofluid stains
  glass.
- Ask Livia's caster for the real wall and opening limits; both are one line in
  the config.
- Print one safe and one 2× STL of Roots in wax resin and cast them. That is the
  only real test of the 0.1% surface tolerance.
- Let a long recording wind around the ring more than once, or give each rail of
  Inline its own phrase.
- Carry the same map to the jewelry buildings in Livistone, where wall limits are
  structural rather than casting limits.
