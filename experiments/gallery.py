"""A standalone HTML overview of sources, transformation schema and outputs."""

from collections import defaultdict
import html
from pathlib import Path

from .data import read_json


def escape(value):
    return html.escape(str(value), quote=True)


def artist_section(context: dict, directory: str, geometry: bool = False):
    cards = []
    for reference in context["references"]:
        roles = "Material and form reference" if geometry else ", ".join(reference["model_styles"]) or "Brief context"
        if directory == "jewelry":
            roles = "Photograph used as redesign input" if reference["id"] in ("mitoring", "mycelium") else "Artist context"
        cards.append(f'''<figure><a href="{escape(directory)}/{escape(reference['display_image'])}"><img src="{escape(directory)}/{escape(reference['display_image'])}" alt="{escape(reference['title'])}"></a><figcaption><b>{escape(reference['title'])}</b><p>{escape(reference['connection'])}</p><small>{escape(roles)}{' · original for setting edits' if reference.get('edit_reference') and not geometry else ''}</small></figcaption></figure>''')
    sources = "".join(f'<li>{escape(source["root"])}/{escape(source["path"])}</li>' for source in context["sources"])
    note = "The silver/amber cocoon is a new procedural study informed by these source works. Sound controls its geometry through the explicit parameters below. The artist has not authored or approved this acoustic mapping." if geometry else f"About the FLUX reference-image experiments: {context['experiment_note']}"
    if directory == "jewelry":
        note = "The new AI-generated jewelry concepts use Mitoring and Mycelium photographs as references. Their sound-to-form correspondences are this experiment's choices."
    return f'''<section class="artist"><h2>Starting from {escape(context['name'])}</h2><p>{escape(context['summary'])}</p><div class="references">{''.join(cards)}</div><p>{escape(note)}</p><details><summary>Sources behind this brief</summary><ul>{sources}</ul><a href="{escape(directory)}/references/profile.json">Reference paths, roles and SHA-256 hashes</a></details></section>'''


def forms_section(output: Path):
    path = output / "long-forms" / "studies.json"
    if not path.exists():
        return ""
    report = read_json(path)
    rows = []
    for index, clip in enumerate(report["clips"]):
        source = clip["source"]
        figures = []
        players = []
        for i, variant in enumerate(clip["variants"]):
            params = variant["parameters"]
            audio_id = f"audio-long-{index}-{i}"
            players.append(f'<div class="listening-input"><button type="button" data-audio="{audio_id}">▶ Listen · {params["duration_s"]:.1f} s source</button><audio id="{audio_id}" data-rate-group="long-{index}" controls preload="metadata" src="long-forms/{escape(variant.get("playback_audio", variant.get("audio", clip["audio"])))}"></audio></div>')
            figures.append(f'<figure><a href="long-forms/{escape(variant["image"])}"><img src="long-forms/{escape(variant["image"])}" alt="{params["duration_s"]:.1f} second prefix, {params["rib_count"]} controlled silver ribs"></a><figcaption><b>{params["duration_s"]:.1f} seconds → {params["rib_count"]} ribs</b><br>Radius {min(params["mid_radius_mm"]):.1f}–{max(params["mid_radius_mm"]):.1f} mm<br>Rib diameter {min(params["rib_diameter_mm"]):.2f}–{max(params["rib_diameter_mm"]):.2f} mm · <a href="long-forms/{escape(variant["mesh"])}">OBJ mesh</a></figcaption></figure>')
        rows.append(f'''<article class="study"><div class="input"><h3>Input · {escape(source['id'])}</h3><p>{escape(source['dataset'])} / row {source['row_index']}<br>Actual waveform: {clip['features']['sample_rate']:,} Hz · {clip['features']['duration_s']:.1f} s</p><label>Listening mode <select data-rate-group="long-{index}"><option value="0.5" selected>Half speed · lower pitch</option><option value="1">Original speed and pitch</option></select></label>{''.join(players)}<p><small>Volume is raised for playback. Half speed makes high frequencies easier to hear and takes twice the source duration. Geometry uses the original speed, frequency and amplitude.</small></p><img src="long-forms/{escape(clip['features_image'])}" alt="Full recording waveform, spectral centroid and RMS time series"><p>5 s, 15 s and full prefixes all start at time zero.</p></div><div class="mapping"><h3>Schema / numeric controls</h3><p><b>Duration → rib count:</b> ceil(seconds / 0.75), bounded to 3–120.</p><p><b>Centroid → radius:</b> the 2–20 kHz spectral centroid controls each rib's mid-height radius, 12–20 mm.</p><p><b>RMS → diameter:</b> local waveform RMS controls each rib's diameter, 0.55–2.20 mm.</p><p>Both recordings share percentile reference ranges. The ranges stay fixed for every prefix; time advances around the cocoon.</p><p>Fixed: amber core, 22 mm height, 12 mm foot radius and camera.</p></div><div class="outputs"><h3>Output · geometry follows the data</h3><div class="images">{''.join(figures)}</div></div></article>''')
    diagram = '<figure><a href="long-forms/controls.png"><img src="long-forms/controls.png" alt="Actual parameters: recording duration controls rib count, spectral centroid controls radius, RMS controls rib diameter; 5, 15 and full-length example outputs"></a><figcaption><a href="long-forms/controls.svg">Vector explanation image</a></figcaption></figure>' if (output / "long-forms" / "controls.png").exists() else ""
    return f'''<section><h2>Longer recordings → explicit silver/amber geometry</h2><p>These procedural cocoon studies connect Livia's open silver settings and Livistone's inhabited shells to measurable acoustic structure. The mesh itself carries the controls; these renders use no diffusion model. Compare the growing prefixes and listen to their matching audio. <a href="long-forms/studies.json">Full time series, reference ranges and per-rib dimensions</a></p>{diagram}{''.join(rows)}<p>Centroid is a frequency-energy summary, not an estimated whistle pitch. Features include all recorded sound, including noise. Rib spacing and the material mapping are our artistic choices. The OBJ files contain the silver structure in millimeters; the amber is a fixed rendered core. Intersections/open ends require further work before fabrication.</p></section>'''


