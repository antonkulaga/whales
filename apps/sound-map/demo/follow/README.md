# Phrase Atlas demo bundle

A copy of what the player needs from `data/output/follow`: 20 source excerpts and
22 finished combinations, as MP3 stems and WebP spectrograms (Git LFS). The server reads it
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
| `sperm-a` | Sperm-whale codas: DSWP rows 0–7 in sequence | Dominica, west-coast study region | Separate coda clips placed one after another; the 0.8 s silences between clips are ours, not recorded. |
| `orca-orcasound-lab` | Southern Resident killer whales, Orcasound Lab, September 2017 | Orcasound Lab, Haro Strait | 11 annotated killer-whale call rows in this window of the DCLDE 2027 table (OrcaSound); certain identifications only. Chosen as the clearest annotated window at this hydrophone: calls stand about 19 dB above the background in their band. |
| `orca-bush-point` | Southern Resident killer whales, Bush Point, September 2020 | Bush Point, Whidbey Island | 13 annotated killer-whale call rows in this window of the DCLDE 2027 table (OrcaSound); certain identifications only. |
| `orca-tekteksen` | Southern Resident killer whales, Tekteksen, August 2022 | Tekteksen, Saturna Island | 34 annotated killer-whale call rows in this window of the DCLDE 2027 table (SIMRES); certain identifications only. |
| `orca-cape-elizabeth` | Bigg's (transient) killer whales, Cape Elizabeth, June 2011 | Cape Elizabeth, outer Washington coast | 10 annotated killer-whale call rows in this window of the DCLDE 2027 table (SIO); certain identifications only. |
| `humpback-cape-elizabeth` | Humpback whale calls, Cape Elizabeth, October 2011 | Cape Elizabeth, outer Washington coast | 13 annotated humpback call rows in this window of the DCLDE 2027 table (SIO); certain identifications only. |
| `orca-montague` | Offshore killer whales, Montague Strait, April 2023 | Montague Strait, Alaska | 22 annotated killer-whale call rows in this window of the DCLDE 2027 table (UAF_NGOS); certain identifications only. |
| `right-whale-stellwagen` | North Atlantic right whale upcalls, Stellwagen Bank, April 2009 | Stellwagen Bank, Massachusetts | Upcalls logged as definite in the NEFSC baleen-whale log for DCLDE 2013 (Nicole Pegg, Alexandra Carroll); 2 kHz bottom recorder. |
| `fin-whale-stellwagen` | Fin whale 20 Hz song, Stellwagen Bank, March 2009 | Stellwagen Bank, Massachusetts | 20 Hz pulses logged as definite in the NEFSC baleen-whale log for DCLDE 2013 (Alexandra Carroll); 2 kHz bottom recorder. |
| `blue-whale-channel-islands` | Blue whale D calls, Channel Islands, June 2012 | Channel Islands, Santa Barbara Channel | D calls logged with start and end times (no frequency bounds) for the DCLDE 2015 low-frequency task; HARP recording decimated to 2 kHz. |
| `minke-whale-niihau` | Minke whale boings, west of Niʻihau, November 2017 | West of Niʻihau, Hawaiʻi | The release's minke sheet logs 10 boing detections in this window; events are measured from the waveform in 1.0–2.2 kHz. Towed-array hydrophone 1. |
| `striped-dolphin-nwhi` | Striped dolphins, north of the Northwestern Hawaiian Islands, August 2017 | North of the Northwestern Hawaiian Islands | Acoustic encounter logged as striped dolphins; the group passed about 265 m abeam at 02:00 UTC. Whistles are detected from the waveform. |
| `rough-toothed-dolphin-kure` | Rough-toothed dolphins, north of Kure Atoll, August 2017 | North of Kure Atoll | Acoustic encounter logged as rough-toothed dolphins; the group passed about 150 m abeam at 06:26 UTC. Whistles are detected from the waveform. |
| `spinner-dolphin-palmyra` | Spinner dolphin whistles, Palmyra Atoll, October 2007 | Palmyra Atoll | Whistle contours traced by analysts (DCLDE 2011, 2025 re-annotation); observers confirmed a single-species group. Whistles centred above 23.5 kHz are left out. |
| `atlantic-spotted-dolphin-mid-atlantic` | Atlantic spotted dolphin whistles, U.S. mid-Atlantic, July 2011 | U.S. mid-Atlantic shelf | Whistle contours traced by analysts (DCLDE 2011 evaluation set); observers confirmed a single-species group. The ship's echosounder ticks near 18 kHz. |
| `blue-whale-weddell-69s` | Antarctic blue whale Z-call, Weddell Sea 69°S, January 2013 | Weddell Sea, 69°S on the Greenwich meridian | One complete Z-call from a regular singer who called about every 69 s, logged at 115 dB re 1 µPa by AWI's automated Z-call detector (PANGAEA 960121). The call spans 16 s before to 10 s after its logged time and is trimmed to where 17.5–29 Hz rises 6 dB above the 10-minute recording's background (our choice). AWI Ocean Acoustics Group recording, PANGAEA 973160; 5.3 kHz recorder resampled to 2 kHz. |
| `blue-whale-weddell-59s` | Antarctic blue whale Z-call, Southern Ocean 59°S, May 2013 | Southern Ocean, 59°S on the Greenwich meridian | One complete Z-call from a regular singer who called about every 69 s, logged at 120 dB re 1 µPa by AWI's automated Z-call detector (PANGAEA 960031). The call spans 16 s before to 10 s after its logged time and is trimmed to where 17.5–29 Hz rises 6 dB above the 10-minute recording's background (our choice). AWI Ocean Acoustics Group recording, PANGAEA 966612; 5.3 kHz recorder resampled to 2 kHz. |

