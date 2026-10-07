"""Standalone listening page for the sound brush: Input → Schema → Output."""

import html
from pathlib import Path

from .data import read_json

PALETTE = {"grow": "#2f6f8f", "branch": "#3f8f4f", "fold": "#9a5a2a", "open": "#7a4f9a", "beads": "#b03a5b", "none": "#7d7d7d"}


def escape(value):
    return html.escape(str(value), quote=True)


def badge(command):
    return f'<span class="badge" style="background:{PALETTE.get(command, "#7d7d7d")}">{escape(command)}</span>'


def player(label: str, path: str):
    return f'<div class="player"><span>{escape(label)}</span><audio controls preload="none" src="{escape(path)}"></audio></div>'


def summary_text(segment: dict):
    s = segment["summary"]
    if segment["kind"] == "clicks":
        return f"{s['clicks']} clicks · {s['rate_hz']:.1f}/s · {s['mean_level_dbfs']:.0f} dBFS"
    return f"{s['start_hz'] / 1000:.1f}→{s['end_hz'] / 1000:.1f} kHz · {s['net_octaves']:+.2f} oct · {s['mean_level_dbfs']:.0f} dBFS"


def metric_text(metrics: dict):
    units = metrics["line_units"] + metrics["fold_units"]
    parts = [f"{units:.0f} units of line" if units else ""]
    parts += [f"{metrics[key]} {label if metrics[key] > 1 else label[:-1]}" for key, label in (("openings", "openings"), ("beads", "beads"), ("lifts", "lifts")) if metrics[key]]
    if metrics["tips_max"] > 1:
        parts.append(f"up to {metrics['tips_max']} tips")
    return " · ".join(part for part in parts if part)


def segment_table(record: dict):
    effects = {event["event"]: event for event in record["stroke_events"]}
    rows = []
    for segment in record["segments"]:
        effect = effects[segment["index"]]
        turn = "" if effect["turn_degrees_first_tip"] is None else f"{effect['turn_degrees_first_tip']:+.0f}°"
        width = "" if effect["mean_width_units"] is None else f"{effect['mean_width_units']:.1f}"
        tips = f"{effect['tips_before']}→{effect['tips_after']}" if effect["tips_before"] != effect["tips_after"] else str(effect["tips_after"])
        rows.append(f'''<tr><td>{segment['index']}</td><td>{segment['start_s']:.2f}–{segment['end_s']:.2f} s</td><td>{escape(summary_text(segment))}</td>
<td>{badge(segment['recognition']['command'])}<br><small>{escape(segment['recognition']['reason'])}</small></td>
<td>{'lift · ' if effect['lifted'] else ''}{effect['path_length_units']:.0f} u · {turn} · w {width} · tips {tips}</td></tr>''')
    return f'''<table class="segments"><thead><tr><th>#</th><th>Time</th><th>Measured</th><th>Recognition</th><th>Stroke effect</th></tr></thead><tbody>{''.join(rows)}</tbody></table>'''


def keys_section(manifest: dict):
    rows = []
    for key in manifest["keys"]:
        record = key["record"]
        folder = "keys"
        source = key["source"]
        kind = "Synthesized contour" if "family" in source else "Recording"
        recognized = " ".join(badge(s["recognition"]["command"]) for s in record["segments"]) or "—"
        reasons = "; ".join(s["recognition"]["reason"] for s in record["segments"] if s["kind"] == "tonal")[:220]
        rows.append(f'''<tr><td><b>{escape(key['pitch_class'])}</b></td><td>{escape(key['title'])}<br><small>{kind}</small></td>
<td>{player('Emitted', f"{folder}/{key['slug']}.wav")}{player('Audible guide (÷4)', f"{folder}/{record['files']['guide']}")}</td>
<td>{badge(key['designed_command']) if key['designed_command'] in PALETTE else escape(key['designed_command'])}</td>
<td>{recognized}<br><small>{escape(reasons)}</small></td>
<td><a href="{folder}/{key['slug']}.svg"><img class="thumb" src="{escape(key['thumbnail'])}" alt="Stroke drawn by key {escape(key['pitch_class'])}, coloured by command"></a><small>{metric_text(record['metrics'])}</small></td></tr>''')
    return f'''<section><h2>The keyboard</h2><p>White keys synthesize explicit contours. Black keys play real recordings: three OpenWhistle bottlenose whistles and two DSWP sperm-whale codas. A recording is high-passed at 2 kHz and normalized before velocity gain; it is never pitch-shifted or stretched. Every key below was played for the same hold and velocity and drawn from its emitted audio.</p>
<div class="scroll"><table class="keys"><thead><tr><th>Key</th><th>Sound</th><th>Listen</th><th>Designed command</th><th>Recognized from the waveform</th><th>Stroke</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p><small>The emitted whistles are at 4–20 kHz. The audible guide is resynthesized from the <i>measured</i> contour two octaves lower, with the same timing, so you can hear what the analysis extracted. The brush never reads the guide.</small></p></section>'''


