"""Saved sound-brush study: key map, performances, one-feature changes, replay checks, live MIDI."""

import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from .brush import (CLASSES, analyze_file, events_from_messages, load_config, parse_phrase, perform, plot_stroke, rounded,
                    save_drawing, stroke_hash, write_svg)
from .data import Layout, ROOT, digest, now, read_json, write_json

KEY_DURATIONS = {"recording": 2.3, "clicks": 0.8}


def key_phrases(config: dict):
    rows = []
    for pitch_class in CLASSES:
        source = config["keyboard"]["pitch_classes"].get(pitch_class)
        if source is None:
            continue
        family = source.get("family")
        duration = KEY_DURATIONS["recording"] if "recording" in source else KEY_DURATIONS.get(family, 0.8)
        rows.append({"pitch_class": pitch_class, "slug": pitch_class.replace("#", "s"), "phrase": f"{pitch_class}4:{duration}@100",
                     "source": source, "title": config["families"][family]["title"] if family else f"Recorded {source['recording']}",
                     "designed_command": config["commands"].get(family, "beads" if family == "clicks" else "none") if family else "not designed"})
    return rows


def keys(layout: Layout, config: dict, output: Path):
    entries = []
    for row in key_phrases(config):
        events = parse_phrase(row["phrase"], config)
        record = perform(layout, events, config, output / "keys", row["slug"], "mitoring", f"Key {row['pitch_class']} · {row['title']}",
                         phrase=row["phrase"], figure=False)
        stroke = read_json(output / "keys" / record["files"]["stroke"])
        commands = {s["index"]: s["recognition"]["command"] for s in record["segments"]}
        write_svg(output / "keys" / f"{row['slug']}-thumb.svg", stroke, config, explained=True, commands=commands, fit=True,
                  title=f"Key {row['pitch_class']}, fitted view")
        entries.append(row | {"record": record, "thumbnail": f"keys/{row['slug']}-thumb.svg"})
        print(f"Key {row['pitch_class']:2s} {row['title']:34s} → {', '.join(s['recognition']['command'] for s in record['segments']) or 'no event'}", flush=True)
    return entries


def performances(layout: Layout, config: dict, output: Path, learned=None):
    entries = []
    for name, spec in config["performances"].items():
        events = parse_phrase(spec["phrase"], config)
        record = perform(layout, events, config, output / "performances", name, spec["stone"], spec["title"], phrase=spec["phrase"])
        entry = {"name": name, "spec": spec, "record": record}
        if learned is not None:
            entry["learned"] = save_drawing(output / "performances", f"{name}-learned", output / "performances" / f"{name}.wav", config,
                                            spec["stone"], spec["title"] + " · OpenWhistle commands", events, learned.recognizer)
            pairs = zip(record["segments"], entry["learned"]["segments"])
            entry["agreement"] = [{"event": a["index"], "kind": a["kind"], "contour": a["recognition"]["command"], "learned": b["recognition"]["command"]}
                                  for a, b in pairs]
        entries.append(entry)
        print(f"Performance {name}: {record['metrics']} · stroke {record['stroke_sha256'][:12]}", flush=True)
    return entries


def compare(base: dict, changed: dict):
    first = lambda record, key: next((event[key] for event in record["stroke_events"] if event[key] is not None), None)
    return {"stroke_identical": base["stroke_sha256"] == changed["stroke_sha256"],
            "commands": [[s["recognition"]["command"] for s in record["segments"]] for record in (base, changed)],
            "turn_degrees_first_event": [first(record, "turn_degrees_first_tip") for record in (base, changed)],
            "path_length_units": [sum(e["path_length_units"] for e in record["stroke_events"]) for record in (base, changed)],
            "mean_width_units": [first(record, "mean_width_units") for record in (base, changed)],
            "lifts": [record["metrics"]["lifts"] for record in (base, changed)],
            "rim_angles_degrees": [[round(e["rim_angle_degrees"], 1) for e in record["stroke_events"]] for record in (base, changed)]}


def bounds(directory: Path, names):
    import numpy as np

    points = []
    for name in names:
        stroke = read_json(directory / f"{name}-stroke.json")
        for mark in stroke["marks"]:
            points += mark.get("points") or mark.get("centers")
        points += [[stroke["stone"]["rx"], stroke["stone"]["ry"]], [-stroke["stone"]["rx"], -stroke["stone"]["ry"]]]
    points = np.asarray(points)
    low, high = points.min(axis=0) - 40, points.max(axis=0) + 40
    centre, half = (low + high) / 2, max(high - low) / 2
    return centre - half, centre + half