## Combinations

| Id | Title | Parts | ACE-Step |
|---|---|---|---|
| `a496d5d52db5` | Antarctic blue whale beneath the dolphins | blue-whale-weddell-59s, spinner-dolphin-palmyra, striped-dolphin-nwhi | yes |
| `31eabc332b49` | Atlantic and Pacific baleen | right-whale-stellwagen, fin-whale-stellwagen, blue-whale-channel-islands, minke-whale-niihau | yes |
| `da5654bbad18` | Blue whales, two oceans | blue-whale-channel-islands, blue-whale-weddell-69s | yes |
| `931c1ae42021` | Dominica answers Montague Strait | sperm-a, orca-montague | yes |
| `5431cf74e40d` | Four-species chorus | humpback-a, orca-montague, dolphin-a, sperm-a | yes |
| `104edba3a24c` | From the Weddell Sea to Alaska | blue-whale-weddell-69s, orca-montague, orca-cape-elizabeth | yes |
| `5668eb0a269f` | Giants and singers | blue-whale-channel-islands, humpback-a, fin-whale-stellwagen, orca-orcasound-lab | yes |
| `f72fcf9ad790` | Haro Strait answers Dominica | humpback-a, sperm-a | yes |
| `dc677d8cc60e` | Hawaiian night | minke-whale-niihau, striped-dolphin-nwhi, rough-toothed-dolphin-kure | yes |
| `5943fd881123` | Humpback and orcas share Haro Strait | humpback-a, orca-orcasound-lab | yes |
| `ab0adfc9b3d0` | Killer whale & Dolphin & Sperm whale ensemble | orca-tekteksen, orca-cape-elizabeth, orca-bush-point, orca-montague, dolphin-a, sperm-a | yes |
| `e54d6b424adb` | Killer whale & Humpback ensemble | orca-cape-elizabeth, humpback-cape-elizabeth | yes |
| `6559aa1d360a` | orca-cape-elizabeth + dolphin-a + orca-montague | orca-cape-elizabeth, dolphin-a, orca-montague | yes |
| `6ecc88ef390a` | Red Sea to Salish Sea | dolphin-a, sperm-a, humpback-cape-elizabeth, orca-tekteksen, humpback-a | yes |
| `ba5bea77119d` | Southern Ocean blue whales | blue-whale-weddell-69s, blue-whale-weddell-59s | yes |
| `884ef0c9055d` | Southern Ocean meets Stellwagen | blue-whale-weddell-59s, right-whale-stellwagen, fin-whale-stellwagen, humpback-cape-elizabeth | yes |
| `c79ca2b67258` | Southern Residents down the Salish Sea | orca-tekteksen, orca-orcasound-lab, orca-bush-point | yes |
| `1f88378ee478` | Stellwagen answers Haro Strait | right-whale-stellwagen, humpback-a | yes |
| `862437f5745b` | Three killer-whale ecotypes | orca-tekteksen, orca-cape-elizabeth, orca-montague | yes |
| `d37737c7b1be` | Three seas | humpback-b, dolphin-a, sperm-a | yes |
| `527cc9dddc35` | Two humpback coasts | humpback-a, humpback-cape-elizabeth | yes |
| `48d9eb707419` | Whistles across three oceans | spinner-dolphin-palmyra, atlantic-spotted-dolphin-mid-atlantic, dolphin-a | yes |