def performance_section(entry: dict):
    record, spec = entry["record"], entry["spec"]
    folder = "performances"
    events = "".join(f'<li><code>{escape(e["token"])}</code> · {escape(e["source"].get("family") or e["source"].get("recording"))}</li>' for e in record["events"])
    learned = ""
    if "learned" in entry:
        agreement = entry["agreement"]
        same = sum(row["contour"] == row["learned"] for row in agreement if row["kind"] == "tonal")
        tonal = sum(row["kind"] == "tonal" for row in agreement)
        pairs = "".join(f'<tr><td>{row["event"]}</td><td>{badge(row["contour"])}</td><td>{badge(row["learned"])}</td></tr>' for row in agreement if row["kind"] == "tonal")
        learned = f'''<figure><a href="{folder}/{escape(entry['learned']['files']['svg'])}"><img src="{folder}/{escape(entry['learned']['files']['svg'])}" alt="Same audio with commands chosen by OpenWhistle embeddings"></a>
<figcaption><b>Learned layer:</b> OpenWhistle chooses the commands; contour, length and width stay measured. Agreement {same}/{tonal} tonal events. <a href="{folder}/{escape(entry['learned']['files']['explained_png'])}">Explained</a></figcaption></figure>
<details><summary>Command per event</summary><table><thead><tr><th>#</th><th>Contour + DTW</th><th>OpenWhistle</th></tr></thead><tbody>{pairs}</tbody></table></details>'''
    return f'''<article class="study"><div class="input"><h3>Input · {escape(spec['title'])}</h3><p>{escape(spec['description'])}</p>
<p><code class="phrase">{escape(spec['phrase'])}</code></p><ol start="0" class="events">{events}</ol>
{player('Emitted (analyzed)', f"{folder}/{entry['name']}.wav")}{player('Audible guide (÷4)', f"{folder}/{record['files']['guide']}")}
<p><small>{record['duration_s']:.1f} s · {record['sample_rate']:,} Hz · audio SHA-256 {record['audio_sha256'][:12]}…</small></p></div>
<div class="mapping"><h3>Schema · sound → recognition → consequence</h3><a href="{folder}/{escape(record['files']['explained_png'])}"><img src="{folder}/{escape(record['files']['explained_png'])}" alt="Spectrogram with measured contour, recognized commands and numbered stroke"></a>
{segment_table(record)}<p><small><a href="{folder}/{escape(record['files']['controls'])}">Frame-level controls</a> · <a href="{folder}/{escape(record['files']['stroke'])}">Stroke geometry</a> · <a href="{folder}/{escape(record['performance'])}">Key events</a></small></p></div>
<div class="outputs"><h3>Output · stroke around the stone</h3><figure><a href="{folder}/{escape(record['files']['svg'])}"><img src="{folder}/{escape(record['files']['svg'])}" alt="Silver stroke drawn from the performance"></a>
<figcaption>Contour layer · {escape(metric_text(record['metrics']))} · stroke SHA-256 {record['stroke_sha256'][:12]}…</figcaption></figure>{learned}</div></article>'''


