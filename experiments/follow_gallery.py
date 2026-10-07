"""Listening page for music that follows the animal phrase: Input → Schema → Output.

Every stem plays on its own or over the recording, on one playhead. Spectrograms
carry the measured events, so a listener can see where the guide's onsets and
contours sit in each output; the numbers next to them come from evaluation.json.
"""

import json
from pathlib import Path
import subprocess

from .data import Layout, read_json
from .follow import directories, study_ids
from .follow_metrics import frames, load_mono

MUSIC_BAND = (40.0, 4000.0)
TRACKS = [
    ("animal", "input", "Recording", "The animal sound, unchanged except for one playback gain."),
    ("guide", "schema", "Measured guide", "Measured events in a declared register and instrument."),
    ("perturbed", "schema", "Perturbed guide", "Event order mirrored in time, contours inverted; all else fixed."),
    ("response", "output", "Deterministic response", "No model: pad, bass or drum placed on the guide's events."),
    ("response-perturbed", "output", "Response to the perturbed guide", "The same rules applied to the perturbed events."),
    ("ace-prompt", "output", "ACE-Step · prompt only", "Caption and seed only, no source audio."),
    ("ace-raw", "output", "ACE-Step · raw recording", "Lego track generated in the context of the recording."),
    ("ace-guide", "output", "ACE-Step · measured guide", "Lego track generated in the context of the guide."),
    ("ace-perturbed", "output", "ACE-Step · perturbed guide", "Lego track generated in the context of the perturbed guide."),
    ("ace-cover-raw", "output", "ACE-Step cover · raw recording", "The recording transformed toward the caption (cover strength 0.6)."),
    ("ace-cover-guide", "output", "ACE-Step cover · measured guide", "The guide transformed toward the caption (cover strength 0.6)."),
    ("ace-cover-perturbed", "output", "ACE-Step cover · perturbed guide", "The perturbed guide transformed toward the caption."),
]


def spectrogram(audio, rate: int, band, path: Path, px_per_s: int = 40, height: int = 140):
    """Log-frequency spectrogram image: one column per 1/px_per_s seconds, 70 dB range, magma."""
    import matplotlib
    import numpy as np
    from PIL import Image

    n_fft = 4096 if band[0] < 500 else 1024
    magnitude, frequencies = frames(audio, rate, px_per_s, n_fft)
    rows = band[0] * (band[1] / band[0]) ** np.linspace(1, 0, height)
    level = 20 * np.log10(magnitude + 1e-9)
    image = np.stack([np.interp(rows, frequencies, column) for column in level], axis=1)
    top = np.percentile(image, 99.7)
    scaled = np.clip((image - (top - 70)) / 70, 0, 1)
    rgb = (matplotlib.colormaps["magma"](scaled)[..., :3] * 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(path, quality=82, method=6)


def mp3(wav: Path, target: Path):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "96k", str(target)], check=True)


def listening(wav: Path, band, rate: int, image: bool = True):
    """MP3 and WebP spectrogram next to a WAV, rebuilt only when the WAV is newer."""
    targets = [wav.with_suffix(".mp3")] + ([wav.with_suffix(".webp")] if image else [])
    for target in targets:
        if target.exists() and target.stat().st_mtime >= wav.stat().st_mtime:
            continue
        if target.suffix == ".mp3":
            mp3(wav, target)
        else:
            spectrogram(load_mono(wav, rate), rate, band, target)
    return targets