def jewelry_section(report: dict, directory: str):
    clips = {clip["id"]: clip for clip in report["analysis"]["clips"]}
    rows = []
    for index, entry in enumerate(report["artifacts"]):
        if not entry.get("clip_id"):
            continue
        clip = clips[entry["clip_id"]]
        operation = entry["transformation"]
        audio_id = f"audio-bold-{index}"
        scores = "".join(f'<tr><td>{escape(key)}</td><td>{value:.3f}</td></tr>' for key, value in clip["scores"].items())
        rows.append(f'''<article class="study"><div class="input"><h3>Inputs · jewelry + sound</h3><figure><a href="{escape(directory)}/{escape(entry['input_image'])}"><img src="{escape(directory)}/{escape(entry['input_image'])}" alt="Original {escape(entry['reference_title'])}"></a><figcaption>{escape(entry['reference_title'])} · original photograph</figcaption></figure><p>{escape(clip['id'])} · {escape(clip['source'].get('dataset', 'Recording'))}</p><button type="button" data-audio="{audio_id}">▶ Listen</button><audio id="{audio_id}" controls preload="metadata" src="{escape(directory)}/{escape(entry.get('playback_audio', entry['audio']))}"></audio><p><small>Playback volume raised. CLAP analyzes the first {clip['preprocessing']['analyzed_duration_s']:.2f} seconds at 48 kHz, without pitch shifting.</small></p></div><div class="mapping"><h3>Schema · CLAP → redesign</h3><p><b>Winning description:</b> {escape(clip['selected_descriptor']['text'])}</p><table><caption>Measured CLAP cosine scores</caption><tbody>{scores}</tbody></table><h4>{escape(operation['title'])}</h4><p>{escape(operation['operation'])}</p><p>{escape(operation['connection'])}</p><p><small>The photo and this instruction enter FLUX. CLAP selects text; it does not deform pixels directly. Redesign freedom is substantial for every sound.</small></p></div><div class="outputs"><h3>Output · {escape(operation['title'])}</h3><div class="images"><figure><a href="{escape(directory)}/{escape(entry['image'])}"><img src="{escape(directory)}/{escape(entry['image'])}" alt="{escape(entry['caption'])}"></a><figcaption><b>Sound-directed redesign</b> · generated concept</figcaption></figure><figure><a href="{escape(directory)}/{escape(entry['neutral_image'])}"><img src="{escape(directory)}/{escape(entry['neutral_image'])}" alt="Same jewelry redesigned without a sound-selected operation"></a><figcaption>No-sound redesign · same photo, seed and redesign freedom</figcaption></figure></div><details><summary>Actual prompt</summary><p>{escape(entry['prompt'])}</p></details></div></article>''')
    return f'''<section><h2>{escape(report['parameters']['title'])}</h2><p>The same three recordings act on two of Livia's real pieces. Compare each sound-directed result with the no-sound redesign beside it: both have the same input photo, seed and freedom to change the silver setting.</p><p>CLAP chooses <b>clicks → staggered silver terraces</b>, <b>whistle → sweeping crest</b>, or <b>wavering → unfurling petals</b>. The setting opens outward from the stone. The stone and ring are reference anchors; substantial changes in silver silhouette are explicitly requested.</p><p>The preservation instruction is a request to the image model: some results also change the stone's shape and details. These images are design explorations rather than exact edits of a fabrication model.</p><p><a href="{escape(directory)}/manifest.json">Scores, exact prompts and source hashes</a> · <a href="{escape(directory)}/contact-sheet.png">All eight generated concepts</a></p>{''.join(rows)}<p>{escape(report['parameters']['comparison_note'])}</p></section>'''