def perturbation_section(manifest: dict):
    cards = []
    for entry in manifest["perturbations"]:
        c = entry["comparison"]
        facts = [f"commands {' '.join(c['commands'][0])} → {' '.join(c['commands'][1])}",
                 f"turn {c['turn_degrees_first_event'][0]:+.0f}° → {c['turn_degrees_first_event'][1]:+.0f}°" if None not in c["turn_degrees_first_event"] else "",
                 f"path {c['path_length_units'][0]:.0f} → {c['path_length_units'][1]:.0f} units",
                 f"width {c['mean_width_units'][0]:.1f} → {c['mean_width_units'][1]:.1f}",
                 f"lifts {c['lifts'][0]} → {c['lifts'][1]}",
                 "identical stroke" if c["stroke_identical"] else "stroke changed"]
        cards.append(f'''<article class="card"><h3>{escape(entry['feature'])}</h3><a href="{escape(entry['figure'])}"><img src="{escape(entry['figure'])}" alt="{escape(entry['feature'])}: base and changed strokes"></a>
{player('Base', f"perturbations/{entry['id']}-base.wav")}{player('Changed', f"perturbations/{entry['id']}-changed.wav")}
<p><code>{escape(entry['base'])}</code> → <code>{escape(entry['changed'])}</code></p><p><b>Expected:</b> {escape(entry['expect'])}</p><p><b>Measured:</b> {escape(' · '.join(f for f in facts if f))}</p></article>''')
    return f'''<section><h2>One acoustic change at a time</h2><p>Each pair differs in a single performed feature; everything else, including the mapping, is fixed. There is no random seed: the procedural brush is deterministic, so every difference below comes from the audio.</p><div class="cards">{''.join(cards)}</div></section>'''


def replay_section(manifest: dict):
    rows = "".join(f'''<tr><td>{escape(r['performance'])}</td><td><code>{r['stroke_sha256'][:12]}</code></td><td><code>{r['anonymous_copy_stroke_sha256'][:12]}</code></td><td><code>{r['fresh_process_stroke_sha256'][:12]}</code></td><td><code>{r['rerendered_stroke_sha256'][:12]}</code></td><td>{'yes' if r['identical'] else '<b>NO</b>'}</td><td><code>{r['control_stroke_sha256'][:12]}</code> ({'differs' if r['control_differs'] else '<b>same</b>'}, width {r['control_width_change_units']:+.3f})</td></tr>''' for r in manifest["replay"])
    return f'''<section><h2>Replay: identical audio → identical stroke</h2><p>The stroke hash is recomputed from the saved WAV copied under an anonymous name (no key data nearby), in a fresh process through <code>art brush draw</code>, and after re-rendering the phrase from its key events. The control plays the first note one velocity step quieter: different audio must give a different stroke.</p>
<div class="scroll"><table><thead><tr><th>Performance</th><th>Original</th><th>Anonymous copy</th><th>Fresh process</th><th>Re-rendered</th><th>Identical</th><th>Velocity −1 control</th></tr></thead><tbody>{rows}</tbody></table></div></section>'''


def learned_section(manifest: dict):
    learned = manifest.get("learned")
    if not learned:
        return ""
    rows = []
    for condition, entry in learned["summary"].items():
        cells = []
        for method in ("contour", "learned"):
            e = entry[method]
            correct = f"{e['correct']}/{e['command_items']}" if e["command_items"] else "—"
            cells.append(f"<td>{correct}</td><td>{e['false_accepts']}/{e['non_command_items']}</td>")
        rows.append(f"<tr><td>{escape(condition)}</td>{''.join(cells)}</tr>")
    representations = sorted(learned["representations_compared"], key=lambda r: -r["loo_accuracy"])[:4]
    picked = learned["selected"]
    return f'''<section><h2>A 2026 dolphin encoder as an additional layer</h2>
<p><a href="https://huggingface.co/dolphinteam/OpenWhistle-Wav2Vec2.0">OpenWhistle Wav2Vec2</a> (weights committed 4 May 2026; <a href="https://arxiv.org/abs/2609.34839">arXiv:2609.34839</a>) is a frozen self-supervised encoder, not a command recognizer. We enrolled {learned['enrollment']['examples']} labelled examples of our four designed contours and assign each sound to the nearest class centroid. The layer and pooling were chosen by leave-one-out accuracy on enrollment only: <b>layer {picked['layer']}, {escape(picked['pooling'])}</b>. Time-averaged embeddings scored near chance (they cannot tell a rise from a fall); order-preserving chunks helped.</p>
<figure><a href="learned.png"><img src="learned.png" alt="Accuracy of measured contour and OpenWhistle layers across conditions, and a PCA of embeddings"></a></figure>
<div class="scroll"><table><thead><tr><th rowspan="2">Condition</th><th colspan="2">Measured contour + DTW</th><th colspan="2">OpenWhistle + centroids</th></tr><tr><th>Commands correct</th><th>Non-commands accepted</th><th>Commands correct</th><th>Non-commands accepted</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p><small>Best enrollment representations: {escape('; '.join(f"layer {r['layer']} {r['pooling']} {r['loo_accuracy']:.0%}" for r in representations))}. Threshold cosine {learned['threshold_cosine']:.3f}, margin {learned['margin_cosine']}. Model license: {escape(learned['model']['license'])}. Training population: {escape(learned['model']['training_population'])}. Synthetic sine contours are out of domain; a fine-tuned head, more enrollment or negative examples could change this result. <a href="learned.json">Every item and score</a>.</small></p></section>'''


