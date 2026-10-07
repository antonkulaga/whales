# Phrase Atlas demo bundle

A copy of what the player needs from `data/output/follow`: 14 source excerpts and
10 finished combinations, as MP3 stems and WebP spectrograms (Git LFS). The server reads it
whenever `data/output/follow` has not been built, so `bun run dev` works on a fresh clone.
Making new combinations still needs the Python pipeline. Regenerate with `bun scripts/demo.ts`.

Excerpt choices, measurement settings and download URLs are in `resources/follow-music.json`;
the method is in `docs/follow-the-phrase.md`. Guides, responses and ACE-Step stems are generated;
only the animal stems are recordings.

## Sources

| Id | Recording | Place | Note |
|---|---|---|---|
| `humpback-a` | Humpback song: ascending moan, growl, whup ×3 | Orcasound Lab, Haro Strait | Annotated units 33–42 of Emily Vierling's Orcasound selection table; the excerpt start and length are ours. |
| `humpback-b` | Humpback song: moans, upsweep and cries | Orcasound Lab, Haro Strait | Annotated units 6–13 of the same recording; a different phrase type from humpback-a. |
| `dolphin-a` | Bottlenose dolphin whistles, OpenWhistle sequence 94 | Dolphin Reef, Eilat | Whistles are detected from the waveform, not annotated; detection can also respond to noise. |
| `dolphin-b` | Bottlenose dolphin whistles, OpenWhistle sequence 37 | Dolphin Reef, Eilat | Whistles are detected from the waveform, not annotated. |
| `sperm-a` | Sperm-whale codas: DSWP rows 0–7 in sequence | Dominica, west-coast study region | Separate coda clips placed one after another; the 0.8 s silences between clips are ours, not recorded. |
| `sperm-b` | Sperm-whale codas: DSWP rows 8–15 in sequence | Dominica, west-coast study region | Separate coda clips placed one after another; the 0.8 s silences between clips are ours. |
| `orca-orcasound-lab` | Southern Resident killer whales, Orcasound Lab, July 2019 | Orcasound Lab, Haro Strait | 20 annotated killer-whale call rows in this window of the DCLDE 2027 table (OrcaSound); certain identifications only. |
| `orca-bush-point` | Southern Resident killer whales, Bush Point, September 2020 | Bush Point, Whidbey Island | 13 annotated killer-whale call rows in this window of the DCLDE 2027 table (OrcaSound); certain identifications only. |
| `orca-port-townsend` | Southern Resident killer whales, Port Townsend, September 2020 | Port Townsend | 13 annotated killer-whale call rows in this window of the DCLDE 2027 table (OrcaSound); certain identifications only. |
| `orca-tekteksen` | Southern Resident killer whales, Tekteksen, August 2022 | Tekteksen, Saturna Island | 34 annotated killer-whale call rows in this window of the DCLDE 2027 table (SIMRES); certain identifications only. |
| `orca-cape-elizabeth` | Bigg's (transient) killer whales, Cape Elizabeth, June 2011 | Cape Elizabeth, outer Washington coast | 10 annotated killer-whale call rows in this window of the DCLDE 2027 table (SIO); certain identifications only. |
| `humpback-cape-elizabeth` | Humpback whale calls, Cape Elizabeth, October 2011 | Cape Elizabeth, outer Washington coast | 13 annotated humpback call rows in this window of the DCLDE 2027 table (SIO); certain identifications only. |
| `orca-kachemak` | Offshore killer whales, Kachemak Bay, May 2022 | Kachemak Bay, Alaska | 28 annotated killer-whale call rows in this window of the DCLDE 2027 table (UAF_NGOS); certain identifications only. |
| `orca-montague` | Offshore killer whales, Montague Strait, April 2023 | Montague Strait, Alaska | 22 annotated killer-whale call rows in this window of the DCLDE 2027 table (UAF_NGOS); certain identifications only. |

## Combinations

| Id | Title | Parts | ACE-Step |
|---|---|---|---|
| `72fcf1374717` | Alaska offshore duet | orca-kachemak, orca-montague | yes |
| `05683d1c11dd` | Dominica answers Kachemak | sperm-b, orca-kachemak | yes |
| `7dbd8797bc13` | Four-species chorus | humpback-a, orca-kachemak, dolphin-b, sperm-b | yes |
| `e3c5fb408486` | Haro Strait answers Dominica | humpback-a, sperm-b | yes |
| `eb3efaffac00` | Humpback and orcas share Haro Strait | humpback-a, orca-orcasound-lab | yes |
| `5996e8f9b435` | Red Sea to Salish Sea | dolphin-a, sperm-a, humpback-cape-elizabeth, orca-tekteksen, humpback-a | yes |
| `bd73bf018cd1` | Southern Residents down the Salish Sea | orca-tekteksen, orca-orcasound-lab, orca-port-townsend, orca-bush-point | yes |
| `aaca05e5f993` | Three killer-whale ecotypes | orca-tekteksen, orca-cape-elizabeth, orca-kachemak | yes |
| `4eace9421fea` | Three seas in sequence | humpback-b, dolphin-a, sperm-a | yes |
| `ac1e166854ac` | Two humpback coasts | humpback-a, humpback-cape-elizabeth | yes |