def write_gallery(output: Path, include_baseline: bool = False):
    manifests = sorted(output.glob("*/manifest.json"))
    bold_path = next((p for p in manifests if read_json(p)["parameters"].get("kind") == "bold-jewelry"), None)
    geometry = (output / "long-forms" / "studies.json").exists() and bold_path is None
    show_baseline = include_baseline or (not geometry and bold_path is None)
    if not manifests and not geometry:
        raise ValueError(f"No generated experiments found in {output}")
    sections = []
    artist = ""
    if bold_path:
        report = read_json(bold_path)
        artist = artist_section(report["parameters"]["artist_context"], bold_path.parent.name)
        sections.append(jewelry_section(report, bold_path.parent.name))
    for manifest_path in manifests:
        if manifest_path == bold_path:
            continue
        report = read_json(manifest_path)
        directory = manifest_path.parent.name
        context = report["parameters"].get("artist_context")
        if context and not artist:
            artist = artist_section(context, directory, geometry=geometry)
        if not show_baseline:
            continue
        clips = {clip["id"]: clip for clip in report["analysis"]["clips"]}
        groups = defaultdict(list)
        for entry in report["artifacts"]:
            if entry.get("clip_id"):
                groups[entry["clip_id"]].append(entry)
        original = ""
        if report["parameters"].get("initial_image"):
            original = f'<figure class="original"><img src="{escape(directory)}/original.png" alt="Original artwork"><figcaption>Original reference image · {escape(Path(report["parameters"]["initial_image"]["path"]).name)}</figcaption></figure>'
        rows = []
        for i, (clip_id, entries) in enumerate(groups.items()):
            clip = clips[clip_id]
            assigned = clips[entries[0].get("descriptor_source_clip_id", clip_id)]
            descriptor = assigned["selected_descriptor"]
            source = clip["source"]
            preprocessing = clip["preprocessing"]
            audio_id = f"audio-{directory}-{i}"
            audio_path = f"{directory}/{entries[0].get('playback_audio', entries[0]['audio'])}"
            provenance = f"{source.get('dataset', 'Personal recording')} / row {source.get('row_index', '—')}"
            score_rows = "".join(f'<tr><td>{escape(key)}</td><td>{value:.3f}</td></tr>' for key, value in assigned["scores"].items())
            control = ""
            if "edit_amount" in entries[0]:
                control = f'<p>RMS: {preprocessing["rms_dbfs"]:.2f} dBFS<br>Shared-reference edit amount: {entries[0]["edit_amount"]:.3f}<br><small>Amount selects bounded instruction wording; it is not denoising strength.</small></p>'
            if assigned["id"] != clip_id:
                control += f'<p>Shuffled descriptor source: {escape(assigned["id"])}</p>'
            connection = f'<p><b>Connection to Livia:</b> {escape(descriptor["connection"])}</p>' if descriptor.get("connection") else ""
            images = "".join(f'<figure><a href="{escape(directory)}/{escape(entry["image"])}"><img src="{escape(directory)}/{escape(entry["image"])}" alt="{escape(entry["caption"])}" loading="lazy"></a><figcaption><b>{escape(entry.get("style", "Silver-setting variation"))}</b> · generated concept</figcaption><details><summary>Actual prompt and reference inputs</summary><p>{escape(entry["prompt"])}</p><p>Image references: {escape(", ".join(entry.get("reference_ids", ["Mitoring original"])) or "None")}</p></details></figure>' for entry in entries)
            rows.append(f'''<article class="study"><div class="input"><h3>Input · {escape(clip_id)}</h3>
<p>{escape(provenance)}</p><button type="button" data-audio="{escape(audio_id)}">▶ Listen</button>
<audio id="{escape(audio_id)}" controls preload="none" src="{escape(audio_path)}"></audio>
<p>{preprocessing['source_sample_rate']:,} Hz source · {preprocessing['analyzed_duration_s']:.2f} s analyzed<br>Mono, 48 kHz, first ≤10 seconds; no pitch shift.</p>
</div><div class="mapping"><h3>Schema / transformation</h3><p><b>CLAP selects:</b> {escape(descriptor['text'])}</p><table><caption>Descriptor cosine scores</caption><tbody>{score_rows}</tbody></table><p><b>Proposed geometry mapping:</b> {escape(descriptor['material'])}</p>{connection}{control}<p>Fixed seed: {report['parameters']['seed']} · {report['parameters']['steps']} steps</p></div><div class="outputs"><h3>Output</h3><div class="images">{images}</div></div></article>''')
        sections.append(f'''<section><h2>{escape(report['parameters']['title'])}</h2><p>Image model: {escape(report['image_model']['id'])} · <a href="{escape(directory)}/manifest.json">Full schema and provenance JSON</a> · <a href="{escape(directory)}/contact-sheet.png">Contact sheet</a></p>{original}{''.join(rows)}</section>''')
    path = output / "index.html"
    explanation = '''<section><h2>How sound changes the image</h2><p>The six inputs are real WAV recordings: three DSWP and three OpenWhistle clips. We mix to mono and resample to 48 kHz. CLAP's processor makes a log-mel spectrogram: energy over time in 64 frequency bands, with this checkpoint covering 50 Hz–14 kHz and a 10 ms frame hop. Short recordings are repeat-padded to its ten-second window.</p><p>CLAP compares the encoded recording with three fixed acoustic sentences; it does not write a caption. The highest cosine score chooses our geometry instruction: <b>clicks → repeated open cells</b>, <b>whistle → continuous silver ribbons</b>, <b>wavering → undulating folds</b>. FLUX receives that text and the reference images. No audio waveform or CLAP vector is passed directly to FLUX.</p><p>For the Mitoring edits, raw recording RMS additionally selects “very subtle,” “subtle,” or “moderate” wording on a common reference range. These are prompt instructions, not numeric metal dimensions or denoising strength. OpenWhistle's provided pitch tracks are retained in the source metadata but are not used by this image pipeline.</p><p>This is a coarse first prototype: clips with the same winning sentence and fixed seed have identical ring/pavilion outputs. Scores are similarities, not probabilities or validated call types. The 14 kHz front-end limit also leaves higher-frequency cetacean information outside CLAP's representation.</p></section>'''
    if (output / "sound-controls.png").exists():
        explanation = explanation.replace("</h2>", '</h2><figure><a href="sound-controls.png"><img src="sound-controls.png" alt="Annotated sound controls: actual waveform, CLAP scores, RMS, prompt parameters and original/edited Mitoring"></a><figcaption><a href="sound-controls.svg">Vector diagram</a> · <a href="sound-controls.json">Exact example values</a></figcaption></figure>', 1)
    explanation = explanation.replace("How sound changes the image", "How the earlier CLAP prompt experiment works")
    if not show_baseline:
        explanation = ""
    intro = "Listen to the input recordings, inspect the measured controls and compare the resulting silver/amber geometry."
    pipeline = ["Recording + Livia's material/form vocabulary", "Whole-recording acoustic time series", "Duration / spectral centroid / RMS", "Rib count / radius / diameter", "Explicit mesh + rendered concept"]
    if bold_path or not geometry:
        intro = "Livia's jewelry photographs and real recordings become inputs for substantial silver-setting redesigns."
        pipeline = ["Jewelry photograph + recording", "CLAP audio/text cosine scores", "Sound-selected silver transformation", "FLUX reference-image edit", "Redesigned jewelry concept"]
    header = f'<h1>Livia × cetacean sounds</h1><p>{intro}</p><div class="pipeline" aria-label="Pipeline schema">' + "".join(f'<span>{escape(stage)}</span>' for stage in pipeline) + '</div><p>The acoustic correspondences are our artistic choices. Source works and generated concepts are labelled separately.</p>'
    current_forms = forms_section(output) if geometry or include_baseline else ""
    path.write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Livia × cetacean sounds · inputs, schema and outputs</title><style>
