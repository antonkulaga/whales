"""Input → schema → output gallery for the Hardata II inscription pilot."""

import html
import math
from pathlib import Path

from .data import ROOT, digest, read_json, write_json

LIVIA = ROOT.parent / "livia"
HARDATA = Path("assets/hard data 2021/HARD DATA.jpg")
FAMILY_COLORS = {  # reference categorical order, validated for adjacent use
    "contour": "var(--s1)", "contour + sea": "var(--s2)", "relief": "var(--s3)", "DAC codec": "var(--s4)",
    "amplitude (Hardata 2021)": "var(--s5)", "control": "var(--muted)",
}
SHOWN = ["contour-32x8", "contour-128x10-sea", "reversed-32x8", "flat-tone", "relief-16x16x2", "relief-64x48x4",
         "amplitude-32x3", "dac-1", "dac-4", "groove-0.1mm", "groove-0.45mm"]
LABELS = {
    "original": "Original recording", "contour-8x8": "Contour 8 pts × 8 bit", "contour-16x8": "Contour 16 × 8",
    "contour-32x4": "Contour 32 × 4", "contour-32x8": "Contour 32 × 8", "contour-64x8": "Contour 64 × 8",
    "contour-128x10": "Contour 128 × 10", "contour-32x8-sea": "Contour 32 × 8 + sea bed",
    "contour-128x10-sea": "Contour 128 × 10 + sea bed", "reversed-32x8": "Reversed contour (control)",
    "flat-tone": "Flat tone, same span and mean pitch (control)", "relief-8x8x2": "Relief 8 × 8 × 2 bit",
    "relief-16x16x2": "Relief 16 × 16 × 2", "relief-32x24x3": "Relief 32 × 24 × 3", "relief-64x48x4": "Relief 64 × 48 × 4",
    "amplitude-32x3": "Amplitude only (Hardata 2021 rule)", "dac-1": "DAC codec, 1 codebook", "dac-2": "DAC, 2 codebooks",
    "dac-4": "DAC, 4 codebooks", "dac-9": "DAC, 9 codebooks",
}


def e(value):
    return html.escape(str(value), quote=True)


def label(key):
    if key.startswith("groove-"):
        return f"Silver groove, {key[7:-2]} mm blur"
    return LABELS.get(key, key)


def verdicts(report):
    """Apply the registered predictions' own thresholds to the OpenWhistle listener."""
    listener = report["listeners"]["OpenWhistle Wav2Vec2"]
    r = {key: value["macro_f1"] for key, value in listener["results"].items()}
    c = listener["comparisons"]
    chance = 1 / len(report["dataset"]["label_names"])
    out = {}
    out["H1"] = ("supported" if r["contour-32x8"] >= 0.7 * r["original"] else "not supported",
                 f"contour 32×8 {r['contour-32x8']:.3f} vs original {r['original']:.3f} ({r['contour-32x8'] / r['original']:.0%} retained)")

    def paired(name):
        low, high = c[name]["ci95"]
        return "supported" if low > 0 else ("not supported" if high < 0 else "inconclusive")
    relief, dac = paired("contour-32x8 vs relief-16x16x2"), paired("contour-32x8 vs dac-1")
    h2 = "supported" if relief == dac == "supported" else ("not supported" if "not supported" in (relief, dac) else "inconclusive")
    out["H2"] = (h2, f"vs relief 16×16×2: {c['contour-32x8 vs relief-16x16x2']['difference']:+.3f} "
                     f"[{c['contour-32x8 vs relief-16x16x2']['ci95'][0]:+.3f}, {c['contour-32x8 vs relief-16x16x2']['ci95'][1]:+.3f}]; "
                     f"vs DAC 1 codebook: {c['contour-32x8 vs dac-1']['difference']:+.3f} "
                     f"[{c['contour-32x8 vs dac-1']['ci95'][0]:+.3f}, {c['contour-32x8 vs dac-1']['ci95'][1]:+.3f}]")
    out["H3"] = ("supported" if r["amplitude-32x3"] <= chance + 0.10 else "not supported",
                 f"amplitude only {r['amplitude-32x3']:.3f}; chance ≈ {chance:.3f}")
    advantage = r["contour-32x8"] - chance
    lost = all(r[key] - chance <= 0.5 * advantage for key in ("reversed-32x8", "flat-tone"))
    out["H4"] = ("supported" if lost and advantage > 0 else "not supported",
                 f"contour {r['contour-32x8']:.3f}, reversed {r['reversed-32x8']:.3f}, flat tone {r['flat-tone']:.3f}")
    grooves = sorted((value["blur_mm"], r[key]) for key, value in report["grooves"].items())
    smooth = all(a[1] - b[1] <= 0.2 for a, b in zip(grooves, grooves[1:]))
    groove_01 = r["groove-0.1mm"]
    out["H5"] = ("supported" if groove_01 >= 0.9 * r["contour-128x10"] and smooth else "not supported",
                 f"groove at 0.1 mm {groove_01:.3f} vs contour 128×10 {r['contour-128x10']:.3f}; by blur: "
                 + ", ".join(f"{blur:g} mm {score:.3f}" for blur, score in grooves))
    return out


