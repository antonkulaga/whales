# AWI Ocean Acoustics recordings on PANGAEA

**Antarctic blue whales and Arctic bowhead whales from the polar moorings of the Alfred Wegener
Institute, seated in the orchestra next to the DCLDE sources.**

Checked **8 October 2026** · Loader: [`experiments/follow_pangaea.py`](../experiments/follow_pangaea.py) ·
Method: [Follow the phrase](follow-the-phrase.md)

The AWI Ocean Acoustics Group (Ilse Van Opzeeland, Olaf Boebel, Karolin Thomisch and colleagues)
records the polar oceans with moored hydrophones. These are the HAFOS moorings in the Weddell Sea
and the FRAM observatory in Fram Strait. Ilse Van Opzeeland also leads the
[Marine Acoustic Underwater Diversity (MAUD)](https://hifmb.de/research/working-groups/marine-acoustic-underwater-diversity-maud/)
group at HIFMB. The group publishes the raw recordings on PANGAEA under CC-BY-4.0, together with
its own label tables for some recorders. [OPUS](https://opus.aq) is AWI's listening portal for the
same data.

## Sources in the orchestra

| Source id | Species | Where and when | Recording | Labels |
|---|---|---|---|---|
| `blue-whale-weddell-69s` | Antarctic blue whale | Weddell Sea, 69.0°S 0.1°W (HAFOS mooring AWI232-11), 14 Jan 2013 | [PANGAEA 973160](https://doi.org/10.1594/PANGAEA.973160) | Z-call detections with received level, [PANGAEA 960121](https://doi.org/10.1594/PANGAEA.960121) |
| `blue-whale-weddell-59s` | Antarctic blue whale | Southern Ocean, 59.0°S 0.1°E (HAFOS mooring AWI227-12), 6 May 2013 | [PANGAEA 966612](https://doi.org/10.1594/PANGAEA.966612) | Z-call detections with received level, [PANGAEA 960031](https://doi.org/10.1594/PANGAEA.960031) |
| `bowhead-fram-strait-f16` | Bowhead whale | Fram Strait, 78.8°N 0.4°E (FRAM mooring F16-9), 11 Nov 2012 | [PANGAEA 967557](https://doi.org/10.1594/PANGAEA.967557) | Hourly presence, [PANGAEA 945331](https://doi.org/10.1594/PANGAEA.945331) |
| `bowhead-fram-strait-f5` | Bowhead whale | Fram Strait, 79.0°N 5.7°E (FRAM mooring F5-17), 22 Nov 2016 | [PANGAEA 956286](https://doi.org/10.1594/PANGAEA.956286) | Hourly presence, [PANGAEA 945392](https://doi.org/10.1594/PANGAEA.945392); song types heard that day, [PANGAEA 945404](https://doi.org/10.1594/PANGAEA.945404) |

Input → Schema → Output for each source:

- **Antarctic blue whales.** *Input:* 30 s holding one complete Z-call from each of two singers,
  each of whom called every ~69 s. AWI's automated detector logged them at 115 and 120 dB re 1 µPa.
  A single Z-call lasts 18–25 s, so 30 s holds exactly one; staggering the two sites in a piece
  brings back some of the song's rhythm. *Schema:* the logged time becomes a call window from 16 s
  before to 10 s after it (the log marks the downsweep, not the start). That window is trimmed to
  where 17.5–29 Hz rises 6 dB above the band's median over the whole 10-minute recording; a 30 s
  window is mostly call, so its own median is not the background. The pitch contour is then
  measured inside the call and smoothed over 0.5 s, which suits a call that changes over seconds. *Output:* one measured contour per site, a ~26.5 Hz tone falling to
  ~18.5 Hz, played two to three octaves up by the organ guide.
- **Bowhead whales.** *Input:* 30 s of song from each of two Fram Strait moorings, in hours in
  which AWI's tables log bowhead whales. On 22 Nov 2016 AWI's repertoire analysis lists song types
  1.2, 2.1, 3.1, 3.2 and 3.3; which one sings in the window is not labelled. *Schema:* a presence
  table names no individual calls, so notes are measured from the waveform in 330–1500 Hz. A 0.5 s
  minimum note length and a 14 dB tonality threshold keep out mooring noise and the broadband
  pulses above 1 kHz at F5-17. *Output:* 8 downswept notes (2012; about 550 to 380 Hz, a phrase
  repeating every ~5 s) and 13 arched and downswept notes (2016; 350–550 Hz), played an octave down
  by a cello-like guide.

The call windows, trim threshold and analysis bands are our choices. The species labels and
detection times are AWI's. The guides and any ACE-Step output are generated; none of this decodes
meaning.

## Why these recordings

Of about 80 AWI acoustic datasets on PANGAEA, only two families come with published labels for
whales: Antarctic blue whale Z-call detections from ten Weddell Sea recorders, 2008–2013
([bundle 959969](https://doi.org/10.1594/PANGAEA.959969)), and bowhead whale presence and song types
in Fram Strait, 2012–2017 ([series 945330](https://doi.org/10.1594/PANGAEA.945330),
[song types 945404](https://doi.org/10.1594/PANGAEA.945404)). The windows were chosen from those
labels, then checked against spectrograms with the measured contours drawn over them. The Weddell Sea singer calls with the ~69 s regularity of
Antarctic blue whale song. The 2012 recordings from mooring AWI209-6 were left out: there the
detections overlap in a chorus of distant whales.

No dolphin recordings with labels were found. The Antarctic killer whales recorded at the PALAOA
observatory (ecotype C, 26 call types; Schall & Van Opzeeland 2017, *Aquatic Mammals* 43(2)) are
described in a paper, but not published as a labelled excerpt.

## Access

- One dataset per recorder and deployment. Each file is a daily `.tar` of 5- or 10-minute WAV files
  named `YYYYMMDD-HHMMSS_<mooring>_<recorder>.wav`. Sizes run from ~100 MB per day (AURAL,
  32,768 Hz, 4.5 min every 3 h) and ~1.3 GB (Sono.Vault at 5,333 Hz, continuous) to ~11.6 GB
  (48 kHz, continuous).
- Single files download without an account from `https://download.pangaea.de/dataset/<id>/files/<file>`.
  Bulk ZIPs need a PANGAEA login.
- The archives live on tape. The first requests return HTTP 503 with a "loading from tape" page;
  staging took 2–7 minutes per archive here. `fetch_pangaea` retries for up to an hour, streams the
  archive only as far as the wanted file, and keeps only the window. A copy saved as
  `data/interim/pangaea-archives/<dataset>-<file>` is read instead, when present.
- Label tables come from `https://doi.pangaea.de/10.1594/PANGAEA.<id>?format=textfile`, cached in
  `data/input/pangaea/`.

## Adding a source

A source entry in `resources/follow-music.json` with `"kind": "pangaea"` names the audio dataset id,
the daily archive (`file`), the WAV inside it (`member`), `start_s`, `duration_s`, an optional
target `rate` (the species analysis is set in samples), a `call_label`, and a `labels` block:

```json
{"format": "detections", "dataset": 960121, "call_window_s": [-16, 10], "band_hz": [17.5, 29], "trim_db": 6}
{"format": "presence", "dataset": 945331}
```

`main.py follow fetch` cuts the window, and `main.py follow prepare` measures it. The excerpt,
the label rows in the window and the archive it came from are recorded in
`data/input/pangaea-audio/sources.json`.