*{box-sizing:border-box}body{font:16px/1.5 system-ui,sans-serif;background:#f4f0e5;color:#39352f;margin:0;padding:32px}header,main{max-width:1440px;margin:auto}h1{font-size:34px;margin-bottom:8px}h2{font-size:26px}h3{font-size:18px;margin-top:0}.pipeline{display:flex;flex-wrap:wrap;gap:10px;margin:26px 0}.pipeline span{background:#e6dcc8;padding:12px;border-radius:8px}.pipeline span+span:before{content:'→ ';color:#81602b}section{margin:50px 0}.study{display:grid;grid-template-columns:minmax(200px,1fr) minmax(250px,1fr) minmax(300px,1.7fr);gap:24px;background:white;padding:24px;margin:24px 0;border-radius:12px}.images{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}.references{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:24px}.references img{aspect-ratio:1;object-fit:contain;background:white}.artist{border-bottom:1px solid #c6bba4;padding-bottom:26px}figure{margin:0}img{display:block;width:100%;border-radius:4px}figcaption,small{font-size:13px}button{cursor:pointer;border:0;border-radius:6px;background:#81602b;color:white;font:inherit;padding:9px 20px;margin:8px 0}audio{display:block;width:100%;margin:10px 0}table{width:100%;border-collapse:collapse}caption{text-align:left;font-size:13px}td{border-bottom:1px solid #e5e5e5;padding:4px}td:last-child{text-align:right;font-variant-numeric:tabular-nums}details{font-size:13px;overflow-wrap:anywhere;margin:8px 0}.original{max-width:320px}a{color:#81602b}p{overflow-wrap:anywhere}.play-error{color:#9c392d}@media(max-width:900px){.study{grid-template-columns:1fr}body{padding:18px}}
</style></head><body><header>''' + header + '</header><main>' + artist + current_forms + explanation + "".join(sections) + '''</main><script>
document.querySelectorAll('select[data-rate-group]').forEach(select=>{const apply=()=>document.querySelectorAll('audio[data-rate-group="'+select.dataset.rateGroup+'"]').forEach(audio=>{audio.playbackRate=Number(select.value);audio.preservesPitch=false});select.addEventListener('change',apply);apply()});
document.querySelectorAll('button[data-audio]').forEach(button=>{const audio=document.getElementById(button.dataset.audio),label=button.textContent;button.addEventListener('click',async()=>{if(audio.paused){document.querySelectorAll('audio').forEach(other=>{if(other!==audio)other.pause()});try{await audio.play()}catch(error){button.textContent='Use the audio controls below';button.classList.add('play-error')}}else{audio.pause()}});audio.addEventListener('play',()=>button.textContent='Ⅱ Pause');audio.addEventListener('pause',()=>button.textContent=label);audio.addEventListener('ended',()=>button.textContent=label)});
</script></body></html>''', encoding="utf-8")
    print(f"Saved input/schema/output gallery to {path.resolve()}")
    return path