def legend_rows(families, left, width):
    """Wrap legend entries (swatch + label) into rows that fit the chart width."""
    rows, row, x = [], [], left
    for family in families:
        w = 26 + 6.4 * len(family)
        if row and x + w > width - 8:
            rows.append(row)
            row, x = [], left
        row.append((x, family))
        x += w + 14
    return rows + ([row] if row else [])


def rate_chart(report, listener, width=640, height=360):
    """Macro-F1 against inscribed bits (log x), one line per encoding family; hover titles on points."""
    results = report["listeners"][listener]["results"]
    conditions = [c for c in report["conditions"] if c["family"] not in ("silver groove (simulated)",)]
    left, right, top, bottom = 56, 132, 20, 44
    order = list(dict.fromkeys(c["family"] for c in conditions if c["key"] != "original"))
    legend = legend_rows(order, left, width)
    plot_height = height
    height = plot_height + 18 * len(legend) + 8
    xs = [c["median_bits"] for c in conditions]
    x_min, x_max = 10 ** math.floor(math.log10(min(xs))), 10 ** math.ceil(math.log10(max(xs)))
    px = lambda bits: left + (math.log10(bits) - math.log10(x_min)) / (math.log10(x_max) - math.log10(x_min)) * (width - left - right)
    py = lambda score: top + (1 - score) * (plot_height - top - bottom)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{e(listener)}: macro-F1 against bits per whistle">']
    for tick in (0, 0.25, 0.5, 0.75, 1.0):
        parts.append(f'<line x1="{left}" x2="{width - right}" y1="{py(tick):.1f}" y2="{py(tick):.1f}" class="grid"/><text x="{left - 8}" y="{py(tick) + 4:.1f}" class="tick" text-anchor="end">{tick:.2f}</text>')
    power = int(math.log10(x_min))
    while 10 ** power <= x_max:
        x = px(10 ** power)
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{plot_height - bottom}" class="grid"/><text x="{x:.1f}" y="{plot_height - bottom + 16}" class="tick" text-anchor="middle">{10 ** power:,}</text>')
        power += 1
    parts.append(f'<text x="{(left + width - right) / 2}" y="{plot_height - 8}" class="axis" text-anchor="middle">Inscribed bits per whistle (median, log scale)</text>')
    parts.append(f'<text x="14" y="{(top + plot_height - bottom) / 2}" class="axis" text-anchor="middle" transform="rotate(-90 14 {(top + plot_height - bottom) / 2})">Macro-F1, 6 whistle types</text>')
    chance = 1 / len(report["dataset"]["label_names"])
    original = results["original"]["macro_f1"]
    for value, text in ((original, f"original audio {original:.2f}"), (chance, f"chance ≈ {chance:.2f}")):
        parts.append(f'<line x1="{left}" x2="{width - right}" y1="{py(value):.1f}" y2="{py(value):.1f}" class="reference"/><text x="{width - right + 6}" y="{py(value) + 4:.1f}" class="note">{e(text)}</text>')
    families = {}
    for condition in conditions:
        if condition["key"] != "original":
            families.setdefault(condition["family"], []).append(condition)
    for family, members in families.items():
        members = sorted(members, key=lambda c: c["median_bits"])
        color = FAMILY_COLORS.get(family, "var(--muted)")
        if family != "control" and len(members) > 1:
            points = " ".join(f'{px(c["median_bits"]):.1f},{py(results[c["key"]]["macro_f1"]):.1f}' for c in members)
            parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        for c in members:
            score = results[c["key"]]
            low, high = score["macro_f1_ci95"]
            x, y = px(c["median_bits"]), py(score["macro_f1"])
            parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{py(high):.1f}" y2="{py(low):.1f}" stroke="{color}" stroke-width="1" opacity=".55"/>')
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="var(--surface)" stroke-width="2"><title>{e(label(c["key"]))}: macro-F1 {score["macro_f1"]:.3f} (95% CI {low:.3f}–{high:.3f}), accuracy {score["accuracy"]:.3f}, median {c["median_bits"]:,.0f} bits</title></circle>')
    # Legend rows under the axis title; identity never relies on line color alone.
    for k, row in enumerate(legend):
        y = plot_height + 10 + k * 18
        for x, family in row:
            parts.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{FAMILY_COLORS.get(family, "var(--muted)")}"/><text x="{x + 15}" y="{y}" class="legend">{e(family)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def groove_chart(report, listener, width=640, height=260):
    results = report["listeners"][listener]["results"]
    grooves = sorted((value["blur_mm"], key) for key, value in report["grooves"].items())
    left, right, top, bottom = 56, 168, 20, 44
    slot = {blur: k for k, (blur, _) in enumerate(grooves)}
    px = lambda blur: left + 20 + slot[blur] / max(1, len(grooves) - 1) * (width - left - right - 40)
    py = lambda score: top + (1 - score) * (height - top - bottom)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{e(listener)}: macro-F1 of the decoded silver groove against casting blur">']
    for tick in (0, 0.25, 0.5, 0.75, 1.0):
        parts.append(f'<line x1="{left}" x2="{width - right}" y1="{py(tick):.1f}" y2="{py(tick):.1f}" class="grid"/><text x="{left - 8}" y="{py(tick) + 4:.1f}" class="tick" text-anchor="end">{tick:.2f}</text>')
    for blur, _ in grooves:
        parts.append(f'<text x="{px(blur):.1f}" y="{height - bottom + 16}" class="tick" text-anchor="middle">{blur:g}</text>')
    parts.append(f'<text x="{(left + width - right) / 2}" y="{height - 6}" class="axis" text-anchor="middle">Simulated print + cast + scan blur, σ in mm</text>')
    for key, text in (("contour-128x10", "digital contour 128×10"), ("original", "original audio")):
        value = results[key]["macro_f1"]
        parts.append(f'<line x1="{left}" x2="{width - right}" y1="{py(value):.1f}" y2="{py(value):.1f}" class="reference"/><text x="{width - right + 6}" y="{py(value) + 4:.1f}" class="note">{e(text)} {value:.2f}</text>')
    points = " ".join(f'{px(blur):.1f},{py(results[key]["macro_f1"]):.1f}' for blur, key in grooves)
    parts.append(f'<polyline points="{points}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>')
    for blur, key in grooves:
        score = results[key]
        cap = report["grooves"][key]
        parts.append(f'<circle cx="{px(blur):.1f}" cy="{py(score["macro_f1"]):.1f}" r="5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"><title>σ = {blur:g} mm: macro-F1 {score["macro_f1"]:.3f} (95% CI {score["macro_f1_ci95"][0]:.3f}–{score["macro_f1_ci95"][1]:.3f}); a binary-pit code at this resolution would hold about {cap["payload_bits"]:,} bits</title></circle>')
    parts.append("</svg>")
    return "".join(parts)