def perturbations(layout: Layout, config: dict, output: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = output / "perturbations"
    entries = []
    for spec in config["perturbations"]:
        records = {}
        for role in ("base", "changed"):
            events = parse_phrase(spec[role], config)
            records[role] = perform(layout, events, config, directory, f"{spec['id']}-{role}", "mitoring", f"{spec['feature']} · {role}",
                                    phrase=spec[role], figure=False)
        entry = spec | {"records": records, "comparison": compare(records["base"], records["changed"])}
        low, high = bounds(directory, [f"{spec['id']}-base", f"{spec['id']}-changed"])
        figure, axes = plt.subplots(1, 2, figsize=(8, 4.3), facecolor="#f4f0e5")
        for axis, role in zip(axes, ("base", "changed")):
            stroke = read_json(directory / f"{spec['id']}-{role}-stroke.json")
            commands = {s["index"]: s["recognition"]["command"] for s in records[role]["segments"]}
            plot_stroke(axis, stroke, config, explained=True, commands=commands, labels=False)
            axis.set(xlim=(low[0], high[0]), ylim=(low[1], high[1]))
            axis.set_title(f"{role}: {spec[role]}", size=9)
        figure.suptitle(spec["feature"], size=12, weight="bold")
        figure.savefig(directory / f"{spec['id']}.png", dpi=110)
        plt.close(figure)
        entry["figure"] = f"perturbations/{spec['id']}.png"
        entries.append(entry)
        print(f"Perturbation {spec['id']}: {entry['comparison']}", flush=True)
    return entries


def replay(layout: Layout, config: dict, output: Path, entries: list[dict]):
    """Identical audio → identical stroke, with and without the keyboard data, in a fresh process."""
    work = layout.interim / "brush-replay"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    rows = []
    for entry in entries:
        name, record, stone = entry["name"], entry["record"], entry["spec"]["stone"]
        emitted = output / "performances" / f"{name}.wav"
        anonymous = work / f"{digest(emitted)[:16]}.wav"
        shutil.copy2(emitted, anonymous)
        *_, stroke, _ = analyze_file(anonymous, config, stone)
        fresh = work / "fresh"
        command = [sys.executable, str(ROOT / "main.py"), "art", "brush", "draw", str(anonymous), "--stone", stone,
                   "--output", str(fresh), "--name", name]
        started = time.perf_counter()
        subprocess.run(command, check=True, capture_output=True, text=True, cwd=ROOT)
        fresh_hash = read_json(fresh / f"{name}-record.json")["stroke_sha256"]
        rerendered = work / f"{name}-rerendered"
        again = perform(layout, parse_phrase(entry["spec"]["phrase"], config), config, rerendered, name, stone, "re-render",
                        phrase=entry["spec"]["phrase"], figure=False)
        # Sensitivity control: the first note one velocity step quieter must change the stroke.
        tokens = entry["spec"]["phrase"].split()
        first = next(i for i, token in enumerate(tokens) if "@" in token)
        velocity = int(tokens[first].split("@")[1].split("~")[0])
        tokens[first] = tokens[first].replace(f"@{velocity}", f"@{velocity - 1}", 1)
        nudged_phrase = " ".join(tokens)
        nudged = perform(layout, parse_phrase(nudged_phrase, config), config, work / f"{name}-nudged", name, stone, "nudged",
                         phrase=nudged_phrase, figure=False)
        rows.append({"performance": name, "audio_sha256": record["audio_sha256"], "stroke_sha256": record["stroke_sha256"],
                     "anonymous_copy_stroke_sha256": stroke_hash(stroke),
                     "fresh_process_stroke_sha256": fresh_hash, "fresh_process_s": round(time.perf_counter() - started, 2),
                     "rerendered_audio_sha256": again["audio_sha256"], "rerendered_stroke_sha256": again["stroke_sha256"],
                     "control_phrase": nudged_phrase, "control_audio_sha256": nudged["audio_sha256"], "control_stroke_sha256": nudged["stroke_sha256"],
                     "identical": len({record["stroke_sha256"], stroke_hash(stroke), fresh_hash, again["stroke_sha256"]}) == 1
                                  and record["audio_sha256"] == again["audio_sha256"],
                     "control_differs": nudged["stroke_sha256"] != record["stroke_sha256"],
                     "control_width_change_units": round((nudged["stroke_events"][0]["mean_width_units"] or 0) - (record["stroke_events"][0]["mean_width_units"] or 0), 3)})
        print(f"Replay {name}: identical={rows[-1]['identical']} control_differs={rows[-1]['control_differs']}", flush=True)
    return rows


def references(layout: Layout, output: Path):
    """Copies of the Livia photographs that the two stones stand for."""
    profile_path = layout.input / "artist" / "profile.json"
    if not profile_path.exists():
        return []
    profile = read_json(profile_path)
    directory = output / "references"
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for reference in profile["references"]:
        if reference["id"] not in ("mitoring", "mycelium", "nanot"):
            continue
        source = Path(reference["cached_path"])
        if not source.exists() or digest(source) != reference["sha256"]:
            continue
        shutil.copy2(source, directory / source.name)
        rows.append({"id": reference["id"], "title": reference["title"], "connection": reference["connection"],
                     "image": f"references/{source.name}", "sha256": reference["sha256"], "source_path": reference["source_path"]})
    return rows


def environment():
    from importlib.metadata import version

    return {"python": sys.version.split()[0], **{name: version(name) for name in ("numpy", "scipy", "soundfile", "matplotlib")}}


def study(layout: Layout, learned: bool = True, device: str = "auto"):
    config = load_config()
    output = layout.output / "brush"
    for child in ("keys", "performances", "perturbations"):
        shutil.rmtree(output / child, ignore_errors=True)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    layer, learned_report = None, None
    if learned:
        from .brush_learned import run

        layer, learned_report = run(layout, config, output, device)
    manifest = {"created_at_utc": now(), "config": config, "environment": environment(),
                "references": references(layout, output),
                "keys": keys(layout, config, output),
                "performances": performances(layout, config, output, layer),
                "perturbations": perturbations(layout, config, output)}
    manifest["replay"] = replay(layout, config, output, manifest["performances"])
    if learned_report is not None:
        manifest["learned"] = {key: value for key, value in learned_report.items() if key != "items"} | {"details": "learned.json", "figure": "learned.png"}
    live = output / "live" / "sessions.json"
    manifest["live"] = read_json(live)["sessions"] if live.exists() else []
    manifest["runtime_s"] = round(time.perf_counter() - started, 1)
    write_json(output / "manifest.json", rounded(manifest, 4))
    from .brush_gallery import write_brush_gallery

    write_brush_gallery(output)
    return output / "index.html"


def warm_up(config: dict, directory: Path):
    """Import and exercise the numeric/plotting stack once so the first phrase is not a cold start."""
    import numpy as np
    import soundfile as sf

    from .brush import artwork_png, draw, measure, recognize, synthesize_note

    rate = config["sample_rate"]
    event = {"note": 60, "duration_s": .3, "velocity": 100, "bend": [[0, 0], [1, 0]], "source": {"family": "rise"}}
    audio = np.concatenate([np.zeros(rate // 10), synthesize_note(event, config, {}), np.zeros(rate // 10)])
    measured = measure(audio, rate, config)
    stroke = draw(measured, [recognize(s, config) for s in measured["segments"]], config, "mitoring")
    directory.mkdir(parents=True, exist_ok=True)
    sf.write(directory / "warm-up.wav", audio, rate, subtype="PCM_16")
    artwork_png(directory / "warm-up.png", stroke, config)
    for name in ("warm-up.wav", "warm-up.png"):
        (directory / name).unlink()


def live(layout: Layout, port: str | None, virtual: bool, phrase_gap: float, phrases: int, stone: str, play: bool,
         figures: bool = False):
    """Capture a phrase from a MIDI keyboard; after a silence, render, analyze and draw it."""
    try:
        import mido
    except ImportError as error:
        raise ValueError("Live MIDI needs: uv run --group art --group viz --group midi main.py art brush live") from error
    config = load_config()
    output = layout.output / "brush" / "live"
    output.mkdir(parents=True, exist_ok=True)
    log = output / "sessions.json"
    sessions = read_json(log)["sessions"] if log.exists() else []
    name = "whales-sound-brush"
    warm_up(config, output)
    inputs = mido.open_input(name, virtual=True) if virtual else mido.open_input(port)
    print(f"Listening on {'virtual port ' + name if virtual else port}. Play a phrase; {phrase_gap:.1f} s of silence ends it.", flush=True)
    with inputs:
        for _ in range(phrases):
            timed, held, last = [], set(), None
            while True:
                for message in inputs.iter_pending():
                    moment = time.perf_counter()
                    timed.append((moment, message))
                    if message.type == "note_on" and message.velocity > 0:
                        held.add((message.channel, message.note))
                    elif message.type in ("note_on", "note_off"):
                        held.discard((message.channel, message.note))
                        last = moment
                if timed and not held and last is not None and time.perf_counter() - last >= phrase_gap:
                    break
                time.sleep(.002)
            detected = time.perf_counter()
            events = events_from_messages(timed, config)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            record = perform(layout, events, config, output, f"live-{stamp}", stone, f"Live phrase {stamp}", figure=figures)
            ready = time.perf_counter()
            if play:
                player = shutil.which("pw-play") or shutil.which("paplay") or shutil.which("aplay")
                if player:
                    subprocess.Popen([player, str(output / f"live-{stamp}.wav")])
            sessions.append({"name": f"live-{stamp}", "created_at_utc": now(), "events": rounded(events, 4), "port": name if virtual else port,
                             "stroke_sha256": record["stroke_sha256"], "audio_sha256": record["audio_sha256"], "metrics": record["metrics"],
                             "commands": [s["recognition"]["command"] for s in record["segments"]],
                             "latency_ms": {"phrase_gap_wait": round(1000 * phrase_gap, 1), "processing_after_gap": round(1000 * (ready - detected), 1)} | record["timing_ms"]})
            write_json(log, {"sessions": sessions, "note": "Phrase-level loop: sound is rendered after the phrase ends; no continuous drawing while keys are held."})
            print(f"Drew live-{stamp}: {len(events)} notes → {sessions[-1]['commands']} in {1000 * (ready - detected):.0f} ms after the phrase gap", flush=True)
    return log