def latency_section(manifest: dict):
    rows = []
    for entry in manifest["performances"]:
        t = entry["record"]["timing_ms"]
        rows.append(f"<tr><td>{escape(entry['name'])}</td><td>{entry['record']['duration_s']:.1f} s</td><td>{t.get('synthesize_ms', 0):.0f}</td><td>{t['measure_ms']:.0f}</td><td>{t['recognize_ms']:.0f}</td><td>{t['draw_ms']:.0f}</td><td>{t['render_ms']:.0f}</td></tr>")
    live = "".join(f"<tr><td>{escape(s['name'])}</td><td>{escape(' '.join(s['commands']))}</td><td>{s['latency_ms']['phrase_gap_wait']:.0f}</td><td>{s['latency_ms']['processing_after_gap']:.0f}</td></tr>" for s in manifest.get("live", []))
    live_table = f'''<h3>Live MIDI phrases</h3><table><thead><tr><th>Phrase</th><th>Commands</th><th>Gap wait (ms)</th><th>Processing after gap (ms)</th></tr></thead><tbody>{live}</tbody></table>''' if live else "<p>No live MIDI phrase has been captured yet.</p>"
    return f'''<section><h2>Latency on this machine</h2><p>This prototype works phrase by phrase, like a CHAT detection window: a phrase ends after a silence, then its audio is rendered, measured, recognized and drawn. It does not draw continuously while a key is held.</p>
<div class="scroll"><table><thead><tr><th>Performance</th><th>Audio</th><th>Synthesize (ms)</th><th>Measure</th><th>Recognize</th><th>Draw</th><th>Render SVG/PNG/figure</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>{live_table}</section>'''


def livia_section(manifest: dict):
    effects = manifest["config"]["effects"]
    commands = {command: family for family, command in manifest["config"]["commands"].items()} | {"beads": "clicks"}
    rows = "".join(f'<tr><td>{badge(command)}</td><td>{escape(manifest["config"]["families"][commands[command]]["title"]) if command in commands else "—"}</td><td>{escape(effect["description"])}</td><td>{escape(effect["livia"])}</td></tr>' for command, effect in effects.items())
    figures = "".join(f'<figure><img src="{escape(r["image"])}" alt="{escape(r["title"])}"><figcaption><b>{escape(r["title"])}</b><br>{escape(r["connection"])}</figcaption></figure>' for r in manifest["references"])
    return f'''<section><h2>Livia's vocabulary instead of a cage</h2><p>The earlier rib cocoon measured sound faithfully but enclosed the stone. Here every stroke starts on the stone's rim and moves outward; the stone stays exposed. Effects borrow material problems from Livia's pieces: Mycelium drains porous opal through open channels, Roots grew from an algorithm, Mitoring folds silver like cristae. These correspondences are our proposals, not her rules.</p>
<div class="references">{figures}</div><div class="scroll"><table><thead><tr><th>Command</th><th>Designed sound</th><th>Effect on the drawing</th><th>Connection to Livia's work</th></tr></thead><tbody>{rows}</tbody></table></div>
<p><small>Continuous controls apply to every tonal sound, recognized or not: heading turns {manifest['config']['drawing']['turn_degrees_per_octave']}° per octave of pitch change (rising turns left, mirrored on branch pairs), the brush advances {manifest['config']['drawing']['speed_units_per_s']} units per second, ridge level {manifest['config']['drawing']['width_level_dbfs'][0]}…{manifest['config']['drawing']['width_level_dbfs'][1]} dBFS sets width {manifest['config']['drawing']['width_units'][0]}…{manifest['config']['drawing']['width_units'][1]} units, and {manifest['config']['drawing']['lift_gap_s']} s of silence lifts the brush to the next point on the rim (golden-angle steps). Absolute register is deliberately unmapped: WDP observed that dolphins may reproduce a whistle in a shifted frequency range.</small></p></section>'''


