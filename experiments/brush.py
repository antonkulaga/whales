"""Human-operated sound brush: keyboard → emitted waveform → measured contour → stroke.

Adapted from CHAT's sound → recognition → consequence loop. A small vocabulary of
designed contours selects a drawing effect; continuous measurements of the same
waveform shape every stroke. The drawing reads only the audio file, so replaying
identical audio reproduces the identical stroke without the keyboard.
"""

import hashlib
import json
import math
from pathlib import Path
import re
import time

from .data import Layout, ROOT, digest, now, read_json, write_json

CONFIG = ROOT / "resources" / "sound-brush.json"
NAMES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
         "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
TOKEN = re.compile(r"^(?P<name>[A-G](?:#|b)?)(?P<octave>-?\d)(?::(?P<duration>[\d.]+))?(?:@(?P<velocity>\d+))?(?:~(?P<bend>[+-]?[\d.]+))?$")


def load_config(path: Path = CONFIG):
    config = read_json(path)
    config["config_sha256"] = digest(path)
    return config


def note_name(note: int):
    return f"{CLASSES[note % 12]}{note // 12 - 1}"


def key_source(note: int, config: dict):
    entry = config["keyboard"]["pitch_classes"].get(CLASSES[note % 12])
    if entry is None:
        raise ValueError(f"Key {note_name(note)} has no sound in the keyboard map")
    return dict(entry)


def parse_phrase(phrase: str, config: dict):
    """`C4:0.8@100~+0.5 rest:0.3 F#4:1.0` → sequential monophonic key events."""
    events, clock = [], 0.0
    for token in phrase.split():
        if token.startswith("rest:"):
            clock += float(token[5:])
            continue
        match = TOKEN.match(token)
        if not match:
            raise ValueError(f"Cannot parse {token!r}; use NOTE:SECONDS[@VELOCITY][~BEND] or rest:SECONDS")
        note = (int(match["octave"]) + 1) * 12 + NAMES[match["name"]]
        duration = float(match["duration"] or 0.8)
        velocity = int(match["velocity"] or 96)
        bend = float(match["bend"] or 0)
        if not (0.05 <= duration <= 4 and 1 <= velocity <= 127 and -1 <= bend <= 1):
            raise ValueError(f"{token}: duration 0.05–4 s, velocity 1–127, bend −1…1")
        events.append({"token": token, "note": note, "name": note_name(note), "start_s": round(clock, 6),
                       "duration_s": duration, "velocity": velocity, "bend": [[0.0, 0.0], [1.0, bend]],
                       "source": key_source(note, config)})
        clock += duration
    if not events:
        raise ValueError("The phrase contains no notes")
    return events


def events_from_messages(messages, config: dict):
    """(seconds, mido message) pairs → key events; pitch-wheel changes become step breakpoints."""
    active, bends, wheel, events = {}, [], {}, []
    for clock, message in messages:
        if message.type == "pitchwheel":
            wheel[message.channel] = message.pitch / 8192
            bends.append((clock, message.channel, wheel[message.channel]))
        elif message.type == "note_on" and message.velocity > 0:
            active[(message.channel, message.note)] = (clock, message.velocity, wheel.get(message.channel, 0.0))
        elif message.type in ("note_off", "note_on") and (message.channel, message.note) in active:
            start, velocity, initial = active.pop((message.channel, message.note))
            duration = min(clock - start, 4.0)
            if duration < 0.05:
                continue
            points = [[0.0, initial]]
            for moment, channel, value in bends:
                if channel == message.channel and start < moment < start + duration:
                    u = (moment - start) / duration
                    points += [[max(0.0, u - 1e-6), points[-1][1]], [u, value]]
            points.append([1.0, points[-1][1]])
            events.append({"token": f"midi:{note_name(message.note)}", "note": message.note, "name": note_name(message.note),
                           "start_s": start, "duration_s": round(duration, 6), "velocity": velocity,
                           "bend": points, "source": key_source(message.note, config)})
    if not events:
        raise ValueError("No complete notes were played")
    first = min(event["start_s"] for event in events)
    for event in events:
        event["start_s"] = round(event["start_s"] - first, 6)
    return sorted(events, key=lambda event: event["start_s"])


def parse_midi(path: Path, config: dict):
    """Note and pitch-wheel events from a MIDI file; mido applies the tempo map."""
    try:
        import mido
    except ImportError as error:
        raise ValueError("Reading MIDI needs: uv run --group art --group viz --group midi ...") from error
    clock, timed = 0.0, []
    for message in mido.MidiFile(path):
        clock += message.time
        timed.append((clock, message))
    return events_from_messages(timed, config)


# --- Emitted sound -----------------------------------------------------------------

def shape(family: dict, u):
    import numpy as np

    kind, extent = family["shape"], family.get("extent_octaves", 0.0)
    if kind == "ramp":
        return extent * u
    if kind == "arch":
        return extent * np.sin(np.pi * u)
    if kind == "wave":
        return extent * np.sin(2 * np.pi * family["cycles"] * u)
    if kind == "flat":
        return np.zeros_like(u)
    raise ValueError(f"Family shape {kind!r} has no contour")


def bend_curve(points, u):
    import numpy as np

    points = np.asarray(points, dtype=float)
    return np.interp(u, points[:, 0], points[:, 1])


