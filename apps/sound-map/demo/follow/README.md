# Phrase Atlas demo bundle

A copy of what the player needs from `data/output/follow`: 20 source excerpts and
212 finished combinations, as MP3 stems and WebP spectrograms (Git LFS). The server reads it
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
| `46f5dd459425` | atlantic-spotted-dolphin-mid-atlantic + blue-whale-channel-islands | atlantic-spotted-dolphin-mid-atlantic, blue-whale-channel-islands | yes |
| `934308bb7aca` | atlantic-spotted-dolphin-mid-atlantic + blue-whale-weddell-59s | atlantic-spotted-dolphin-mid-atlantic, blue-whale-weddell-59s | yes |
| `4f9d07bec6b4` | atlantic-spotted-dolphin-mid-atlantic + blue-whale-weddell-69s | atlantic-spotted-dolphin-mid-atlantic, blue-whale-weddell-69s | yes |
| `964d10793308` | atlantic-spotted-dolphin-mid-atlantic + dolphin-a | atlantic-spotted-dolphin-mid-atlantic, dolphin-a | yes |
| `1f1fd28d5517` | atlantic-spotted-dolphin-mid-atlantic + fin-whale-stellwagen | atlantic-spotted-dolphin-mid-atlantic, fin-whale-stellwagen | yes |
| `3b0291f2dbaf` | atlantic-spotted-dolphin-mid-atlantic + humpback-a | atlantic-spotted-dolphin-mid-atlantic, humpback-a | yes |
| `c3d9d17a1d78` | atlantic-spotted-dolphin-mid-atlantic + humpback-b | atlantic-spotted-dolphin-mid-atlantic, humpback-b | yes |
| `419cb38651a1` | atlantic-spotted-dolphin-mid-atlantic + humpback-cape-elizabeth | atlantic-spotted-dolphin-mid-atlantic, humpback-cape-elizabeth | yes |
| `ffc3d15f9940` | atlantic-spotted-dolphin-mid-atlantic + minke-whale-niihau | atlantic-spotted-dolphin-mid-atlantic, minke-whale-niihau | yes |
| `f94fbdd5db9f` | atlantic-spotted-dolphin-mid-atlantic + orca-bush-point | atlantic-spotted-dolphin-mid-atlantic, orca-bush-point | yes |
| `3b27bbbd19bf` | atlantic-spotted-dolphin-mid-atlantic + orca-cape-elizabeth | atlantic-spotted-dolphin-mid-atlantic, orca-cape-elizabeth | yes |
| `fd28552e697a` | atlantic-spotted-dolphin-mid-atlantic + orca-montague | atlantic-spotted-dolphin-mid-atlantic, orca-montague | yes |
| `b5dafa1f5ce0` | atlantic-spotted-dolphin-mid-atlantic + orca-orcasound-lab | atlantic-spotted-dolphin-mid-atlantic, orca-orcasound-lab | yes |
| `708574ee9dd3` | atlantic-spotted-dolphin-mid-atlantic + orca-tekteksen | atlantic-spotted-dolphin-mid-atlantic, orca-tekteksen | yes |
| `bbba007a6d75` | atlantic-spotted-dolphin-mid-atlantic + right-whale-stellwagen | atlantic-spotted-dolphin-mid-atlantic, right-whale-stellwagen | yes |
| `c7525684ba65` | atlantic-spotted-dolphin-mid-atlantic + rough-toothed-dolphin-kure | atlantic-spotted-dolphin-mid-atlantic, rough-toothed-dolphin-kure | yes |
| `16177c7811fa` | atlantic-spotted-dolphin-mid-atlantic + sperm-a | atlantic-spotted-dolphin-mid-atlantic, sperm-a | yes |
| `6d8f0777d90c` | atlantic-spotted-dolphin-mid-atlantic + spinner-dolphin-palmyra | atlantic-spotted-dolphin-mid-atlantic, spinner-dolphin-palmyra | yes |
| `f3ec5d628e4f` | atlantic-spotted-dolphin-mid-atlantic + striped-dolphin-nwhi | atlantic-spotted-dolphin-mid-atlantic, striped-dolphin-nwhi | yes |
| `da5654bbad18` | Blue whales, two oceans | blue-whale-channel-islands, blue-whale-weddell-69s | yes |
| `199b071459bd` | blue-whale-channel-islands + blue-whale-weddell-59s | blue-whale-channel-islands, blue-whale-weddell-59s | yes |
| `f5fa183b5567` | blue-whale-channel-islands + blue-whale-weddell-69s | blue-whale-channel-islands, blue-whale-weddell-69s | yes |
| `b649ff5c6e81` | blue-whale-channel-islands + dolphin-a | blue-whale-channel-islands, dolphin-a | yes |
| `bdcfc8502516` | blue-whale-channel-islands + fin-whale-stellwagen | blue-whale-channel-islands, fin-whale-stellwagen | yes |
| `96f83c974b8e` | blue-whale-channel-islands + humpback-a | blue-whale-channel-islands, humpback-a | yes |
| `3e53d42fc482` | blue-whale-channel-islands + humpback-b | blue-whale-channel-islands, humpback-b | yes |
| `78341628cc0a` | blue-whale-channel-islands + humpback-cape-elizabeth | blue-whale-channel-islands, humpback-cape-elizabeth | yes |
| `9b33b3a2b4ac` | blue-whale-channel-islands + minke-whale-niihau | blue-whale-channel-islands, minke-whale-niihau | yes |
| `40e3c9d7f180` | blue-whale-channel-islands + orca-bush-point | blue-whale-channel-islands, orca-bush-point | yes |
| `14d39ebaada4` | blue-whale-channel-islands + orca-cape-elizabeth | blue-whale-channel-islands, orca-cape-elizabeth | yes |
| `f410249558e2` | blue-whale-channel-islands + orca-montague | blue-whale-channel-islands, orca-montague | yes |
| `cc289abb111f` | blue-whale-channel-islands + orca-orcasound-lab | blue-whale-channel-islands, orca-orcasound-lab | yes |
| `c636c0104fdd` | blue-whale-channel-islands + orca-tekteksen | blue-whale-channel-islands, orca-tekteksen | yes |
| `2d799b1aab35` | blue-whale-channel-islands + right-whale-stellwagen | blue-whale-channel-islands, right-whale-stellwagen | yes |
| `9bd31f67134b` | blue-whale-channel-islands + rough-toothed-dolphin-kure | blue-whale-channel-islands, rough-toothed-dolphin-kure | yes |
| `cf177f0a0f01` | blue-whale-channel-islands + sperm-a | blue-whale-channel-islands, sperm-a | yes |
| `3d53efa0333b` | blue-whale-channel-islands + spinner-dolphin-palmyra | blue-whale-channel-islands, spinner-dolphin-palmyra | yes |
| `e00cd36e7f32` | blue-whale-channel-islands + striped-dolphin-nwhi | blue-whale-channel-islands, striped-dolphin-nwhi | yes |
| `9a7e06ec9b29` | blue-whale-weddell-59s + blue-whale-weddell-69s | blue-whale-weddell-59s, blue-whale-weddell-69s | yes |
| `e575fa54b559` | blue-whale-weddell-59s + dolphin-a | blue-whale-weddell-59s, dolphin-a | yes |
| `73835c79319f` | blue-whale-weddell-59s + fin-whale-stellwagen | blue-whale-weddell-59s, fin-whale-stellwagen | yes |
| `1be45496a8f4` | blue-whale-weddell-59s + humpback-a | blue-whale-weddell-59s, humpback-a | yes |
| `c63ada204de1` | blue-whale-weddell-59s + humpback-b | blue-whale-weddell-59s, humpback-b | yes |
| `4bb958761c44` | blue-whale-weddell-59s + humpback-cape-elizabeth | blue-whale-weddell-59s, humpback-cape-elizabeth | yes |
| `3a702fe6021e` | blue-whale-weddell-59s + minke-whale-niihau | blue-whale-weddell-59s, minke-whale-niihau | yes |
| `623ae6d9b981` | blue-whale-weddell-59s + orca-bush-point | blue-whale-weddell-59s, orca-bush-point | yes |
| `8715e04da805` | blue-whale-weddell-59s + orca-cape-elizabeth | blue-whale-weddell-59s, orca-cape-elizabeth | yes |
| `3b15505740bd` | blue-whale-weddell-59s + orca-montague | blue-whale-weddell-59s, orca-montague | yes |
| `41dd72e4c91d` | blue-whale-weddell-59s + orca-orcasound-lab | blue-whale-weddell-59s, orca-orcasound-lab | yes |
| `365b180512da` | blue-whale-weddell-59s + orca-tekteksen | blue-whale-weddell-59s, orca-tekteksen | yes |
| `2809f1288ebc` | blue-whale-weddell-59s + right-whale-stellwagen | blue-whale-weddell-59s, right-whale-stellwagen | yes |
| `8190f9f1d630` | blue-whale-weddell-59s + rough-toothed-dolphin-kure | blue-whale-weddell-59s, rough-toothed-dolphin-kure | yes |
| `c660a10313b4` | blue-whale-weddell-59s + sperm-a | blue-whale-weddell-59s, sperm-a | yes |
| `3f8acc537b55` | blue-whale-weddell-59s + spinner-dolphin-palmyra | blue-whale-weddell-59s, spinner-dolphin-palmyra | yes |
| `e98212a6d563` | blue-whale-weddell-59s + striped-dolphin-nwhi | blue-whale-weddell-59s, striped-dolphin-nwhi | yes |
| `9acb5a46d76b` | blue-whale-weddell-69s + dolphin-a | blue-whale-weddell-69s, dolphin-a | yes |
| `10c0cd1deb2f` | blue-whale-weddell-69s + fin-whale-stellwagen | blue-whale-weddell-69s, fin-whale-stellwagen | yes |
| `3d6460b92166` | blue-whale-weddell-69s + humpback-a | blue-whale-weddell-69s, humpback-a | yes |
| `9b6eac559255` | blue-whale-weddell-69s + humpback-b | blue-whale-weddell-69s, humpback-b | yes |
| `eb58450794a1` | blue-whale-weddell-69s + humpback-cape-elizabeth | blue-whale-weddell-69s, humpback-cape-elizabeth | yes |
| `74a428ebf6a4` | blue-whale-weddell-69s + minke-whale-niihau | blue-whale-weddell-69s, minke-whale-niihau | yes |
| `84becf0a6cbc` | blue-whale-weddell-69s + orca-bush-point | blue-whale-weddell-69s, orca-bush-point | yes |
| `678db5b5a58a` | blue-whale-weddell-69s + orca-cape-elizabeth | blue-whale-weddell-69s, orca-cape-elizabeth | yes |
| `816a3fe55dcb` | blue-whale-weddell-69s + orca-montague | blue-whale-weddell-69s, orca-montague | yes |
| `a7414813937f` | blue-whale-weddell-69s + orca-orcasound-lab | blue-whale-weddell-69s, orca-orcasound-lab | yes |
| `709143dbe038` | blue-whale-weddell-69s + orca-tekteksen | blue-whale-weddell-69s, orca-tekteksen | yes |
| `3c23ad3bbbdb` | blue-whale-weddell-69s + right-whale-stellwagen | blue-whale-weddell-69s, right-whale-stellwagen | yes |
| `26036e84d0ce` | blue-whale-weddell-69s + rough-toothed-dolphin-kure | blue-whale-weddell-69s, rough-toothed-dolphin-kure | yes |
| `f56893eca707` | blue-whale-weddell-69s + sperm-a | blue-whale-weddell-69s, sperm-a | yes |
| `3e773c6af37f` | blue-whale-weddell-69s + spinner-dolphin-palmyra | blue-whale-weddell-69s, spinner-dolphin-palmyra | yes |
| `103c66232365` | blue-whale-weddell-69s + striped-dolphin-nwhi | blue-whale-weddell-69s, striped-dolphin-nwhi | yes |
| `3319f7712a10` | dolphin-a + fin-whale-stellwagen | dolphin-a, fin-whale-stellwagen | yes |
| `1a42c39cee30` | dolphin-a + humpback-a | dolphin-a, humpback-a | yes |
| `69566d372e12` | dolphin-a + humpback-b | dolphin-a, humpback-b | yes |
| `eadeb7df4052` | dolphin-a + humpback-cape-elizabeth | dolphin-a, humpback-cape-elizabeth | yes |
| `34aee0291477` | dolphin-a + minke-whale-niihau | dolphin-a, minke-whale-niihau | yes |
| `0ba17bbd9217` | dolphin-a + orca-bush-point | dolphin-a, orca-bush-point | yes |
| `7a38d35cbbe1` | dolphin-a + orca-cape-elizabeth | dolphin-a, orca-cape-elizabeth | yes |
| `27e92044f3db` | dolphin-a + orca-montague | dolphin-a, orca-montague | yes |
| `9f4dd82e3423` | dolphin-a + orca-orcasound-lab | dolphin-a, orca-orcasound-lab | yes |
| `c8cc36a4ac9b` | dolphin-a + orca-tekteksen | dolphin-a, orca-tekteksen | yes |
| `0e1d252997cf` | dolphin-a + right-whale-stellwagen | dolphin-a, right-whale-stellwagen | yes |
| `813bb1712fc8` | dolphin-a + rough-toothed-dolphin-kure | dolphin-a, rough-toothed-dolphin-kure | yes |
| `c95b74190f5a` | dolphin-a + sperm-a | dolphin-a, sperm-a | yes |
| `031d17821e0a` | dolphin-a + spinner-dolphin-palmyra | dolphin-a, spinner-dolphin-palmyra | yes |
| `afe5fb608c18` | dolphin-a + striped-dolphin-nwhi | dolphin-a, striped-dolphin-nwhi | yes |
| `931c1ae42021` | Dominica answers Montague Strait | sperm-a, orca-montague | yes |
| `983734208793` | fin-whale-stellwagen + humpback-a | fin-whale-stellwagen, humpback-a | yes |
| `bc5ff614fc45` | fin-whale-stellwagen + humpback-b | fin-whale-stellwagen, humpback-b | yes |
| `0bbc7dc7d47b` | fin-whale-stellwagen + humpback-cape-elizabeth | fin-whale-stellwagen, humpback-cape-elizabeth | yes |
| `8a284b1e7f92` | fin-whale-stellwagen + minke-whale-niihau | fin-whale-stellwagen, minke-whale-niihau | yes |
| `621326d5396d` | fin-whale-stellwagen + orca-bush-point | fin-whale-stellwagen, orca-bush-point | yes |
| `9f72ddbfd0db` | fin-whale-stellwagen + orca-cape-elizabeth | fin-whale-stellwagen, orca-cape-elizabeth | yes |
| `b5de489bd393` | fin-whale-stellwagen + orca-montague | fin-whale-stellwagen, orca-montague | yes |
| `cd1a0c7c4779` | fin-whale-stellwagen + orca-orcasound-lab | fin-whale-stellwagen, orca-orcasound-lab | yes |
| `9e80ae03f29d` | fin-whale-stellwagen + orca-tekteksen | fin-whale-stellwagen, orca-tekteksen | yes |
| `f4b33b9ffc1d` | fin-whale-stellwagen + right-whale-stellwagen | fin-whale-stellwagen, right-whale-stellwagen | yes |
| `0278cbaf0699` | fin-whale-stellwagen + rough-toothed-dolphin-kure | fin-whale-stellwagen, rough-toothed-dolphin-kure | yes |
| `08e08501fc34` | fin-whale-stellwagen + sperm-a | fin-whale-stellwagen, sperm-a | yes |
| `f251cc2c0a7a` | fin-whale-stellwagen + spinner-dolphin-palmyra | fin-whale-stellwagen, spinner-dolphin-palmyra | yes |
| `a017cd26c1a4` | fin-whale-stellwagen + striped-dolphin-nwhi | fin-whale-stellwagen, striped-dolphin-nwhi | yes |
| `5431cf74e40d` | Four-species chorus | humpback-a, orca-montague, dolphin-a, sperm-a | yes |
| `104edba3a24c` | From the Weddell Sea to Alaska | blue-whale-weddell-69s, orca-montague, orca-cape-elizabeth | yes |
| `5668eb0a269f` | Giants and singers | blue-whale-channel-islands, humpback-a, fin-whale-stellwagen, orca-orcasound-lab | yes |
| `f72fcf9ad790` | Haro Strait answers Dominica | humpback-a, sperm-a | yes |
| `dc677d8cc60e` | Hawaiian night | minke-whale-niihau, striped-dolphin-nwhi, rough-toothed-dolphin-kure | yes |
| `5943fd881123` | Humpback and orcas share Haro Strait | humpback-a, orca-orcasound-lab | yes |
| `c464a1a51649` | humpback-a + humpback-b | humpback-a, humpback-b | yes |
| `271eb83dc8e9` | humpback-a + humpback-cape-elizabeth | humpback-a, humpback-cape-elizabeth | yes |
| `83194d025454` | humpback-a + minke-whale-niihau | humpback-a, minke-whale-niihau | yes |
| `f416fedefa8c` | humpback-a + orca-bush-point | humpback-a, orca-bush-point | yes |
| `9648b87bd5e7` | humpback-a + orca-cape-elizabeth | humpback-a, orca-cape-elizabeth | yes |
| `67b0c8a3f498` | humpback-a + orca-montague | humpback-a, orca-montague | yes |
| `ad8da54f5f6d` | humpback-a + orca-orcasound-lab | humpback-a, orca-orcasound-lab | yes |
| `0e64fa78f9b9` | humpback-a + orca-tekteksen | humpback-a, orca-tekteksen | yes |
| `dac0980ace41` | humpback-a + right-whale-stellwagen | humpback-a, right-whale-stellwagen | yes |
| `900c631b9cd7` | humpback-a + rough-toothed-dolphin-kure | humpback-a, rough-toothed-dolphin-kure | yes |
| `c6445484086e` | humpback-a + sperm-a | humpback-a, sperm-a | yes |
| `2a2ecf85e192` | humpback-a + spinner-dolphin-palmyra | humpback-a, spinner-dolphin-palmyra | yes |
| `9d9b39b051fd` | humpback-a + striped-dolphin-nwhi | humpback-a, striped-dolphin-nwhi | yes |
| `a550a136a46b` | humpback-b + humpback-cape-elizabeth | humpback-b, humpback-cape-elizabeth | yes |
| `e1a95529dd66` | humpback-b + minke-whale-niihau | humpback-b, minke-whale-niihau | yes |
| `9d5658a1f258` | humpback-b + orca-bush-point | humpback-b, orca-bush-point | yes |
| `7f01bfd92a8b` | humpback-b + orca-cape-elizabeth | humpback-b, orca-cape-elizabeth | yes |
| `b5dd24698bd0` | humpback-b + orca-montague | humpback-b, orca-montague | yes |
| `0c39cacea2b2` | humpback-b + orca-orcasound-lab | humpback-b, orca-orcasound-lab | yes |
| `771d756beb3b` | humpback-b + orca-tekteksen | humpback-b, orca-tekteksen | yes |
| `cdbe2d8268e5` | humpback-b + right-whale-stellwagen | humpback-b, right-whale-stellwagen | yes |
| `402396b9c602` | humpback-b + rough-toothed-dolphin-kure | humpback-b, rough-toothed-dolphin-kure | yes |
| `7209e7d2efe7` | humpback-b + sperm-a | humpback-b, sperm-a | yes |
| `ac4cdcaf556d` | humpback-b + spinner-dolphin-palmyra | humpback-b, spinner-dolphin-palmyra | yes |
| `6b05ec3fbcd7` | humpback-b + striped-dolphin-nwhi | humpback-b, striped-dolphin-nwhi | yes |
| `d4ce82805bd7` | humpback-cape-elizabeth + minke-whale-niihau | humpback-cape-elizabeth, minke-whale-niihau | yes |
| `284f0205f918` | humpback-cape-elizabeth + orca-bush-point | humpback-cape-elizabeth, orca-bush-point | yes |
| `534e7e7fb453` | humpback-cape-elizabeth + orca-cape-elizabeth | humpback-cape-elizabeth, orca-cape-elizabeth | yes |
| `aa045663ccb5` | humpback-cape-elizabeth + orca-montague | humpback-cape-elizabeth, orca-montague | yes |
| `e60ab1116b08` | humpback-cape-elizabeth + orca-orcasound-lab | humpback-cape-elizabeth, orca-orcasound-lab | yes |
| `02d41963cd1c` | humpback-cape-elizabeth + orca-tekteksen | humpback-cape-elizabeth, orca-tekteksen | yes |
| `1614fab6ab77` | humpback-cape-elizabeth + right-whale-stellwagen | humpback-cape-elizabeth, right-whale-stellwagen | yes |
| `b530512cfb5c` | humpback-cape-elizabeth + rough-toothed-dolphin-kure | humpback-cape-elizabeth, rough-toothed-dolphin-kure | yes |
| `27e6317399a7` | humpback-cape-elizabeth + sperm-a | humpback-cape-elizabeth, sperm-a | yes |
| `1c468ce3dc89` | humpback-cape-elizabeth + spinner-dolphin-palmyra | humpback-cape-elizabeth, spinner-dolphin-palmyra | yes |
| `c562ad5fe141` | humpback-cape-elizabeth + striped-dolphin-nwhi | humpback-cape-elizabeth, striped-dolphin-nwhi | yes |
| `ab0adfc9b3d0` | Killer whale & Dolphin & Sperm whale ensemble | orca-tekteksen, orca-cape-elizabeth, orca-bush-point, orca-montague, dolphin-a, sperm-a | yes |
| `e54d6b424adb` | Killer whale & Humpback ensemble | orca-cape-elizabeth, humpback-cape-elizabeth | yes |
| `ab79eb22c96e` | minke-whale-niihau + orca-bush-point | minke-whale-niihau, orca-bush-point | yes |
| `602f6e35faa9` | minke-whale-niihau + orca-cape-elizabeth | minke-whale-niihau, orca-cape-elizabeth | yes |
| `8d498400111b` | minke-whale-niihau + orca-montague | minke-whale-niihau, orca-montague | yes |
| `a4ab4f52412f` | minke-whale-niihau + orca-orcasound-lab | minke-whale-niihau, orca-orcasound-lab | yes |
| `b55170455480` | minke-whale-niihau + orca-tekteksen | minke-whale-niihau, orca-tekteksen | yes |
| `4d0a15f07641` | minke-whale-niihau + right-whale-stellwagen | minke-whale-niihau, right-whale-stellwagen | yes |
| `e72327bac38b` | minke-whale-niihau + rough-toothed-dolphin-kure | minke-whale-niihau, rough-toothed-dolphin-kure | yes |
| `a9e7c37e05f6` | minke-whale-niihau + sperm-a | minke-whale-niihau, sperm-a | yes |
| `422ef6aefb39` | minke-whale-niihau + spinner-dolphin-palmyra | minke-whale-niihau, spinner-dolphin-palmyra | yes |
| `9fdd150fc04e` | minke-whale-niihau + striped-dolphin-nwhi | minke-whale-niihau, striped-dolphin-nwhi | yes |
| `05e9f1c6ade1` | orca-bush-point + orca-cape-elizabeth | orca-bush-point, orca-cape-elizabeth | yes |
| `8e64bee37698` | orca-bush-point + orca-montague | orca-bush-point, orca-montague | yes |
| `7e6c89b9e594` | orca-bush-point + orca-orcasound-lab | orca-bush-point, orca-orcasound-lab | yes |
| `d6ad2d00cb86` | orca-bush-point + orca-tekteksen | orca-bush-point, orca-tekteksen | yes |
| `f9d7956e8764` | orca-bush-point + right-whale-stellwagen | orca-bush-point, right-whale-stellwagen | yes |
| `f642ba4d7d19` | orca-bush-point + rough-toothed-dolphin-kure | orca-bush-point, rough-toothed-dolphin-kure | yes |
| `e98c2420598f` | orca-bush-point + sperm-a | orca-bush-point, sperm-a | yes |
| `fed874683d63` | orca-bush-point + spinner-dolphin-palmyra | orca-bush-point, spinner-dolphin-palmyra | yes |
| `5558e5506101` | orca-bush-point + striped-dolphin-nwhi | orca-bush-point, striped-dolphin-nwhi | yes |
| `6559aa1d360a` | orca-cape-elizabeth + dolphin-a + orca-montague | orca-cape-elizabeth, dolphin-a, orca-montague | yes |
| `0b8ffc342e5a` | orca-cape-elizabeth + orca-montague | orca-cape-elizabeth, orca-montague | yes |
| `9bdebc8e7c9d` | orca-cape-elizabeth + orca-orcasound-lab | orca-cape-elizabeth, orca-orcasound-lab | yes |
| `29cb7ab72422` | orca-cape-elizabeth + orca-tekteksen | orca-cape-elizabeth, orca-tekteksen | yes |
| `a1848dcfc80b` | orca-cape-elizabeth + right-whale-stellwagen | orca-cape-elizabeth, right-whale-stellwagen | yes |
| `25d664ff11f8` | orca-cape-elizabeth + rough-toothed-dolphin-kure | orca-cape-elizabeth, rough-toothed-dolphin-kure | yes |
| `1b3da8f51583` | orca-cape-elizabeth + sperm-a | orca-cape-elizabeth, sperm-a | yes |
| `1f6bfc6b99a0` | orca-cape-elizabeth + spinner-dolphin-palmyra | orca-cape-elizabeth, spinner-dolphin-palmyra | yes |
| `46ee914d9d47` | orca-cape-elizabeth + striped-dolphin-nwhi | orca-cape-elizabeth, striped-dolphin-nwhi | yes |
| `d1bf3be4f634` | orca-montague + orca-orcasound-lab | orca-montague, orca-orcasound-lab | yes |
| `9bbae4c9b661` | orca-montague + orca-tekteksen | orca-montague, orca-tekteksen | yes |
| `b1c4f5390030` | orca-montague + right-whale-stellwagen | orca-montague, right-whale-stellwagen | yes |
| `5c6541da3f78` | orca-montague + rough-toothed-dolphin-kure | orca-montague, rough-toothed-dolphin-kure | yes |
| `905faa247aeb` | orca-montague + sperm-a | orca-montague, sperm-a | yes |
| `9617abb1d770` | orca-montague + spinner-dolphin-palmyra | orca-montague, spinner-dolphin-palmyra | yes |
| `d8ef09133627` | orca-montague + striped-dolphin-nwhi | orca-montague, striped-dolphin-nwhi | yes |
| `868da87ff467` | orca-orcasound-lab + orca-tekteksen | orca-orcasound-lab, orca-tekteksen | yes |
| `a80025fde7c8` | orca-orcasound-lab + right-whale-stellwagen | orca-orcasound-lab, right-whale-stellwagen | yes |
| `611d79809a5d` | orca-orcasound-lab + rough-toothed-dolphin-kure | orca-orcasound-lab, rough-toothed-dolphin-kure | yes |
| `475d3f1bab69` | orca-orcasound-lab + sperm-a | orca-orcasound-lab, sperm-a | yes |
| `3f5367f58652` | orca-orcasound-lab + spinner-dolphin-palmyra | orca-orcasound-lab, spinner-dolphin-palmyra | yes |
| `593b1cf88608` | orca-orcasound-lab + striped-dolphin-nwhi | orca-orcasound-lab, striped-dolphin-nwhi | yes |
| `25d0326add41` | orca-tekteksen + right-whale-stellwagen | orca-tekteksen, right-whale-stellwagen | yes |
| `abd7044575bd` | orca-tekteksen + rough-toothed-dolphin-kure | orca-tekteksen, rough-toothed-dolphin-kure | yes |
| `5483f18993dc` | orca-tekteksen + sperm-a | orca-tekteksen, sperm-a | yes |
| `5c6f80998dea` | orca-tekteksen + spinner-dolphin-palmyra | orca-tekteksen, spinner-dolphin-palmyra | yes |
| `0e36b975dcc1` | orca-tekteksen + striped-dolphin-nwhi | orca-tekteksen, striped-dolphin-nwhi | yes |
| `6ecc88ef390a` | Red Sea to Salish Sea | dolphin-a, sperm-a, humpback-cape-elizabeth, orca-tekteksen, humpback-a | yes |
| `5e4b521ec19e` | right-whale-stellwagen + rough-toothed-dolphin-kure | right-whale-stellwagen, rough-toothed-dolphin-kure | yes |
| `fafaa796bd59` | right-whale-stellwagen + sperm-a | right-whale-stellwagen, sperm-a | yes |
| `b86537467ae0` | right-whale-stellwagen + spinner-dolphin-palmyra | right-whale-stellwagen, spinner-dolphin-palmyra | yes |
| `3c5f0dd324bb` | right-whale-stellwagen + striped-dolphin-nwhi | right-whale-stellwagen, striped-dolphin-nwhi | yes |
| `8d0519e2c8c6` | rough-toothed-dolphin-kure + sperm-a | rough-toothed-dolphin-kure, sperm-a | yes |
| `85e7ecd34a57` | rough-toothed-dolphin-kure + spinner-dolphin-palmyra | rough-toothed-dolphin-kure, spinner-dolphin-palmyra | yes |
| `1e68c6b24ecd` | rough-toothed-dolphin-kure + striped-dolphin-nwhi | rough-toothed-dolphin-kure, striped-dolphin-nwhi | yes |
| `ba5bea77119d` | Southern Ocean blue whales | blue-whale-weddell-69s, blue-whale-weddell-59s | yes |
| `884ef0c9055d` | Southern Ocean meets Stellwagen | blue-whale-weddell-59s, right-whale-stellwagen, fin-whale-stellwagen, humpback-cape-elizabeth | yes |
| `c79ca2b67258` | Southern Residents down the Salish Sea | orca-tekteksen, orca-orcasound-lab, orca-bush-point | yes |
| `335c29051afc` | sperm-a + spinner-dolphin-palmyra | sperm-a, spinner-dolphin-palmyra | yes |
| `4409fe456ba6` | sperm-a + striped-dolphin-nwhi | sperm-a, striped-dolphin-nwhi | yes |
| `ed066d93d846` | spinner-dolphin-palmyra + striped-dolphin-nwhi | spinner-dolphin-palmyra, striped-dolphin-nwhi | yes |
| `1f88378ee478` | Stellwagen answers Haro Strait | right-whale-stellwagen, humpback-a | yes |
| `862437f5745b` | Three killer-whale ecotypes | orca-tekteksen, orca-cape-elizabeth, orca-montague | yes |
| `d37737c7b1be` | Three seas | humpback-b, dolphin-a, sperm-a | yes |
| `527cc9dddc35` | Two humpback coasts | humpback-a, humpback-cape-elizabeth | yes |
| `48d9eb707419` | Whistles across three oceans | spinner-dolphin-palmyra, atlantic-spotted-dolphin-mid-atlantic, dolphin-a | yes |