def contour_svg(row, width=300, height=150):
    """Annotated F0 contour and the contour read back from the simulated band."""
    times, freqs = row["f0_time"], row["f0_hz"]
    duration = max(row["duration_s"], 1e-3)
    lo, hi = math.log2(2000), math.log2(22050)
    px = lambda t: 8 + t / duration * (width - 16)
    py = lambda f: 8 + (1 - (math.log2(f) - lo) / (hi - lo)) * (height - 28)
    original = " ".join(f"{px(t):.1f},{py(f):.1f}" for t, f in zip(times, freqs))
    read = " ".join(f"{px(t):.1f},{py(f):.1f}" for t, f in zip(row["groove_read_time"], row["groove_read_hz"]))
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Annotated whistle contour and the contour read from the simulated band">'
            f'<rect x="8" y="8" width="{width - 16}" height="{height - 28}" class="frame"/>'
            f'<polyline points="{original}" fill="none" stroke="var(--s1)" stroke-width="4" stroke-opacity=".45" stroke-linecap="round"/>'
            f'<polyline points="{read}" fill="none" stroke="var(--s2)" stroke-width="1.5" stroke-dasharray="4 3"/>'
            f'<text x="8" y="{height - 4}" class="tick">0 s</text><text x="{width - 8}" y="{height - 4}" class="tick" text-anchor="end">{duration:.2f} s</text>'
            f'<text x="12" y="20" class="tick">22 kHz</text><text x="12" y="{height - 24}" class="tick">2 kHz</text></svg>')


