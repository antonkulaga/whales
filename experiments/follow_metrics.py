"""Does the music follow its phrase? Agreement with a guide, against circular-shift nulls.

Timing: correlation between the output's spectral-flux onset envelope and
Gaussian bumps at the guide's event onsets. Events: F1 of detected output
onsets within ±tolerance. Pitch: transposition-invariant pitch-class agreement
inside tonal events. Each score is compared with the same score after circular
time shifts of at least `min_null_shift_s`, so z ≈ 0 means "no more aligned than
the same music at a wrong time". Swapped and perturbed guides answer whether
the alignment belongs to this phrase or to music in general.
"""

from pathlib import Path

from .data import Layout, now, read_json, write_json
from .follow import CONDITIONS, contour_at, directories, resample, study_ids

OUTPUTS = {"response": "guide", "response-perturbed": "perturbed", **{f"ace-{c}": ("perturbed" if c.endswith("perturbed") else "guide") for c in CONDITIONS}}


def load_mono(path: Path, rate: int):
    import soundfile as sf

    samples, native = sf.read(path, dtype="float64", always_2d=True)
    return resample(samples.mean(axis=1), native, rate)


def frames(x, rate: int, frame_rate: int, n_fft: int):
    """Centered Hann frames at k / frame_rate seconds, magnitude spectra and their frequencies."""
    import numpy as np

    hop = rate // frame_rate
    padded = np.pad(x, (n_fft // 2, n_fft // 2 + hop))
    count = len(x) // hop
    windows = np.lib.stride_tricks.sliding_window_view(padded, n_fft)[::hop][:count]
    return np.abs(np.fft.rfft(windows * np.hanning(n_fft), axis=1)), np.fft.rfftfreq(n_fft, 1 / rate)


def onset_envelope(x, rate: int, frame_rate: int, band=(30.0, 8000.0)):
    import numpy as np

    magnitude, frequencies = frames(x, rate, frame_rate, 2048)
    keep = (frequencies >= band[0]) & (frequencies <= band[1])
    level = np.log1p(1000 * magnitude[:, keep] / (magnitude[:, keep].max() + 1e-12))
    flux = np.concatenate([[0.0], np.maximum(0, np.diff(level, axis=0)).sum(axis=1)])
    return (flux - flux.mean()) / (flux.std() + 1e-12)


def bumps(times, n: int, frame_rate: int, sigma_s: float):
    import numpy as np

    grid = np.arange(n) / frame_rate
    out = np.zeros(n)
    for t in times:
        out += np.exp(-.5 * ((grid - t) / sigma_s) ** 2)
    return out


def shifts(n: int, frame_rate: int, min_shift_s: float, step: int = 5):
    lowest = round(min_shift_s * frame_rate)
    return range(lowest, n - lowest + 1, step)


def null_summary(observed: float, null):
    import numpy as np

    null = np.asarray(null)
    sd = float(null.std()) or 1e-12
    return {"value": float(observed), "null_mean": float(null.mean()), "null_sd": float(null.std()),
            "z": float((observed - null.mean()) / sd), "p": float((1 + (null >= observed).sum()) / (1 + len(null)))}


def timing(env, onsets, frame_rate: int, sigma_s: float, min_shift_s: float):
    """Pearson r between onset envelope and onset bumps, versus circularly shifted envelopes."""
    import numpy as np

    reference = bumps(onsets, len(env), frame_rate, sigma_s)
    if not reference.any():
        return None
    reference = (reference - reference.mean()) / reference.std()
    r = lambda e: float(np.mean(e * reference))
    return null_summary(r(env), [r(np.roll(env, k)) for k in shifts(len(env), frame_rate, min_shift_s)])


def peak_times(env, frame_rate: int, min_gap_s: float = .08):
    from scipy.signal import find_peaks

    found, _ = find_peaks(env, height=1.0, distance=max(1, round(min_gap_s * frame_rate)))
    return found / frame_rate


def f1(detected, reference, tolerance: float):
    """Greedy one-to-one matching in time order."""
    if not len(detected) or not len(reference):
        return 0.0
    matched, used = 0, set()
    for t in reference:
        best = min((abs(d - t), i) for i, d in enumerate(detected) if i not in used) if len(used) < len(detected) else None
        if best and best[0] <= tolerance:
            matched += 1
            used.add(best[1])
    return 2 * matched / (len(detected) + len(reference))


def events(env, onsets, frame_rate: int, tolerance: float, min_shift_s: float):
    import numpy as np

    detected = peak_times(env, frame_rate)
    duration = len(env) / frame_rate
    null = [f1(np.sort((detected + k / frame_rate) % duration), onsets, tolerance) for k in shifts(len(env), frame_rate, min_shift_s, 10)]
    return null_summary(f1(detected, onsets, tolerance), null) | {"detected": len(detected), "reference": len(onsets)}


def chroma(x, rate: int, frame_rate: int, band):
    """12 × frames pitch-class energy from 8192-point spectra, unit length per frame."""
    import numpy as np

    magnitude, frequencies = frames(x, rate, frame_rate, 8192)
    keep = (frequencies >= band[0]) & (frequencies <= band[1])
    classes = np.round(12 * np.log2(frequencies[keep] / 440) + 69).astype(int) % 12
    power = magnitude[:, keep] ** 2
    out = np.zeros((12, len(magnitude)))
    for pitch_class in range(12):
        out[pitch_class] = power[:, classes == pitch_class].sum(axis=1)
    return out / (np.linalg.norm(out, axis=0, keepdims=True) + 1e-12)


def guide_chroma(event_list, shift: int, n: int, frame_rate: int):
    """Pitch classes of the rendered guide contour, split between the two nearest classes."""
    import numpy as np

    out = np.zeros((12, n))
    for event in event_list:
        if event["kind"] != "tonal":
            continue
        k = np.arange(max(0, round(event["start_s"] * frame_rate)), min(n, round(event["end_s"] * frame_rate)))
        if not len(k):
            continue
        midi = 12 * np.log2(contour_at(event, k / frame_rate) * 2.0 ** shift / 440) + 69
        low = np.floor(midi).astype(int)
        upper = midi - low
        np.add.at(out, (low % 12, k), 1 - upper)
        np.add.at(out, ((low + 1) % 12, k), upper)
    return out / (np.linalg.norm(out, axis=0, keepdims=True) + 1e-12)


def pitch(output_chroma, reference_chroma, min_shift_s: float, frame_rate: int):
    """Mean cosine inside tonal events at the best single transposition, versus shifted outputs."""
    import numpy as np

    voiced = reference_chroma.sum(axis=0) > 0
    if voiced.sum() < frame_rate // 2:
        return None
    reference = reference_chroma[:, voiced]
    rotations = np.stack([np.roll(reference, r, axis=0) for r in range(12)])

    def best(candidate):
        return float((rotations * candidate[:, voiced][None]).sum(axis=1).mean(axis=1).max())

    observed = best(output_chroma)
    n = output_chroma.shape[1]
    return null_summary(observed, [best(np.roll(output_chroma, k, axis=1)) for k in shifts(n, frame_rate, min_shift_s, 10)])


def leakage(output, source, rate: int, max_lag_s: float = .1):
    """Peak normalized cross-correlation within ±max_lag: does the output contain the source waveform?"""
    import numpy as np
    from scipy.signal import correlate

    n = min(len(output), len(source))
    a, b = output[:n] - output[:n].mean(), source[:n] - source[:n].mean()
    full = correlate(a, b, mode="full", method="fft")
    middle, lag = n - 1, round(max_lag_s * rate)
    return float(np.max(np.abs(full[middle - lag:middle + lag + 1])) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def evaluate(layout: Layout, config: dict, predictions: dict):
    interim, output = directories(layout)
    prepared = read_json(interim / "prepared.json")
    prepared["sources"] = [s for s in prepared["sources"] if s["id"] in study_ids(config)]
    ace = read_json(interim / "ace-results.json") if (interim / "ace-results.json").exists() else {"jobs": {}}
    m, rate = config["metrics"], prepared["sample_rate"]
    fr = m["frame_rate_hz"]
    sources = {item["id"]: item for item in prepared["sources"]}
    references = {}
    for item in prepared["sources"]:
        for variant, key in (("guide", "events"), ("perturbed", "perturbed_events")):
            references[f"{item['id']}/{variant}"] = {"source": item["id"], "variant": variant, "species": item["species"],
                                                     "events": item[key], "onsets": item["onsets_s" if variant == "guide" else "perturbed_onsets_s"],
                                                     "shift": item["register_shift_octaves"], "tonal": item["events"][0]["kind"] == "tonal"}
    results = []
    for item in prepared["sources"]:
        stems = {name: output / item["id"] / f"{name}.wav" for name in OUTPUTS}
        source_audio = {name: load_mono(output / item["stems"][name], rate) for name in ("animal", "guide", "perturbed")}
        for name, own_variant in OUTPUTS.items():
            if not stems[name].exists():
                continue
            audio = load_mono(stems[name], rate)
            env = onset_envelope(audio, rate, fr)
            duration = len(env) / fr
            out_chroma = chroma(audio, rate, fr, m["chroma_hz"]) if references[f"{item['id']}/guide"]["tonal"] else None
            scores = {}
            for key, ref in references.items():
                onsets = [t for t in ref["onsets"] if t < duration]
                entry = {"timing": timing(env, onsets, fr, m["onset_sigma_s"], m["min_null_shift_s"])}
                if ref["species"] == item["species"]:
                    entry["events"] = events(env, onsets, fr, m["tolerance_s"], m["min_null_shift_s"])
                    if out_chroma is not None:
                        entry["pitch"] = pitch(out_chroma, guide_chroma(ref["events"], ref["shift"], len(env), fr), m["min_null_shift_s"], fr)
                scores[key] = entry
            own = f"{item['id']}/{own_variant}"
            same = [k for k, ref in references.items() if ref["species"] == item["species"]]
            ranked = sorted(same, key=lambda k: -(scores[k]["timing"] or {"z": -1e9})["z"])
            job = ace["jobs"].get(f"{item['id']}-{name[4:]}") if name.startswith("ace-") else None
            leak = {}
            if job and job["src_audio"]:
                leak = {"source_stem": Path(job["src_audio"]).stem, "value": leakage(audio, source_audio[Path(job["src_audio"]).stem], rate)}
            results.append({"source": item["id"], "species": item["species"], "output": name, "own_reference": own,
                            "own_rank_among_species": ranked.index(own) + 1, "species_references": len(same),
                            "scores": scores, "leakage": leak, "job": job,
                            "envelope": [round(float(v), 2) for v in env[::2]], "envelope_rate_hz": fr / 2})
            own_score = scores[own]
            pitch_z = f"{own_score['pitch']['z']:+.2f}" if own_score.get("pitch") else "—"
            print(f"{item['id']:11s} {name:19s} timing z {own_score['timing']['z']:+6.2f}  events F1 {own_score['events']['value']:.2f} "
                  f"(null {own_score['events']['null_mean']:.2f})  pitch z {pitch_z}  "
                  f"rank {ranked.index(own) + 1}/{len(same)}" + (f"  leak {leak['value']:.2f}" if leak else ""), flush=True)
    verdicts = judge(results, sources, predictions)
    report = {"created_at_utc": now(), "config_sha256": config["config_sha256"], "metrics": m, "predictions": predictions,
              "verdicts": verdicts, "results": results, "ace": {k: v for k, v in ace.items() if k != "jobs"}}
    write_json(interim / "evaluation.json", report)
    return interim / "evaluation.json"


def judge(results: list[dict], sources: dict, predictions: dict):
    """Each registered prediction → supported / not supported / untested, with the numbers behind it."""
    def find(source, output):
        return next((r for r in results if r["source"] == source and r["output"] == output), None)

    def z(result, reference, metric="timing"):
        value = result["scores"][reference].get(metric)
        return None if value is None else value["z"]

    verdicts = {}
    rows = [(s, find(s, "response"), find(s, "response-perturbed")) for s in sources]
    p1 = [(s, z(a, f"{s}/guide"), z(b, f"{s}/perturbed") - z(b, f"{s}/guide")) for s, a, b in rows if a and b]
    verdicts["P1"] = {"supported": bool(p1) and all(own >= 3 and gap > 0 for _, own, gap in p1),
                      "detail": [{"source": s, "timing_z": own, "perturbed_minus_original_z": gap} for s, own, gap in p1]}
    prompt = [(s, z(r, f"{s}/guide")) for s in sources if (r := find(s, "ace-prompt"))]
    verdicts["P2"] = {"supported": all(abs(v) < 2 for _, v in prompt) if prompt else None,
                      "detail": [{"source": s, "timing_z": v} for s, v in prompt]}
    species = sorted({sources[s]["species"] for s in sources})
    p3 = []
    for name in species:
        pairs = [(z(g, f"{s}/guide"), z(r, f"{s}/guide")) for s in sources if sources[s]["species"] == name
                 and (g := find(s, "ace-guide")) and (r := find(s, "ace-raw"))]
        if pairs:
            p3.append({"species": name, "guide_mean_z": sum(p[0] for p in pairs) / len(pairs), "raw_mean_z": sum(p[1] for p in pairs) / len(pairs)})
    verdicts["P3"] = {"supported": sum(row["guide_mean_z"] > row["raw_mean_z"] for row in p3) >= 2 if len(p3) == 3 else None, "detail": p3}
    p4 = [(s, r["own_rank_among_species"], r["species_references"]) for s in sources if (r := find(s, "ace-guide"))]
    verdicts["P4"] = {"supported": sum(rank == 1 for _, rank, _ in p4) >= len(p4) / 2 if p4 else None,
                      "detail": [{"source": s, "rank": rank, "of": n} for s, rank, n in p4]}
    p5 = [(s, z(r, f"{s}/perturbed"), z(r, f"{s}/guide")) for s in sources if (r := find(s, "ace-perturbed"))]
    verdicts["P5"] = {"supported": sum(a > b for _, a, b in p5) >= len(p5) / 2 if p5 else None,
                      "detail": [{"source": s, "z_vs_perturbed": a, "z_vs_original": b} for s, a, b in p5]}
    p6 = [(s, z(r, f"{s}/guide")) for s in sources if (r := find(s, "ace-cover-guide"))]
    verdicts["P6"] = {"supported": sum(v >= 3 for _, v in p6) >= 4 if len(p6) == 6 else None,
                      "detail": [{"source": s, "timing_z": v} for s, v in p6]}
    p7 = [(s, z(r, f"{s}/perturbed"), z(r, f"{s}/guide")) for s in sources if (r := find(s, "ace-cover-perturbed"))]
    verdicts["P7"] = {"supported": sum(a > b for _, a, b in p7) >= 4 if len(p7) == 6 else None,
                      "detail": [{"source": s, "z_vs_perturbed": a, "z_vs_original": b} for s, a, b in p7]}
    for key in verdicts:
        verdicts[key]["prediction"] = predictions[key]
    caveats(verdicts, results)
    return verdicts


LEAK = .15  # waveform correlation above this means the output partly copies its conditioning audio
OUTPUTS_BY_PREDICTION = {"P2": ["ace-prompt"], "P3": ["ace-guide", "ace-raw"], "P4": ["ace-guide"], "P5": ["ace-perturbed"],
                         "P6": ["ace-cover-guide"], "P7": ["ace-cover-perturbed"]}


def caveats(verdicts: dict, results: list[dict]):
    """Reading notes that do not change the registered criteria: copied sources and comparisons of two weak scores."""
    for key in verdicts:
        outputs, notes = OUTPUTS_BY_PREDICTION.get(key, []), []
        leaked = [f"{r['source']} {r['output']} ({r['leakage']['value']:.2f})" for r in results
                  if r["output"] in outputs and r["leakage"] and r["leakage"]["value"] >= LEAK]
        if leaked:
            notes.append(f"Partly copies its conditioning audio (waveform correlation ≥ {LEAK}): " + ", ".join(leaked) + ".")
        detail = verdicts[key]["detail"]
        pairs = [(row.get("species", row.get("source")), row[a], row[b]) for row in detail
                 for a, b in (("guide_mean_z", "raw_mean_z"), ("z_vs_perturbed", "z_vs_original")) if a in row]
        weak = [name for name, a, b in pairs if max(a, b) < 2]
        if weak:
            notes.append(f"Neither compared score reaches z = 2 for {', '.join(weak)}; the ordering there is within noise.")
        verdicts[key]["caveats"] = notes