def thin(times, values, limit: int = 40):
    step = max(1, len(times) // limit)
    points = list(zip(times[::step], values[::step]))
    if (times[-1], values[-1]) != points[-1]:
        points.append((times[-1], values[-1]))
    return [[round(t, 3), round(v, 1)] for t, v in points]


def event_data(events):
    out = []
    for e in events:
        if e["kind"] == "click":
            out.append({"k": "c", "t": round(e["time_s"], 4), "g": e["group"]})
        else:
            out.append({"k": "t", "s": round(e["start_s"], 3), "e": round(e["end_s"], 3), "l": e["label"], "c": thin(e["time_s"], e["hz"])})
    return out


def score_data(result):
    own = result["scores"][result["own_reference"]]
    other = result["own_reference"].rsplit("/", 1)
    alternative = f"{other[0]}/{'guide' if other[1] == 'perturbed' else 'perturbed'}"
    pick = lambda value, *keys: None if value is None else {k: round(value[k], 3) for k in keys}
    return {"timing": pick(own["timing"], "z", "value", "p"), "events": pick(own.get("events"), "value", "null_mean", "z", "detected", "reference"),
            "pitch": pick(own.get("pitch"), "z", "value", "null_mean"), "alt_timing_z": round(result["scores"][alternative]["timing"]["z"], 2),
            "alternative": alternative, "rank": result["own_rank_among_species"], "of": result["species_references"],
            "leak": result["leakage"] or None, "envelope": result["envelope"], "envelope_rate": result["envelope_rate_hz"]}


def write_page(layout: Layout, config: dict):
    interim, output = directories(layout)
    prepared = read_json(interim / "prepared.json")
    prepared["sources"] = [s for s in prepared["sources"] if s["id"] in study_ids(config)]
    evaluation = read_json(interim / "evaluation.json")
    rate = prepared["sample_rate"]
    results = {(r["source"], r["output"]): r for r in evaluation["results"]}
    downloads = config["downloads"]
    sources = []
    for item in prepared["sources"]:
        species = config["species"][item["species"]]
        tracks = []
        for name, stage, title, caption in TRACKS:
            wav = output / item["id"] / f"{name}.wav"
            if not wav.exists():
                continue
            band = species["spectrogram_hz"] if name == "animal" else MUSIC_BAND
            audio_file, image = listening(wav, band, rate)
            track = {"name": name, "stage": stage, "title": title, "caption": caption, "band": list(band),
                     "audio": f"{item['id']}/{audio_file.name}", "image": f"{item['id']}/{image.name}"}
            if (item["id"], name) in results:
                track["score"] = score_data(results[(item["id"], name)])
                job = results[(item["id"], name)]["job"]
                if job:
                    track["job"] = {k: job[k] for k in ("task", "track", "instruction", "caption", "seed", "inference_steps", "guidance_scale", "seconds") if k in job}
            tracks.append(track)
        provenance = item["provenance"]
        if provenance.get("file") in downloads:
            credit = downloads[provenance["file"]]
            origin = {"credit": credit["credit"], "license": credit.get("license", ""), "url": credit["url"],
                      "excerpt": f"{provenance['start_s']:.1f}–{provenance['start_s'] + item['duration_s']:.1f} s of {Path(provenance['file']).name}"}
        elif "file" in provenance:  # fetched earlier by `art long-forms`
            origin = {"credit": "OpenWhistle pretraining corpus, review sample (dolphinteam on Hugging Face).",
                      "license": "No license declared on the dataset card; research use.",
                      "url": "https://huggingface.co/datasets/dolphinteam/OpenWhistle-Pretraining",
                      "excerpt": f"first {item['duration_s']:.0f} s of {Path(provenance['file']).name} (96 kHz)"}
        else:
            origin = {"credit": "Dominica Sperm Whale Project codas (orrp/DSWP, accompanying WhAM, NeurIPS 2025).", "license": "CC BY 4.0",
                      "url": "https://huggingface.co/datasets/orrp/DSWP",
                      "excerpt": f"rows {provenance['clips'][0]['row_index']}–{provenance['clips'][-1]['row_index']}, {provenance['gap_s']} s gaps inserted",
                      "clips": [[c["start_s"], c["end_s"], c["row_index"]] for c in provenance["clips"]]}
        sources.append({"id": item["id"], "species": item["species"], "title": item["title"], "note": item["note"],
                        "duration": round(item["duration_s"], 3), "shift": item["register_shift_octaves"], "counts": item["counts"],
                        "instrument": item["instrument"]["name"], "caption": species["caption"], "lego_track": species["lego_track"],
                        "material": species["material"], "origin": origin, "events": event_data(item["events"]),
                        "perturbed": event_data(item["perturbed_events"]), "tracks": tracks})
    matrix = {}
    for name in dict.fromkeys(s["species"] for s in sources):
        same = [s["id"] for s in sources if s["species"] == name]
        cols = [f"{s}/{v}" for s in same for v in ("guide", "perturbed")]
        rows = [(s, o) for s in same for o, *_ in TRACKS if (s, o) in results]
        matrix[name] = {"cols": cols, "rows": [f"{s} · {o}" for s, o in rows], "own": [results[r]["own_reference"] for r in rows],
                        "z": [[round(results[r]["scores"][c]["timing"]["z"], 2) for c in cols] for r in rows]}
    data = {"sources": sources, "matrix": matrix, "verdicts": evaluation["verdicts"], "registration": {k: v for k, v in evaluation["predictions"].items() if not k.startswith("P")},
            "evaluated": evaluation["created_at_utc"], "ace": evaluation.get("ace", {}), "ace_config": {k: config["ace_step"][k] for k in ("repository", "model", "model_repo", "model_revision")},
            "perturbation": config["perturbation"], "response": config["response"]["interpretation"], "metrics": evaluation["metrics"]}
    template = (Path(__file__).with_name("follow_page.html")).read_text(encoding="utf-8")
    page = template.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")).replace("</", "<\\/"))
    # page.html is the publishable fragment; index.html wraps it for opening from disk.
    (output / "page.html").write_text(page, encoding="utf-8")
    path = output / "index.html"
    path.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
                    + page + "</body></html>\n", encoding="utf-8")
    return path