def write_brush_gallery(output: Path):
    manifest = read_json(output / "manifest.json")
    pipeline = ["Key or recording", "Emitted waveform (saved)", "Measured ridge contour and click onsets",
                "Recognition: designed vocabulary, with rejection", "Consequence: stroke effect + continuous controls"]
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sound Brush Study</title><style>
*{{box-sizing:border-box}}body{{font:16px/1.5 system-ui,sans-serif;background:#f4f0e5;color:#39352f;margin:0;padding:32px}}header,main{{max-width:1440px;margin:auto}}h1{{font-size:34px;margin-bottom:8px}}h2{{font-size:26px;margin-top:0}}h3{{font-size:18px;margin-top:0}}
.pipeline{{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}}.pipeline span{{background:#e6dcc8;padding:10px 12px;border-radius:8px}}.pipeline span+span:before{{content:'→ ';color:#81602b}}
section{{margin:46px 0}}.study{{display:grid;grid-template-columns:minmax(220px,.8fr) minmax(320px,1.6fr) minmax(260px,1fr);gap:24px;background:white;padding:24px;margin:24px 0;border-radius:12px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}}.card{{background:white;border-radius:12px;padding:18px}}.references{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin:16px 0}}.references img{{aspect-ratio:1;object-fit:contain;background:white}}
img{{display:block;width:100%;border-radius:4px}}.thumb{{width:140px;background:#f4f0e5}}figure{{margin:0 0 14px}}figcaption,small{{font-size:13px}}audio{{width:100%;height:34px}}.player{{margin:6px 0}}.player span{{font-size:13px;display:block}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5dfd2;padding:5px;text-align:left;vertical-align:top}}.scroll{{overflow-x:auto}}.badge{{color:white;border-radius:4px;padding:1px 7px;font-size:13px;white-space:nowrap}}
.evidence{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}.evidence div{{background:white;border-radius:10px;padding:14px}}code{{overflow-wrap:anywhere}}.phrase{{background:#efe7d6;padding:2px 4px}}a{{color:#81602b}}.events{{font-size:13px;padding-left:22px}}
@media(max-width:900px){{.study{{grid-template-columns:1fr}}body{{padding:16px}}}}
</style></head><body><header><p><a href="../index.html">← All experiments</a></p><h1>Sound brush: a CHAT-style loop for drawing</h1>
<p>A person plays a keyboard. Each key emits a recorded whistle or an explicitly synthesized contour. The brush listens to the <b>emitted waveform only</b>: it measures the contour, recognizes a small designed vocabulary and draws the consequence. Replaying the same audio file reproduces the same stroke without the keyboard.</p>
<div class="pipeline">{''.join(f'<span>{escape(step)}</span>' for step in pipeline)}</div>
<div class="evidence"><div><b>Documented interface.</b> CHAT pairs designed whistles with play objects; a wearable computer recognizes possible mimics and alerts the diver. <a href="https://www.wilddolphinproject.org/our-research/chat-research/">WDP</a> · <a href="https://www.cc.gatech.edu/news/video-illustrates-interactive-tech-created-help-understand-dolphin-communication">Georgia Tech</a> · <a href="https://www.youtube.com/watch?v=YhopeQKbpZA">explainer video</a></div>
<div><b>Prototype demonstration.</b> The Spring 2025 Dolphin CHAT Bot turns whistles into thruster commands, demonstrated in controlled tanks; live dolphin trials are future plans. <a href="https://expo.gatech.edu/prod1/portal/portal.jsp?c=17462&amp;g=413665329&amp;id=417265676&amp;p=413142918">Project page</a> · <a href="https://www.youtube.com/watch?v=kbzZdFaaAwk">video</a></div>
<div><b>Animal learning.</b> In 2013–2016 field sessions wild spotted dolphins imitated CHAT's computer-generated whistles but showed no functional understanding of the labels. <a href="https://doi.org/10.26451/abc.11.02.02.2024">Herzing et al. 2024</a>. This brush is human-operated; it tests nothing about dolphins.</div></div>
<p><small>Read with: <a href="../../../docs/sound-brush.md">sound-brush report</a> · <a href="../../../docs/chat-sound-interface.md">CHAT report</a> · <a href="manifest.json">full manifest</a>. Created {escape(manifest['created_at_utc'])}.</small></p></header><main>
{livia_section(manifest)}{keys_section(manifest)}<section><h2>Performances</h2>{''.join(performance_section(entry) for entry in manifest['performances'])}</section>
{perturbation_section(manifest)}{replay_section(manifest)}{learned_section(manifest)}{latency_section(manifest)}
</main></body></html>
'''
    (output / "index.html").write_text(page, encoding="utf-8")
    return output / "index.html"