def envelope(n: int, rate: int, keyboard: dict):
    import numpy as np

    env = np.ones(n)
    attack = min(round(keyboard["attack_s"] * rate), n // 2)
    release = min(round(keyboard["release_s"] * rate), n // 2)
    env[:attack] *= .5 - .5 * np.cos(np.pi * np.arange(attack) / attack)
    env[n - release:] *= (.5 - .5 * np.cos(np.pi * np.arange(release) / release))[::-1]
    return env


def peak_amplitude(velocity: int, keyboard: dict):
    low, high = keyboard["velocity_peak_dbfs"]
    return 10 ** ((low + (high - low) * velocity / 127) / 20)


def register_factor(note: int, keyboard: dict):
    return 2 ** ((note // 12 - 1 - keyboard["reference_octave"]) * keyboard["register_octaves_per_keyboard_octave"])


def synthesize_note(event: dict, config: dict, recordings: dict):
    import numpy as np

    keyboard, rate = config["keyboard"], config["sample_rate"]
    amplitude = peak_amplitude(event["velocity"], keyboard)
    source = event["source"]
    if "recording" in source:
        clip = recordings[source["recording"]]
        n = min(len(clip), round(event["duration_s"] * rate))
        audio = clip[:n] * amplitude
        if n < len(clip):
            fade = min(round(keyboard["release_s"] * rate), n)
            audio[n - fade:] *= .5 + .5 * np.cos(np.pi * np.arange(fade) / fade)
        return audio
    family = config["families"][source["family"]]
    n = round(event["duration_s"] * rate)
    t = np.arange(n) / rate
    u = t / event["duration_s"]
    bend = bend_curve(event["bend"], u)
    if family["shape"] == "clicks":
        audio, moment = np.zeros(n), 0.0
        offsets = np.arange(-8, 9)
        pulse_t = offsets / rate
        pulse = np.exp(-.5 * (pulse_t / family["pulse_sigma_s"]) ** 2) * np.cos(2 * np.pi * family["pulse_center_hz"] * pulse_t)
        while moment < event["duration_s"] - .005:
            index = round(moment * rate)
            inside = (index + offsets >= 0) & (index + offsets < n)
            audio[index + offsets[inside]] += pulse[inside]
            factor = keyboard["click_bend_rate_factor"] ** float(bend_curve(event["bend"], np.array([moment / event["duration_s"]]))[0])
            moment += 1 / (family["click_rate_hz"] * factor)
        return amplitude * audio / max(np.max(np.abs(audio)), 1e-12)
    low, high = keyboard["frequency_limits_hz"]
    register = 2 ** event["register_octaves"] if "register_octaves" in event else register_factor(event["note"], keyboard)
    log2f = math.log2(family["base_hz"] * register) + shape(family, u) + keyboard["bend_range_octaves"] * bend
    frequency = np.clip(2 ** log2f, low, high)
    phase = 2 * np.pi * np.cumsum(frequency) / rate
    return amplitude * envelope(n, rate, keyboard) * np.sin(phase)


def load_recordings(layout: Layout, events: list[dict], config: dict):
    """Recorded keys: hash-checked source clips, high-passed and peak-normalized to 1."""
    import numpy as np
    import soundfile as sf
    from scipy.signal import butter, resample_poly, sosfiltfilt

    needed = {event["source"]["recording"] for event in events if "recording" in event["source"]}
    if not needed:
        return {}, {}
    manifest = layout.input / "audio" / "sources.json"
    known = {item["id"]: item for item in read_json(manifest)["clips"]} if manifest.exists() else {}
    rate, clips, provenance = config["sample_rate"], {}, {}
    for clip_id in sorted(needed):
        path = layout.input / "audio" / f"{clip_id}.wav"
        if clip_id not in known or not path.exists():
            raise ValueError(f"Recorded key needs {path}; run: uv run --group art main.py art fetch")
        if digest(path) != known[clip_id]["sha256"]:
            raise ValueError(f"Recorded source changed since download: {path}")
        audio, source_rate = sf.read(path, dtype="float64", always_2d=True)
        audio = audio.mean(axis=1)
        if source_rate != rate:
            divisor = math.gcd(source_rate, rate)
            audio = resample_poly(audio, rate // divisor, source_rate // divisor)
        sos = butter(4, config["keyboard"]["recording_highpass_hz"], "highpass", fs=rate, output="sos")
        audio = sosfiltfilt(sos, audio)
        peak = float(np.max(np.abs(audio)))
        clips[clip_id] = audio / peak
        provenance[clip_id] = {"path": str(path.resolve()), "sha256": known[clip_id]["sha256"], "dataset": known[clip_id]["dataset"],
                               "row_index": known[clip_id]["row_index"], "source_sample_rate": source_rate,
                               "duration_s": len(audio) / rate, "highpassed_peak": peak,
                               "transform": f"Mono mean; {config['keyboard']['recording_highpass_hz']} Hz 4th-order zero-phase high-pass; peak-normalized, then velocity gain. No pitch or time change."}
    return clips, provenance


def render_events(events: list[dict], config: dict, recordings: dict):
    import numpy as np

    keyboard, rate = config["keyboard"], config["sample_rate"]
    lead = keyboard["lead_in_s"]
    parts = [(round((lead + event["start_s"]) * rate), synthesize_note(event, config, recordings)) for event in events]
    total = max(start + len(audio) for start, audio in parts) + round(keyboard["tail_s"] * rate)
    mix = np.zeros(total)
    for start, audio in parts:
        mix[start:start + len(audio)] += audio
    for event, (start, audio) in zip(events, parts):
        event["emitted_start_s"] = start / rate
        event["emitted_duration_s"] = len(audio) / rate
    if np.max(np.abs(mix)) >= 1:
        raise ValueError("Overlapping notes clip; lower the velocities")
    return mix


# --- Measurement ---------------------------------------------------------------------

def read_audio(path: Path):
    import soundfile as sf

    samples, rate = sf.read(path, dtype="float64", always_2d=True)
    return samples.mean(axis=1), rate


def runs(mask):
    import numpy as np

    edges = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def measure(waveform, rate: int, config: dict):
    """Ridge contour, tonal segments and click groups measured from the waveform alone."""
    import numpy as np
    from scipy.ndimage import uniform_filter1d
    from scipy.signal import butter, find_peaks, medfilt, sosfiltfilt, stft

    a = config["analysis"]
    if len(waveform) < a["n_fft"] or not np.isfinite(waveform).all():
        raise ValueError("Audio is too short or not finite")
    frequencies, times, spectrum = stft(waveform, rate, window="hann", nperseg=a["n_fft"], noverlap=a["n_fft"] - a["hop"],
                                        boundary=None, padded=False)
    band = (frequencies >= a["band_hz"][0]) & (frequencies <= min(a["band_hz"][1], rate / 2 - 1))
    power = np.abs(spectrum[band]) ** 2
    bins = frequencies[band]
    peak = np.argmax(power, axis=0)
    columns = np.arange(power.shape[1])
    log_power = 10 * np.log10(np.maximum(power, 1e-30))
    inner = np.clip(peak, 1, len(bins) - 2)
    alpha, beta, gamma = log_power[inner - 1, columns], log_power[inner, columns], log_power[inner + 1, columns]
    denominator = alpha - 2 * beta + gamma
    delta = np.where(np.abs(denominator) > 1e-12, .5 * (alpha - gamma) / np.where(denominator == 0, 1, denominator), 0)
    delta = np.where((peak > 0) & (peak < len(bins) - 1), np.clip(delta, -.5, .5), 0)
    ridge_hz = bins[inner] + delta * (bins[1] - bins[0])
    ridge_hz = np.where((peak > 0) & (peak < len(bins) - 1), ridge_hz, bins[peak])
    ridge_db = 20 * np.log10(np.maximum(2 * np.sqrt(power[peak, columns]), 1e-12))
    tonality = 10 * np.log10(np.maximum(power[peak, columns], 1e-30) / np.maximum(np.median(power, axis=0), 1e-30))
    voiced = (tonality >= a["tonality_db"]) & (ridge_db >= a["absolute_floor_dbfs"])
    log2f = np.log2(ridge_hz)
    # Bridge short dropouts when the contour continues at a similar frequency.
    for start, stop in runs(~voiced):
        if 0 < start and stop < len(voiced) and stop - start <= a["bridge_frames"] and abs(log2f[stop] - log2f[start - 1]) < a["max_jump_octaves"]:
            voiced[start:stop] = True
            log2f[start:stop] = np.interp(np.arange(start, stop), [start - 1, stop], [log2f[start - 1], log2f[stop]])
    # A level valley splits legato notes whose pitch happens to be continuous.
    reach = max(1, round(a["valley_window_s"] * rate / a["hop"]))
    segments = []
    for start, stop in runs(voiced):
        level = ridge_db[start:stop]
        valleys = [start + i for i in range(1, len(level) - 1)
                   if level[i] <= level[i - 1] and level[i] < level[i + 1]
                   and min(level[max(0, i - reach):i].max(), level[i + 1:i + 1 + reach].max()) - level[i] >= a["valley_db"]]
        jumps = [i for i in range(start + 1, stop) if abs(log2f[i] - log2f[i - 1]) > a["max_jump_octaves"]]
        cuts = sorted(set([start, stop] + jumps + valleys))
        for begin, end in zip(cuts[:-1], cuts[1:]):
            if (end - begin) * a["hop"] / rate < a["min_segment_s"]:
                continue
            kernel = min(a["median_frames"], (end - begin) // 2 * 2 - 1)
            smooth = medfilt(log2f[begin:end], kernel) if kernel >= 3 else log2f[begin:end]
            segments.append({"kind": "tonal", "frames": [int(begin), int(end)],
                             "start_s": float(times[begin]), "end_s": float(times[end - 1]),
                             "time_s": times[begin:end].tolist(), "hz": (2 ** smooth).tolist(),
                             "level_dbfs": ridge_db[begin:end].tolist()})
    # Clicks: short-time energy far above its local surround in the high-passed waveform.
    sos = butter(4, a["click_highpass_hz"], "highpass", fs=rate, output="sos")
    energy = sosfiltfilt(sos, waveform) ** 2
    short = uniform_filter1d(energy, max(1, round(a["click_short_s"] * rate)))
    local = uniform_filter1d(energy, max(1, round(a["click_long_s"] * rate)))
    ratio = 10 * np.log10(np.maximum(short, 1e-30) / np.maximum(local, 1e-30))
    candidates, _ = find_peaks(short, distance=max(1, round(a["click_min_separation_s"] * rate)))
    floor = 10 ** (a["absolute_floor_dbfs"] / 10)
    clicks = [int(i) for i in candidates if ratio[i] >= a["click_ratio_db"] and short[i] >= floor]
    click_db = {i: float(10 * np.log10(short[i] * 2)) for i in clicks}
    groups, current = [], []
    for index in clicks:
        if current and (index - current[-1]) / rate > a["click_group_gap_s"]:
            groups.append(current)
            current = []
        current.append(index)
    if current:
        groups.append(current)
    isolated = []
    for group in groups:
        if len(group) < a["click_min_count"]:
            isolated += [i / rate for i in group]
            continue
        segments.append({"kind": "clicks", "start_s": group[0] / rate, "end_s": group[-1] / rate,
                          "time_s": [i / rate for i in group], "level_dbfs": [click_db[i] for i in group]})
    segments.sort(key=lambda segment: (segment["start_s"], segment["kind"]))
    for index, segment in enumerate(segments):
        segment["index"] = index
        segment["duration_s"] = segment["end_s"] - segment["start_s"]
        if segment["kind"] == "tonal":
            octaves = np.log2(segment["hz"])
            fit = np.polyfit(np.asarray(segment["time_s"]) - segment["start_s"], octaves, 1) if len(octaves) > 2 else [0, octaves.mean()]
            residual = octaves - np.polyval(fit, np.asarray(segment["time_s"]) - segment["start_s"])
            segment["summary"] = {"start_hz": float(2 ** octaves[0]), "end_hz": float(2 ** octaves[-1]), "mean_hz": float(2 ** octaves.mean()),
                                  "net_octaves": float(octaves[-1] - octaves[0]), "slope_octaves_per_s": float(fit[0]),
                                  "modulation_semitones": float(12 * residual.std()), "mean_level_dbfs": float(np.mean(segment["level_dbfs"]))}
        else:
            intervals = np.diff(segment["time_s"])
            segment["summary"] = {"clicks": len(segment["time_s"]), "rate_hz": float(1 / intervals.mean()),
                                  "mean_interval_s": float(intervals.mean()), "mean_level_dbfs": float(np.mean(segment["level_dbfs"]))}
    return {"sample_rate": rate, "duration_s": len(waveform) / rate, "frame_hop_s": a["hop"] / rate,
            "frames": {"time_s": times.tolist(), "ridge_hz": ridge_hz.tolist(), "ridge_dbfs": ridge_db.tolist(),
                       "tonality_db": tonality.tolist(), "voiced": voiced.tolist()},
            "segments": segments, "isolated_clicks_s": isolated}


# --- Recognition: CHAT-style designed vocabulary with rejection ----------------------------

def normalized_contour(hz, points: int):
    import numpy as np

    octaves = np.log2(np.asarray(hz, dtype=float))
    u = np.linspace(0, 1, len(octaves))
    values = 12 * np.interp(np.linspace(0, 1, points), u, octaves)
    return values - values.mean()


def template(family: dict, points: int):
    import numpy as np

    values = 12 * shape(family, np.linspace(0, 1, points))
    return values - values.mean()


def dtw(a, b, band: int):
    import numpy as np

    n, m = len(a), len(b)
    cost = np.full((n + 1, m + 1), np.inf)
    steps = np.zeros((n + 1, m + 1))
    cost[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(max(1, i - band), min(m, i + band) + 1):
            options = (cost[i - 1, j - 1], cost[i - 1, j], cost[i, j - 1])
            k = int(np.argmin(options))
            cost[i, j] = abs(a[i - 1] - b[j - 1]) + options[k]
            steps[i, j] = (steps[i - 1, j - 1], steps[i - 1, j], steps[i, j - 1])[k] + 1
    return float(cost[n, m] / steps[n, m])


def recognize(segment: dict, config: dict):
    """Nearest designed template by DTW distance in semitones; reject unclear matches."""
    if segment["kind"] == "clicks":
        return {"method": "onsets", "command": "beads", "accepted": True,
                "reason": f"{segment['summary']['clicks']} clicks at {segment['summary']['rate_hz']:.1f}/s"}
    r = config["recognition"]
    contour = normalized_contour(segment["hz"], r["points"])
    extent = float(contour.max() - contour.min())
    band = max(1, round(r["band_fraction"] * r["points"]))
    distances = {name: dtw(contour, template(config["families"][name], r["points"]), band) for name in config["commands"]}
    ranked = sorted(distances, key=distances.get)
    best, second = ranked[0], ranked[1]
    margin = distances[second] - distances[best]
    result = {"method": "contour-dtw", "distances_semitones": distances, "nearest": best, "distance": distances[best],
              "margin": margin, "extent_semitones": extent}
    if segment["duration_s"] < r["min_duration_s"]:
        reason = f"too short ({segment['duration_s']:.2f} s < {r['min_duration_s']} s)"
    elif extent < r["min_extent_semitones"]:
        reason = f"nearly steady ({extent:.1f} semitones)"
    elif distances[best] > r["accept_semitones"]:
        reason = f"no template within {r['accept_semitones']} semitones (nearest {best}: {distances[best]:.2f})"
    elif margin < r["margin_semitones"]:
        reason = f"ambiguous: {best} vs {second} differ by {margin:.2f} semitones"
    else:
        return result | {"command": config["commands"][best], "accepted": True,
                         "reason": f"{best} at {distances[best]:.2f} semitones, margin {margin:.2f}"}
    return result | {"command": "none", "accepted": False, "reason": reason}


# --- Consequence: drawing ----------------------------------------------------------------

def rim(angle_degrees: float, stone: dict):
    angle = math.radians(angle_degrees)
    point = (stone["rx"] * math.cos(angle), stone["ry"] * math.sin(angle))
    heading = math.atan2(math.sin(angle) / stone["ry"], math.cos(angle) / stone["rx"])
    return point, heading


def width_for(level, drawing: dict):
    import numpy as np

    (w0, w1), (l0, l1) = drawing["width_units"], drawing["width_level_dbfs"]
    return w0 + (w1 - w0) * np.clip((np.asarray(level, dtype=float) - l0) / (l1 - l0), 0, 1)


def walk(tip: dict, segment: dict, drawing: dict, scale: float = 1.0):
    """Heading follows pitch (degrees per octave, mirrored by chirality); time sets length."""
    import numpy as np

    octaves = np.log2(segment["hz"])
    heading = tip["heading"] + tip["chirality"] * np.radians(drawing["turn_degrees_per_octave"]) * (octaves - octaves[0])
    step = drawing["speed_units_per_s"] * np.diff(np.concatenate([segment["time_s"], [segment["time_s"][-1] + segment.get("hop", 0.005)]]))
    x = tip["point"][0] + np.concatenate([[0], np.cumsum(step * np.cos(heading))[:-1]])
    y = tip["point"][1] + np.concatenate([[0], np.cumsum(step * np.sin(heading))[:-1]])
    return np.column_stack([x, y]), heading, width_for(segment["level_dbfs"], drawing) * scale * tip["scale"]


def draw(measured: dict, recognitions: list[dict], config: dict, stone_id: str):
    import numpy as np

    drawing = config["drawing"]
    stone = drawing["stones"][stone_id]
    hop = measured["frame_hop_s"]
    angle = drawing["start_angle_degrees"]
    point, heading = rim(angle, stone)
    tips = [{"point": point, "heading": heading, "chirality": 1, "scale": 1.0}]
    marks, events, previous_end = [], [], None
    for segment, recognition in zip(measured["segments"], recognitions):
        segment = dict(segment, hop=hop)
        lifted = previous_end is not None and segment["start_s"] - previous_end >= drawing["lift_gap_s"]
        if lifted:
            angle += drawing["lift_angle_degrees"]
            point, heading = rim(angle, stone)
            tips = [{"point": point, "heading": heading, "chirality": 1, "scale": 1.0}]
        previous_end = segment["end_s"] if previous_end is None else max(previous_end, segment["end_s"])
        command = recognition["command"]
        before = len(tips)
        if command == "branch":
            spread = math.radians(drawing["branch_degrees"])
            children = []
            for tip in tips:
                for sign in (1, -1) if len(tips) + len(children) < drawing["max_tips"] else (tip["chirality"],):
                    # Mirrored turning makes the pair diverge: each child bends away from its sibling.
                    children.append({"point": tip["point"], "heading": tip["heading"] + sign * spread, "chirality": -sign,
                                     "scale": tip["scale"] * drawing["branch_width_factor"]})
            tips = children
        length, turns, widths = 0.0, [], []
        for number, tip in enumerate(tips):
            if segment["kind"] == "clicks":
                times = np.asarray(segment["time_s"])
                distance = drawing["speed_units_per_s"] * (times - times[0])
                (r0, r1), (l0, l1) = drawing["bead_radius_units"], drawing["width_level_dbfs"]
                radius = r0 + (r1 - r0) * np.clip((np.asarray(segment["level_dbfs"]) - l0) / (l1 - l0), 0, 1)
                direction = np.array([math.cos(tip["heading"]), math.sin(tip["heading"])])
                centers = np.asarray(tip["point"]) + (distance[:, None] + radius[0]) * direction
                marks.append({"kind": "beads", "event": segment["index"], "tip": number,
                              "centers": centers.tolist(), "radii": (radius * tip["scale"]).tolist()})
                tip["point"] = tuple(centers[-1] + (radius[-1] + 2) * direction)
                length += float(distance[-1])
                widths.append(float(np.mean(radius)))
                continue
            path, heading_curve, width = walk(tip, segment, drawing)
            if command == "open":
                total = float(np.sum(np.linalg.norm(np.diff(path, axis=0), axis=1))) + drawing["speed_units_per_s"] * hop
                radius = min(drawing["open_diameter_fraction"] * total / 2, drawing["open_max_radius_units"])
                octaves = np.log2(segment["hz"])
                trend = np.polyval(np.polyfit(np.arange(len(octaves)), octaves, 1), np.arange(len(octaves)))
                deviation = 12 * (octaves - trend)
                deviation = deviation / max(np.abs(deviation).max(), 1.0)
                phi = np.linspace(0, 2 * math.pi, len(octaves), endpoint=False)
                direction = np.array([math.cos(tip["heading"]), math.sin(tip["heading"])])
                center = np.asarray(tip["point"]) + radius * direction
                start = tip["heading"] + math.pi
                r = radius * (1 + drawing["open_scallop_fraction"] * deviation)
                ring = center + np.column_stack([r * np.cos(start + tip["chirality"] * phi), r * np.sin(start + tip["chirality"] * phi)])
                marks.append({"kind": "loop", "event": segment["index"], "tip": number, "points": ring.tolist(),
                              "widths": width.tolist(), "radius": radius})
                tip["point"] = tuple(center + radius * direction)
                length += total
                turns.append(0.0)
                widths.append(float(np.mean(width)))
                continue
            if command == "fold":
                slope = np.gradient(np.log2(segment["hz"]))
                slope = np.convolve(slope, np.ones(5) / 5, mode="same")
                marks.append({"kind": "fold", "event": segment["index"], "tip": number, "points": path.tolist(),
                              "widths": (width * drawing["fold_width_factor"]).tolist(), "lit_left": (slope * tip["chirality"] >= 0).tolist()})
            else:
                marks.append({"kind": "line", "event": segment["index"], "tip": number, "points": path.tolist(), "widths": width.tolist()})
            last = path[-1] + drawing["speed_units_per_s"] * hop * np.array([math.cos(heading_curve[-1]), math.sin(heading_curve[-1])])
            tip["point"], tip["heading"] = tuple(last), float(heading_curve[-1])
            length += float(np.sum(np.linalg.norm(np.diff(path, axis=0), axis=1)))
            turns.append(float(np.degrees(heading_curve[-1] - heading_curve[0])))
            widths.append(float(np.mean(width)))
        events.append({"event": segment["index"], "kind": segment["kind"], "start_s": segment["start_s"], "end_s": segment["end_s"],
                       "command": command, "lifted": lifted, "rim_angle_degrees": angle % 360, "tips_before": before,
                       "tips_after": len(tips), "path_length_units": round(length, 3),
                       "turn_degrees_first_tip": round(turns[0], 3) if turns else None,
                       "mean_width_units": round(float(np.mean(widths)), 3) if widths else None})
    return {"stone": dict(stone, id=stone_id), "marks": marks, "events": events}


def rounded(value, digits: int = 3):
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, dict):
        return {key: rounded(item, digits) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [rounded(item, digits) for item in value]
    return value


def stroke_hash(stroke: dict):
    text = json.dumps(rounded(stroke), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


def metrics(stroke: dict):
    import numpy as np

    totals = {"marks": len(stroke["marks"]), "line_units": 0.0, "fold_units": 0.0, "openings": 0, "beads": 0, "tips_max": 0}
    for mark in stroke["marks"]:
        if mark["kind"] in ("line", "fold"):
            totals[f"{mark['kind']}_units"] += float(np.sum(np.linalg.norm(np.diff(np.asarray(mark["points"]), axis=0), axis=1)))
        elif mark["kind"] == "loop":
            totals["openings"] += 1
        else:
            totals["beads"] += len(mark["centers"])
    totals["tips_max"] = max((event["tips_after"] for event in stroke["events"]), default=0)
    totals["lifts"] = sum(event["lifted"] for event in stroke["events"])
    return rounded(totals, 1)


# --- Rendering: one primitive list feeds both SVG and PNG ------------------------------------

PALETTE = {"grow": "#2f6f8f", "branch": "#3f8f4f", "fold": "#9a5a2a", "open": "#7a4f9a", "beads": "#b03a5b", "none": "#7d7d7d"}


def offset(points, widths):
    import numpy as np

    points = np.asarray(points, dtype=float)
    tangent = np.gradient(points, axis=0) if len(points) > 1 else np.array([[1.0, 0.0]])
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-12)
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
    half = np.asarray(widths, dtype=float)[:, None] / 2
    return points + normal * half, points - normal * half


def primitives(stroke: dict, explained: bool = False, commands: dict | None = None):
    """Polygons/circles in drawing units (y up)."""
    import numpy as np

    shapes = []
    command_of = commands or {}
    for mark in stroke["marks"]:
        colour = PALETTE[command_of.get(mark["event"], "none")] if explained else None
        if mark["kind"] == "line":
            left, right = offset(mark["points"], mark["widths"])
            shapes.append({"polygon": np.vstack([left, right[::-1]]).tolist(), "fill": colour or "#c9cdd3", "stroke": "#6f747c", "event": mark["event"]})
            if not explained:
                shine, _ = offset(mark["points"], np.asarray(mark["widths"]) * .35)
                shapes.append({"polyline": shine.tolist(), "stroke": "#f4f6f8", "width": 1.6, "event": mark["event"]})
        elif mark["kind"] == "fold":
            left, right = offset(mark["points"], mark["widths"])
            centre = np.asarray(mark["points"])
            for i in range(len(centre) - 1):
                lit = mark["lit_left"][i]
                for side, light in ((left, lit), (right, not lit)):
                    quad = [centre[i], side[i], side[i + 1], centre[i + 1]]
                    tone = ("#e9ecef" if light else "#8e949c") if not explained else (colour if light else "#3b2a1e")
                    shapes.append({"polygon": np.asarray(quad).tolist(), "fill": tone, "stroke": None, "event": mark["event"]})
            shapes.append({"polyline": centre.tolist(), "stroke": "#5d6168", "width": .8, "event": mark["event"]})
        elif mark["kind"] == "loop":
            ring = np.asarray(mark["points"])
            closed = np.vstack([ring, ring[:1]])
            widths = np.concatenate([mark["widths"], mark["widths"][:1]])
            left, right = offset(closed, widths)
            shapes.append({"ring": [left.tolist(), right.tolist()], "fill": colour or "#c9cdd3", "stroke": "#6f747c", "event": mark["event"]})
        else:
            for center, radius in zip(mark["centers"], mark["radii"]):
                shapes.append({"circle": center, "r": radius, "fill": colour or "#d4d7dc", "stroke": "#6f747c", "event": mark["event"]})
    return shapes


def fitted_view(stroke: dict, shapes: list[dict], margin: float = 24):
    """Square viewBox around the drawn geometry, in SVG coordinates (y down)."""
    import numpy as np

    points = [[stroke["stone"]["rx"], stroke["stone"]["ry"]], [-stroke["stone"]["rx"], -stroke["stone"]["ry"]]]
    for shape in shapes:
        if "circle" in shape:
            x, y = shape["circle"]
            points += [[x - shape["r"], y - shape["r"]], [x + shape["r"], y + shape["r"]]]
        else:
            for part in shape.get("ring") or [shape.get("polygon") or shape.get("polyline")]:
                points += part
    points = np.asarray(points, dtype=float)
    low, high = points.min(axis=0) - margin, points.max(axis=0) + margin
    centre, half = (low + high) / 2, float(max(high - low)) / 2
    return centre[0] - half, -centre[1] - half, 2 * half


def write_svg(path: Path, stroke: dict, config: dict, explained: bool = False, commands: dict | None = None, title: str = "",
              fit: bool = False):
    half = config["drawing"]["canvas_half_size"]
    stone = stroke["stone"]
    fmt = lambda points: " ".join(f"{x:.2f},{-y:.2f}" for x, y in points)
    body = []
    for shape in primitives(stroke, explained, commands):
        outline = f' stroke="{shape["stroke"]}" stroke-width="0.8"' if shape.get("stroke") else ' stroke="none"'
        if "polygon" in shape:
            body.append(f'<polygon points="{fmt(shape["polygon"])}" fill="{shape["fill"]}"{outline}/>')
        elif "polyline" in shape:
            body.append(f'<polyline points="{fmt(shape["polyline"])}" fill="none" stroke="{shape["stroke"]}" stroke-width="{shape["width"]}"/>')
        elif "ring" in shape:
            outer, inner = shape["ring"]
            body.append(f'<path d="M{fmt(outer)}Z M{fmt(inner[::-1])}Z" fill="{shape["fill"]}" fill-rule="evenodd"{outline}/>')
        else:
            x, y = shape["circle"]
            body.append(f'<circle cx="{x:.2f}" cy="{-y:.2f}" r="{shape["r"]:.2f}" fill="{shape["fill"] if explained else "url(#bead)"}"{outline}/>')
    labels = []
    if explained:
        for event in stroke["events"]:
            first = next((m for m in stroke["marks"] if m["event"] == event["event"]), None)
            if first is None:
                continue
            x, y = (first.get("points") or first.get("centers"))[0]
            labels.append(f'<text x="{x + 6:.1f}" y="{-y - 6:.1f}" font-size="18" font-family="sans-serif" fill="#222">{event["event"]}</text>')
    x0, y0, size = fitted_view(stroke, primitives(stroke, explained, commands)) if fit else (-half, -half, 2 * half)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {size:.1f} {size:.1f}" width="800" height="800">
<title>{title}</title>
<defs><radialGradient id="stone" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="{stone['inner']}"/><stop offset="1" stop-color="{stone['outer']}"/></radialGradient>
<radialGradient id="bead" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#9aa0a8"/></radialGradient></defs>
<rect x="{x0:.1f}" y="{y0:.1f}" width="{size:.1f}" height="{size:.1f}" fill="#f4f0e5"/>
{"".join(body)}
<ellipse cx="0" cy="0" rx="{stone['rx']}" ry="{stone['ry']}" fill="url(#stone)" stroke="#5b3a12" stroke-width="1.5"/>
{"".join(labels)}
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def plot_stroke(axes, stroke: dict, config: dict, explained: bool = False, commands: dict | None = None, labels: bool = True):
    from matplotlib.patches import Circle, Ellipse, PathPatch, Polygon
    from matplotlib.path import Path as MplPath
    import numpy as np

    half = config["drawing"]["canvas_half_size"]
    stone = stroke["stone"]
    axes.add_patch(Polygon([[-half, -half], [half, -half], [half, half], [-half, half]], color="#f4f0e5", zorder=0))
    for shape in primitives(stroke, explained, commands):
        edge = shape.get("stroke") or "none"
        if "polygon" in shape:
            axes.add_patch(Polygon(shape["polygon"], facecolor=shape["fill"], edgecolor=edge, linewidth=.4))
        elif "polyline" in shape:
            line = np.asarray(shape["polyline"])
            axes.plot(line[:, 0], line[:, 1], color=shape["stroke"], linewidth=.4)
        elif "ring" in shape:
            outer, inner = (np.asarray(item) for item in shape["ring"])
            vertices = np.vstack([outer, outer[:1], inner[::-1], inner[-1:]])
            codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(outer) - 1) + [MplPath.CLOSEPOLY] + [MplPath.MOVETO] + [MplPath.LINETO] * (len(inner) - 1) + [MplPath.CLOSEPOLY]
            axes.add_patch(PathPatch(MplPath(vertices, codes), facecolor=shape["fill"], edgecolor=edge, linewidth=.4))
        else:
            axes.add_patch(Circle(shape["circle"], shape["r"], facecolor=shape["fill"], edgecolor=edge, linewidth=.4))
    axes.add_patch(Ellipse((0, 0), 2 * stone["rx"], 2 * stone["ry"], facecolor=stone["inner"], edgecolor=stone["outer"], linewidth=2, zorder=5))
    if explained and labels:
        for event in stroke["events"]:
            first = next((m for m in stroke["marks"] if m["event"] == event["event"]), None)
            if first is not None:
                x, y = (first.get("points") or first.get("centers"))[0]
                axes.text(x + 6, y + 6, str(event["event"]), fontsize=9, zorder=6)
    axes.set(xlim=(-half, half), ylim=(-half, half), aspect="equal")
    axes.set_axis_off()


# --- Audible guide ---------------------------------------------------------------------------

def audible_guide(measured: dict, rate: int, divisor: float = 4.0):
    """Resynthesis from the measurements: contour ÷ divisor at the same timing, plus click markers."""
    import numpy as np

    out = np.zeros(round(measured["duration_s"] * rate))
    hop = measured["frame_hop_s"]
    for segment in measured["segments"]:
        if segment["kind"] == "tonal":
            t = np.asarray(segment["time_s"])
            start, stop = round(t[0] * rate), min(len(out), round((t[-1] + hop) * rate))
            grid = np.arange(start, stop) / rate
            frequency = np.interp(grid, t, np.asarray(segment["hz"]) / divisor)
            level = 10 ** (np.interp(grid, t, segment["level_dbfs"]) / 20)
            fade = np.minimum(1, np.minimum(np.arange(len(grid)), np.arange(len(grid))[::-1]) / (.01 * rate))
            out[start:stop] += level * fade * np.sin(2 * np.pi * np.cumsum(frequency) / rate)
        else:
            pulse_t = np.arange(round(.004 * rate)) / rate
            pulse = np.sin(2 * np.pi * 1800 * pulse_t) * np.exp(-pulse_t / .0008)
            for moment, level in zip(segment["time_s"], segment["level_dbfs"]):
                i = round(moment * rate)
                n = min(len(pulse), len(out) - i)
                out[i:i + n] += 10 ** (level / 20) * pulse[:n]
    peak = np.max(np.abs(out))
    return out * (.7 / peak if peak > 0 else 1)


# --- Pipelines -----------------------------------------------------------------------------

def analyze_file(path: Path, config: dict, stone: str, recognizer=None):
    """Audio file → measurements → recognition → stroke. Reads nothing except the audio."""
    started = time.perf_counter()
    waveform, rate = read_audio(path)
    measured = measure(waveform, rate, config)
    measured_at = time.perf_counter()
    recognitions = [recognize(segment, config) for segment in measured["segments"]]
    if recognizer is not None:
        recognitions = recognizer(waveform, rate, measured, recognitions)
    recognized_at = time.perf_counter()
    stroke = draw(measured, recognitions, config, stone)
    drawn_at = time.perf_counter()
    timing = {"measure_ms": 1000 * (measured_at - started), "recognize_ms": 1000 * (recognized_at - measured_at),
              "draw_ms": 1000 * (drawn_at - recognized_at)}
    return waveform, rate, measured, recognitions, stroke, timing


def explain_figure(path: Path, waveform, rate: int, measured: dict, recognitions: list[dict], stroke: dict, config: dict,
                   title: str, events: list[dict] | None = None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.signal import stft

    commands = {segment["index"]: recognition["command"] for segment, recognition in zip(measured["segments"], recognitions)}
    figure = plt.figure(figsize=(16, 8.4), facecolor="#f4f0e5")
    figure.text(.02, .955, title, size=18, weight="bold", color="#39352f")
    has_keys = bool(events)
    spectrum_axes = figure.add_axes([.05, .1, .52, .56 if has_keys else .78])
    f, t, z = stft(waveform, rate, nperseg=1024, noverlap=1024 - 220)
    spectrum_axes.pcolormesh(t, f / 1000, 20 * np.log10(np.abs(z) + 1e-9), shading="auto", cmap="Greys", vmin=-110, vmax=-20, rasterized=True)
    for segment, recognition in zip(measured["segments"], recognitions):
        colour = PALETTE[recognition["command"]]
        if segment["kind"] == "tonal":
            spectrum_axes.plot(segment["time_s"], np.asarray(segment["hz"]) / 1000, color=colour, linewidth=2.2)
            spectrum_axes.text(segment["start_s"], max(segment["hz"]) / 1000 + .6, f"{segment['index']}·{recognition['command']}", color=colour, size=9, weight="bold")
        else:
            spectrum_axes.vlines(segment["time_s"], 1, 2.5, color=colour, linewidth=1.5)
            spectrum_axes.text(segment["start_s"], 2.8, f"{segment['index']}·beads", color=colour, size=9, weight="bold")
    spectrum_axes.set(ylim=(0, rate / 2000), xlim=(0, measured["duration_s"]), ylabel="Frequency (kHz)", xlabel="Time (s) · emitted waveform")
    spectrum_axes.set_title("Measured from the waveform: ridge contour (coloured by recognized command) and click onsets", loc="left", size=10)
    if has_keys:
        keys_axes = figure.add_axes([.05, .72, .52, .17], sharex=spectrum_axes)
        lead = config["keyboard"]["lead_in_s"]
        for event in events:
            source = event["source"]
            colour = "#39352f" if "recording" in source else PALETTE[config["commands"].get(source.get("family"), "beads" if source.get("family") == "clicks" else "none")]
            keys_axes.broken_barh([(lead + event["start_s"], event["duration_s"])], (event["note"] - .4, .8), color=colour)
            label = source.get("recording", source.get("family"))
            keys_axes.text(lead + event["start_s"], event["note"] + .7, f"{event['name']} {label}", size=8)
        notes = [event["note"] for event in events]
        keys_axes.set(ylim=(min(notes) - 2, max(notes) + 3), ylabel="Key")
        keys_axes.set_title("Keyboard input (shown for reference; the drawing does not read it)", loc="left", size=10)
        keys_axes.tick_params(labelbottom=False)
    drawing_axes = figure.add_axes([.6, .04, .39, .86])
    plot_stroke(drawing_axes, stroke, config, explained=True, commands=commands)
    drawing_axes.set_title("Consequence: stroke coloured by command, numbered by sound event", size=10)
    handles = [plt.Line2D([], [], color=colour, linewidth=6, label=name) for name, colour in PALETTE.items()]
    drawing_axes.legend(handles=handles, loc="lower left", fontsize=8, ncol=3, frameon=False)
    figure.savefig(path, dpi=110)
    plt.close(figure)


def artwork_png(path: Path, stroke: dict, config: dict):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(6, 6), facecolor="#f4f0e5")
    axes = figure.add_axes([0, 0, 1, 1])
    plot_stroke(axes, stroke, config)
    figure.savefig(path, dpi=120)
    plt.close(figure)


def save_drawing(directory: Path, name: str, audio_path: Path, config: dict, stone: str, title: str,
                 events: list[dict] | None = None, recognizer=None, figure: bool = True):
    import soundfile as sf

    directory.mkdir(parents=True, exist_ok=True)
    waveform, rate, measured, recognitions, stroke, timing = analyze_file(audio_path, config, stone, recognizer)
    commands = {segment["index"]: recognition["command"] for segment, recognition in zip(measured["segments"], recognitions)}
    write_svg(directory / f"{name}.svg", stroke, config, title=title)
    write_svg(directory / f"{name}-explained.svg", stroke, config, explained=True, commands=commands, title=title)
    started = time.perf_counter()
    artwork_png(directory / f"{name}.png", stroke, config)
    if figure:
        explain_figure(directory / f"{name}-explained.png", waveform, rate, measured, recognitions, stroke, config, title, events)
    timing["render_ms"] = 1000 * (time.perf_counter() - started)
    guide = directory / f"{name}-guide.wav"
    sf.write(guide, audible_guide(measured, rate), rate, subtype="PCM_16")
    record = {"audio": audio_path.name if audio_path.parent == directory else str(audio_path), "audio_sha256": digest(audio_path),
              "sample_rate": rate, "duration_s": len(waveform) / rate, "stone": stone, "stroke_sha256": stroke_hash(stroke),
              "metrics": metrics(stroke), "timing_ms": rounded(timing, 1),
              "segments": [rounded({key: value for key, value in segment.items() if key not in ("time_s", "hz", "level_dbfs")} | {"recognition": recognition}, 4)
                           for segment, recognition in zip(measured["segments"], recognitions)],
              "stroke_events": stroke["events"], "isolated_clicks_s": rounded(measured["isolated_clicks_s"], 4),
              "files": {"svg": f"{name}.svg", "explained_svg": f"{name}-explained.svg", "png": f"{name}.png",
                        "explained_png": f"{name}-explained.png" if figure else None, "guide": guide.name,
                        "controls": f"{name}-controls.json", "stroke": f"{name}-stroke.json"}}
    write_json(directory / f"{name}-controls.json", rounded({"measured": measured, "recognitions": recognitions}, 5))
    write_json(directory / f"{name}-stroke.json", rounded(stroke))
    return record


def perform(layout: Layout, events: list[dict], config: dict, directory: Path, name: str, stone: str, title: str,
            phrase: str | None = None, midi: Path | None = None, recognizer=None, figure: bool = True):
    """Keyboard events → emitted waveform (saved) → drawing analyzed from that file only."""
    import soundfile as sf

    started = time.perf_counter()
    recordings, provenance = load_recordings(layout, events, config)
    mix = render_events(events, config, recordings)
    directory.mkdir(parents=True, exist_ok=True)
    audio_path = directory / f"{name}.wav"
    sf.write(audio_path, mix, config["sample_rate"], subtype="PCM_16")
    synthesis_ms = 1000 * (time.perf_counter() - started)
    record = save_drawing(directory, name, audio_path, config, stone, title, events, recognizer, figure)
    record["timing_ms"]["synthesize_ms"] = round(synthesis_ms, 1)
    performance = {"name": name, "title": title, "phrase": phrase, "midi": str(midi) if midi else None, "events": events,
                   "recordings": provenance, "config_sha256": config["config_sha256"], "created_at_utc": now(),
                   "emitted_audio": audio_path.name, "note": "The drawing is computed from the emitted WAV alone; these events document how it was played."}
    write_json(directory / f"{name}-performance.json", rounded(performance, 6))
    return record | {"performance": f"{name}-performance.json", "events": rounded(events, 4), "phrase": phrase, "title": title, "name": name}