def heightmap_png(interim: Path, stem: str, destination: Path):
    """Hillshaded unrolled band after simulated casting, as a PNG."""
    import numpy as np
    from PIL import Image

    data = np.load(interim / f"{stem}-groove.npz")["scanned"]
    surface = -data
    gy, gx = np.gradient(surface, 0.02)
    shade = np.clip(0.55 + 0.45 * (-gx * 0.6 - gy * 0.8) / np.sqrt(1 + gx ** 2 + gy ** 2), 0, 1)
    rgb = (np.stack([shade * 205 + 40, shade * 205 + 40, shade * 210 + 42], -1)).astype(np.uint8)
    image = Image.fromarray(rgb[::-1])
    image = image.resize((min(900, image.width), max(60, round(image.height * min(900, image.width) / image.width))))
    image.save(destination)
    return destination.name


def write_gallery(results_path: Path):
    report = read_json(results_path)
    out = results_path.parent
    interim = out.parent.parent / "interim" / "inscription"
    (out / "references").mkdir(exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    reference = ""
    if (LIVIA / HARDATA).exists():
        target = out / "references" / "hardata-2021.jpg"
        from PIL import Image
        with Image.open(LIVIA / HARDATA) as image:
            image.convert("RGB").resize((min(1200, image.width), round(image.height * min(1200, image.width) / image.width))).save(target, quality=88)
        write_json(out / "references" / "provenance.json", {"source": str(LIVIA / HARDATA), "sha256": digest(LIVIA / HARDATA),
                                                            "role": "Artist's original 2021 work; displayed for context, not generated."})
        reference = (f'<figure class="hardata"><img src="references/hardata-2021.jpg" alt="Livia Zaharia, Hardata (2021): a cylinder engraved with a QR code and a sound-amplitude pattern">'
                     f'<figcaption><b>Livia Zaharia, Hardata, 2021</b> · original work, first prize at Hyper Form (Lapsus, Timișoara). Its board notes the sound pattern "has, for the moment, no way of being played". '
                     f'<a href="references/provenance.json">Source path and hash</a></figcaption></figure>')
    listener = "OpenWhistle Wav2Vec2"
    v = verdicts(report)
    write_json(out / "verdicts.json", {key: {"verdict": value[0], "evidence": value[1], "prediction": report["predictions"][key]} for key, value in v.items()})
    prediction_rows = "".join(f'<tr><td>{key}</td><td>{e(report["predictions"][key])}</td><td><b>{e(value[0])}</b></td><td>{e(value[1])}</td></tr>' for key, value in v.items())
    charts = "".join(f'<figure class="chart"><figcaption><b>{e(name)} listener</b> · probe layer {report["listeners"][name]["probe"]["layer"]}, C = {report["listeners"][name]["probe"]["C"]}, validation macro-F1 {report["listeners"][name]["probe"]["validation_macro_f1"]:.3f}</figcaption>{rate_chart(report, name)}</figure>' for name in report["listeners"])
    table_rows = []
    for condition in report["conditions"]:
        cells = "".join(f'<td>{report["listeners"][name]["results"][condition["key"]]["macro_f1"]:.3f} <small>[{report["listeners"][name]["results"][condition["key"]]["macro_f1_ci95"][0]:.2f}–{report["listeners"][name]["results"][condition["key"]]["macro_f1_ci95"][1]:.2f}]</small></td>' for name in report["listeners"])
        table_rows.append(f'<tr><td>{e(condition["family"])}</td><td>{e(label(condition["key"]))}</td><td>{condition["median_bits"]:,.0f}</td>{cells}</tr>')
    headers = "".join(f"<th>{e(name)} macro-F1 [95% CI]</th>" for name in report["listeners"])
    examples = []
    labels = report["dataset"]["label_names"]
    probs = report["listeners"][listener]["example_probabilities"]
    for k, row in enumerate(report["examples"]):
        truth = labels.index(row["label"])
        png = heightmap_png(interim, row["id"], out / "figures" / f"{row['id']}-band.png") if (interim / f"{row['id']}-groove.npz").exists() else None
        schema_rows = []
        for key in ["original"] + SHOWN:
            p = probs[key][row["id"]]
            top = max(range(len(p)), key=p.__getitem__)
            schema_rows.append(f'<tr><td>{e(label(key))}</td><td>{row["bits"][key]:,}</td><td>{e(labels[top])}</td><td>{p[truth]:.2f}</td></tr>')
        players = []
        for key in SHOWN:
            audio_id = f"a-{k}-{key}"
            players.append(f'<div class="player"><button type="button" data-audio="{audio_id}">▶ {e(label(key))}</button><audio id="{audio_id}" data-rate-group="g{k}" preload="none" controls src="audio/{e(row["audio"][key])}"></audio></div>')
        band = f'<figure><img src="figures/{e(png)}" alt="Unrolled silver band with the engraved contour groove after simulated 0.1 mm casting blur"><figcaption>Unrolled band, 0.1 mm simulated blur · <a href="{e(row["mesh"])}">STL ring band</a> ({row["mesh_triangles"]:,} triangles, mm)</figcaption></figure>' if png else ""
        examples.append(f'''<article class="study"><div class="input"><h3>Input · {e(row["label"])}</h3><p>{e(row["id"])} · session {e(row["session"])} · {row["duration_s"]:.2f} s</p>
<label>Listening <select data-rate-group="g{k}"><option value="0.5" selected>Half speed · one octave lower</option><option value="1">Original speed and pitch</option></select></label>
<div class="player"><button type="button" data-audio="o-{k}">▶ Original recording</button><audio id="o-{k}" data-rate-group="g{k}" preload="none" controls src="audio/{e(row["audio"]["original_playback"])}"></audio></div>
{contour_svg(row)}<p><small><span class="key s1"></span> annotated F0 (confidence ≥ 0.3) · <span class="key s2"></span> read back from the simulated band. Playback copies are peak-normalized; analysis used raw amplitudes.</small></p></div>
<div class="mapping"><h3>Schema · bits and the listener's answer</h3><table><thead><tr><th>Inscription</th><th>Bits</th><th>Probe's top type</th><th>p(true)</th></tr></thead><tbody>{"".join(schema_rows)}</tbody></table></div>
<div class="outputs"><h3>Output · decoded sound and the band</h3>{band}<div class="players">{"".join(players)}</div></div></article>''')
    matched_section = ""
    if (out / "matched.json").exists():
        matched = read_json(out / "matched.json")
        main = report["listeners"][matched["listener"]]["results"]
        rows = "".join(f'<tr><td>{e(label(key))}</td><td>{main[key]["macro_f1"]:.3f}</td><td>{value["macro_f1"]:.3f} <small>[{value["macro_f1_ci95"][0]:.2f}–{value["macro_f1_ci95"][1]:.2f}]</small></td><td>{main["original"]["macro_f1"]:.3f}</td></tr>'
                       for key, value in matched["results"].items())
        matched_section = (f'<section><h2>Lost information or domain shift? (exploratory)</h2><p>{e(matched["note"])} A probe that only ever heard original recordings may misjudge clean tones even when their contour carries the type. Training on decoded whistles of the same condition removes that mismatch.</p>'
                           f'<table><thead><tr><th>Condition</th><th>Probe trained on originals</th><th>Probe trained on decoded audio [95% CI]</th><th>Original audio</th></tr></thead><tbody>{rows}</tbody></table><p><a href="matched.json">matched.json</a></p></section>')
    counts = report["counts"]
    groove_figure = f'<figure class="chart"><figcaption><b>{e(listener)} listener</b> · contour decoded from a simulated cast band</figcaption>{groove_chart(report, listener)}</figure>'
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hardata II pilot</title><style>
:root{{color-scheme:light;--bg:#f4f0e5;--surface:#ffffff;--ink:#2f2b26;--ink2:#5b554b;--muted:#8a8478;--rule:#e4ddcf;--accent:#81602b;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#151412;--surface:#1f1e1b;--ink:#f3efe6;--ink2:#c3c2b7;--muted:#8f8b80;--rule:#383835;--accent:#d7a85a;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#151412;--surface:#1f1e1b;--ink:#f3efe6;--ink2:#c3c2b7;--muted:#8f8b80;--rule:#383835;--accent:#d7a85a;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181}}
*{{box-sizing:border-box}}body{{font:16px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--ink);margin:0;padding:32px 16px}}header,main{{max-width:1380px;margin:auto}}h1{{font-size:32px;margin:0 0 8px}}h2{{font-size:24px;margin-top:48px}}h3{{font-size:17px;margin-top:0}}
.pipeline{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}}.pipeline span{{background:var(--surface);border:1px solid var(--rule);padding:10px 12px;border-radius:8px}}.pipeline span+span:before{{content:'→ ';color:var(--accent)}}
.study{{display:grid;grid-template-columns:minmax(220px,1fr) minmax(260px,1.1fr) minmax(280px,1.4fr);gap:24px;background:var(--surface);padding:22px;margin:22px 0;border-radius:12px}}
.charts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}}.chart{{background:var(--surface);border-radius:12px;padding:14px;margin:0;max-width:760px}}svg{{width:100%;height:auto;display:block}}
.grid{{stroke:var(--rule);stroke-width:1}}.reference{{stroke:var(--muted);stroke-width:1;stroke-dasharray:4 3}}.frame{{fill:none;stroke:var(--rule)}}.tick,.note,.legend{{font-size:11px;fill:var(--ink2)}}.axis{{font-size:12px;fill:var(--ink2)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{border-bottom:1px solid var(--rule);padding:4px 6px;text-align:left;vertical-align:top}}td:nth-child(n+2){{font-variant-numeric:tabular-nums}}
.hardata{{max-width:680px;margin:20px 0}}img{{display:block;max-width:100%;border-radius:6px}}figcaption,small{{font-size:13px;color:var(--ink2)}}a{{color:var(--accent)}}
button{{cursor:pointer;border:0;border-radius:6px;background:var(--accent);color:#fff;font:inherit;font-size:13px;padding:6px 12px;margin:6px 0 2px;text-align:left}}audio{{display:block;width:100%;height:32px}}.players{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:4px 12px}}
.key{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:4px}}.key.s1{{background:var(--s1)}}.key.s2{{background:var(--s2)}}details{{margin:12px 0}}p{{overflow-wrap:anywhere}}
@media(max-width:900px){{.study{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>Hardata II · how much of a dolphin whistle can a silver band keep?</h1>
<p>Pilot for the <a href="../../../docs/hardata-ii-pilot.md">Hardata II proposal</a>. Each whistle is inscribed with a counted number of bits, decoded back into sound, and given to a probe on the 2026 OpenWhistle dolphin encoder. The probe answers one question: does the decoded sound still sit with its whistle type? It does not tell us what a dolphin would hear.</p>
<div class="pipeline"><span>Recorded whistle + annotated F0</span><span>Inscription with counted bits</span><span>Optional simulated cast band</span><span>Decoded sound</span><span>OpenWhistle encoder + linear probe</span><span>Type retained?</span></div>
{reference}
<p>Test whistles: {counts["test"]} from session-disjoint upstream splits ({counts["test_excluded_without_contour"]} excluded for lacking a usable contour); probe trained on {counts["train"]} original training whistles and tuned on {counts["validation"]} validation whistles. Labels are whistle types (5 signature types associated with named dolphins and one shared non-signature type), not verified callers.</p></header><main>
<section><h2>Registered predictions and outcomes</h2><p>Predictions were written into the code before the first evaluation (registered {e(report["predictions"]["registered_at_utc"])}). Verdicts below apply their own thresholds to the OpenWhistle listener. {e(report["predictions"].get("registration_note", ""))}</p><table><thead><tr><th></th><th>Prediction</th><th>Outcome</th><th>Evidence</th></tr></thead><tbody>{prediction_rows}</tbody></table></section>
<section><h2>Bits against retained whistle type</h2><p>Hover over a point for exact values and confidence intervals. Dashed lines mark original-audio performance and chance. Bits count only what is inscribed per whistle; the decoder's shared knowledge (frequency axis, synthesis rule, noise bed, codec weights) is not counted.</p><div class="charts">{charts}</div>
<details><summary>Table view of every condition</summary><table><thead><tr><th>Family</th><th>Condition</th><th>Median bits</th>{headers}</tr></thead><tbody>{"".join(table_rows)}</tbody></table></details></section>
{matched_section}
<section><h2>From bits to silver</h2><p>The contour is engraved as a groove around a plain band: time runs along the band at {report["band"]["mm_per_second"]:g} mm/s, log frequency runs across its {report["band"]["width"]:g} mm width. We blur the heightmap to imitate printing, casting, polishing and scanning, add {report["band"]["surface_noise"]:g} mm surface noise, read the deepest point in each column, and resynthesize. These are simulations; no band has been cast or scanned.</p><div class="charts">{groove_figure}</div></section>
<section><h2>One whistle per type</h2><p>Selection rule: within each type, the test whistle closest to the type's median duration, chosen before looking at predictions. Half speed lowers pitch one octave so the high whistles are easier to hear.</p>{"".join(examples)}</section>
<section><h2>Provenance</h2><p>Dataset {e(report["dataset"]["dataset"])} · config {e(report["dataset"]["config"])} · parquet revision {e(report["dataset"]["parquet_revision"][:12])}</p>
<p>Encoder {e(ENCODER_LINE(report))} · codec {e(report["codec"]["id"])}@{e(str(report["codec"]["revision"])[:12])}</p><p><a href="results.json">results.json</a> (all predictions, bits, confusion matrices, parameters) · <a href="verdicts.json">verdicts.json</a></p>
<ul>{"".join(f"<li>{e(note)}</li>" for note in report["notes"])}</ul></section></main>
<script>
document.querySelectorAll('select[data-rate-group]').forEach(s=>{{const apply=()=>document.querySelectorAll('audio[data-rate-group="'+s.dataset.rateGroup+'"]').forEach(a=>{{a.playbackRate=Number(s.value);a.preservesPitch=false}});s.addEventListener('change',apply);apply()}});
document.querySelectorAll('button[data-audio]').forEach(b=>{{const a=document.getElementById(b.dataset.audio),t=b.textContent;b.addEventListener('click',async()=>{{if(a.paused){{document.querySelectorAll('audio').forEach(o=>{{if(o!==a)o.pause()}});const g=document.querySelector('select[data-rate-group="'+a.dataset.rateGroup+'"]');if(g){{a.playbackRate=Number(g.value);a.preservesPitch=false}}try{{await a.play()}}catch(err){{b.textContent='Use the audio controls'}}}}else{{a.pause()}}}});a.addEventListener('play',()=>b.textContent='Ⅱ Pause');a.addEventListener('pause',()=>b.textContent=t);a.addEventListener('ended',()=>b.textContent=t)}});
</script></body></html>'''
    export_svg(report, out / "figures" / "rate-distortion.svg")
    path = out / "index.html"
    path.write_text(page, encoding="utf-8")
    print(f"Saved gallery to {path.resolve()}")
    return path


SVG_STYLE = ("<style>text{font-family:system-ui,sans-serif}.grid{stroke:#e4ddcf;stroke-width:1}.reference{stroke:#8a8478;stroke-width:1;stroke-dasharray:4 3}"
             ".tick,.note,.legend{font-size:11px;fill:#5b554b}.axis{font-size:12px;fill:#5b554b}.title{font-size:13px;fill:#2f2b26;font-weight:600}</style>")
SVG_VARS = {"var(--s1)": "#2a78d6", "var(--s2)": "#eb6834", "var(--s3)": "#1baf7a", "var(--s4)": "#eda100",
            "var(--s5)": "#e87ba4", "var(--muted)": "#8a8478", "var(--surface)": "#ffffff"}


def export_svg(report, path: Path):
    """Standalone light-theme figure for Markdown: both listeners side by side, then the groove curve."""
    panels = [(name, rate_chart(report, name)) for name in report["listeners"]]
    panels.append((f"{list(report['listeners'])[0]}: decoded silver groove", groove_chart(report, list(report["listeners"])[0])))
    parts, y = [], 0
    for title, svg in panels:
        body = svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
        height = float(svg.split('viewBox="0 0 ', 1)[1].split('"', 1)[0].split()[1])
        parts.append(f'<text x="8" y="{y + 16}" class="title">{e(title)}</text><g transform="translate(0 {y + 22})">{body}</g>')
        y += height + 34
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {y:.0f}" width="640" height="{y:.0f}">{SVG_STYLE}'
            f'<rect width="640" height="{y:.0f}" fill="#ffffff"/>' + "".join(parts) + "</svg>")
    for variable, color in SVG_VARS.items():
        text = text.replace(variable, color)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def ENCODER_LINE(report):
    entry = report["listeners"]["OpenWhistle Wav2Vec2"]
    return f'{entry["model_id"]}@{entry["model_revision"][:12]}'
