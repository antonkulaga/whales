"""FLUX.2 klein material prints, bounded reference edits, and a listening gallery."""

import html
from importlib.metadata import version
import math
from pathlib import Path
import random
import shutil
import textwrap

from .audio import device_name, listening_copy, reference_controls, release_models
from .artist import snapshot_references
from .data import Layout, digest, now, read_json, write_json

IMAGE_MODEL = "black-forest-labs/FLUX.2-klein-4B"


def load_pipeline(layout: Layout, device: str, revision: str | None = None):
    import torch
    from diffusers import Flux2KleinPipeline
    from huggingface_hub import HfApi

    device = device_name(device)
    revision = HfApi().model_info(IMAGE_MODEL, revision=revision, timeout=60).sha
    print(f"Loading FLUX.2 klein @{revision[:10]} on {device}", flush=True)
    options = dict(revision=revision, cache_dir=layout.cache, use_safetensors=True)
    if device == "cuda":
        options.update(dtype=torch.bfloat16)
    else:
        options.update(dtype=torch.float32)
    pipe = Flux2KleinPipeline.from_pretrained(IMAGE_MODEL, **options)
    if device == "cuda":
        pipe.enable_model_cpu_offload()
    else:
        pipe.to(device)
    pipe.set_progress_bar_config(disable=True)
    return pipe, {"id": IMAGE_MODEL, "revision": revision, "device": device, "dtype": str(pipe.transformer.dtype), "cpu_offload": device == "cuda"}


def load_analysis(path: Path):
    report = read_json(path)
    if not report["clips"]:
        raise ValueError("Analysis contains no clips")
    for clip in report["clips"]:
        source = Path(clip["source"]["path"])
        if digest(source) != clip["source"]["sha256"]:
            raise ValueError(f"Source audio changed since analysis: {source}")
    return report


def generator(seed: int):
    import torch

    # Fresh CPU generator for each output keeps noise identical across clips.
    return torch.Generator(device="cpu").manual_seed(seed)


def save_image(image, path: Path, prompt: str, seed: int):
    from PIL.PngImagePlugin import PngInfo

    metadata = PngInfo()
    metadata.add_text("prompt", prompt)
    metadata.add_text("seed", str(seed))
    image.save(path, pnginfo=metadata)


def contact_sheet(output: Path, entries: list[dict], title: str, columns: int = 3):
    from PIL import Image, ImageDraw, ImageFont

    tile, caption = 320, 100
    sheet = Image.new("RGB", (columns * tile, 65 + math.ceil(len(entries) / columns) * (tile + caption)), "#f5f2ec")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    draw.text((18, 16), title, fill="#233d43", font=ImageFont.load_default(size=20))
    for i, entry in enumerate(entries):
        x, y = (i % columns) * tile, 65 + (i // columns) * (tile + caption)
        with Image.open(output / entry["image"]) as image:
            sheet.paste(image.convert("RGB").resize((tile, tile)), (x, y))
        draw.text((x + 10, y + tile + 8), textwrap.fill(entry["caption"], 40), fill="#233d43", font=font)
    sheet.save(output / "contact-sheet.png")


def finish_report(output: Path, analysis_path: Path, analysis, model, entries, parameters):
    output.mkdir(parents=True, exist_ok=True)
    audio_dir = output / "audio"
    audio_dir.mkdir(exist_ok=True)
    clips = {clip["id"]: clip for clip in analysis["clips"]}
    for entry in entries:
        if entry.get("clip_id"):
            clip = clips[entry["clip_id"]]
            source = Path(clip["source"]["path"])
            destination = audio_dir / source.name
            shutil.copy2(source, destination)
            entry["audio"] = f"audio/{source.name}"
            entry["audio_sha256"] = clip["source"]["sha256"]
            playback = audio_dir / f"{source.stem}-listen.wav"
            entry["playback"] = listening_copy(source, playback)
            entry["playback_audio"] = f"audio/{playback.name}"
            entry["playback_sha256"] = digest(playback)
            entry["descriptor_scores"] = clip["scores"]
        entry["image_sha256"] = digest(output / entry["image"])
    # Freeze the exact analysis used, even if the shared cache is later refreshed.
    write_json(output / "analysis.json", analysis)
    manifest = {
        "created_at_utc": now(), "analysis_path": str(analysis_path.resolve()), "analysis_snapshot": "analysis.json", "analysis_sha256": digest(output / "analysis.json"),
        "analysis": analysis, "image_model": model, "parameters": parameters, "artifacts": entries,
        "packages": {name: version(name) for name in ("torch", "transformers", "diffusers", "huggingface-hub", "numpy", "pillow", "scipy", "soundfile", "typer")},
    }
    write_json(output / "manifest.json", manifest)
    cards = []
    for entry in entries:
        audio = f'<audio controls preload="none" src="{html.escape(entry.get("playback_audio", entry["audio"]))}"></audio>' if entry.get("audio") else ""
        scores = html.escape(str(entry.get("descriptor_scores", {})))
        prompt = html.escape(entry.get("prompt", "Original input image"))
        cards.append(f'<article><a href="{html.escape(entry["image"])}"><img src="{html.escape(entry["image"])}" alt="{html.escape(entry["caption"])}"></a><h2>{html.escape(entry["caption"])}</h2>{audio}<details><summary>Prompt and controls</summary><p>{prompt}</p><pre>{scores}</pre></details></article>')
    title = html.escape(parameters["title"])
    (output / "index.html").write_text(f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font:16px system-ui;margin:32px;background:#f5f2ec;color:#233d43}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:24px}}article{{background:white;padding:12px;border-radius:8px}}img{{width:100%;display:block}}h2{{font-size:17px}}audio{{width:100%}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}details{{margin-top:12px}}
</style><h1>{title}</h1><p>Real recordings; frozen CLAP and FLUX.2 klein. Acoustic descriptions and material mappings are artistic choices, not animal meanings.</p><p>Seed {parameters['seed']} · <a href="manifest.json">Complete provenance</a> · <a href="contact-sheet.png">Contact sheet</a></p><main>{''.join(cards)}</main></html>''', encoding="utf-8")
    contact_sheet(output, entries, parameters["title"])
    from .gallery import write_gallery

    write_gallery(output.parent)
    print(f"Saved {len(entries)} images and listening gallery to {output.resolve()}", flush=True)
    return output / "index.html"


def materials(layout: Layout, analysis_path: Path, output: Path | None = None,
              seed: int = 20261004, steps: int = 4, device: str = "auto", shuffle: bool = False,
              revision: str | None = None, artist: dict | None = None, runtime=None):
    analysis = load_analysis(analysis_path)
    output = output or layout.output / ("materials-shuffled" if shuffle else "materials")
    output.mkdir(parents=True, exist_ok=True)
    vocab = analysis["vocabulary"]
    assignments = analysis["clips"].copy()
    if shuffle:
        random.Random(seed).shuffle(assignments)
    context, references = snapshot_references(artist, output)
    pipe, model = runtime or load_pipeline(layout, device, revision=revision)
    entries = []
    for clip, assigned in zip(analysis["clips"], assignments):
        descriptor = assigned["selected_descriptor"]
        for style, style_prompt in vocab["styles"].items():
            prompt = f"{vocab['composition']}, {descriptor['material']}, {style_prompt}"
            reference = references.get(style, [])
            options = {"image": [image for _, image in reference]} if reference else {}
            image = pipe(prompt=prompt, **options, generator=generator(seed), num_inference_steps=steps,
                         guidance_scale=1.0, height=512, width=512).images[0]
            filename = f"{clip['id']}-{style}.png"
            save_image(image, output / filename, prompt, seed)
            entries.append({
                "clip_id": clip["id"], "descriptor_source_clip_id": assigned["id"], "image": filename,
                "descriptor": descriptor, "prompt": prompt, "style": style,
                "reference_ids": [identifier for identifier, _ in reference],
                "caption": f"{clip['id']} / {style} / {descriptor['id']}",
            })
            print(f"Rendered {filename}", flush=True)
    if runtime is None:
        del pipe
        release_models()
    return finish_report(output, analysis_path, analysis, model, entries, {
        "title": ("Sound → Livia's jewelry → Livistone pavilion" if artist else "Acoustic material studies") + (" — shuffled controls" if shuffle else ""),
        "artist_context": context,
        "seed": seed, "steps": steps, "guidance_scale": 1.0, "resolution": [512, 512], "shuffled": shuffle,
        "comparison_note": "Identical descriptor, style and seed intentionally produce identical images. Shuffling repeated winners may have no effect.",
    })


def edit_instruction(descriptor: dict, amount: float):
    """A bounded vocabulary instruction, not a diffusion strength parameter."""
    degree = "very subtle" if amount < 0.38 else "subtle" if amount < 0.47 else "moderate"
    operation = descriptor.get("edit", f"introduce details inspired by {descriptor['material']}")
    return f"Make a {degree} structural variation: {operation}. Apply this only to the silver setting."


def painting(layout: Layout, analysis_path: Path, image_path: Path, output: Path | None = None,
             prompt: str | None = None, limit: int = 4, seed: int = 20261004, steps: int = 4,
             edit_min: float = 0.30, edit_max: float = 0.55, device: str = "auto",
             revision: str | None = None, artist: dict | None = None, runtime=None):
    from PIL import Image, ImageOps

    analysis = load_analysis(analysis_path)
    amounts, controls = reference_controls([clip["preprocessing"]["rms_dbfs"] for clip in analysis["clips"]], edit_min, edit_max)
    controls["mapping"] = {"[0,0.38)": "very subtle", "[0.38,0.47)": "subtle", "[0.47,1]": "moderate"}
    # Spread across the reference's amplitudes rather than selecting only one dataset.
    ordered = sorted(zip(analysis["clips"], amounts), key=lambda pair: pair[1])
    count = min(limit, len(ordered))
    selected = [ordered[round(i * (len(ordered) - 1) / (count - 1))] for i in range(count)] if count > 1 else ordered[:1]
    output = output or layout.output / "painting"
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as source:
        original_size = source.size
        # Pad instead of cropping away parts of the jewelry.
        initial = ImageOps.pad(ImageOps.exif_transpose(source).convert("RGB"), (512, 512), color="white", method=Image.Resampling.LANCZOS)
    initial.save(output / "original.png")
    input_copy = layout.input / "images" / f"{digest(image_path)[:12]}{image_path.suffix.lower()}"
    input_copy.parent.mkdir(parents=True, exist_ok=True)
    if input_copy.resolve() != image_path.resolve():
        shutil.copy2(image_path, input_copy)
    context, _ = snapshot_references(artist, output)
    prompt = prompt or analysis["vocabulary"]["painting_prompt"]
    pipe, model = runtime or load_pipeline(layout, device, revision=revision)
    entries = [{"image": "original.png", "caption": "Original image (resized and padded)"}]
    for clip, amount in selected:
        instruction = f"{prompt} {edit_instruction(clip['selected_descriptor'], amount)}"
        image = pipe(prompt=instruction, image=initial, generator=generator(seed),
                     num_inference_steps=steps, guidance_scale=1.0, height=512, width=512).images[0]
        filename = f"{clip['id']}.png"
        save_image(image, output / filename, instruction, seed)
        entries.append({
            "clip_id": clip["id"], "image": filename, "prompt": instruction, "edit_amount": amount,
            "steps": steps, "rms_dbfs": clip["preprocessing"]["rms_dbfs"],
            "caption": f"{clip['id']} / {clip['selected_descriptor']['id']} / edit amount {amount:.3f}",
        })
        print(f"Rendered {filename}: edit amount {amount:.3f}", flush=True)
    if runtime is None:
        del pipe
        release_models()
    return finish_report(output, analysis_path, analysis, model, entries, {
        "title": f"Mitoring listens: {count} sound-controlled setting variations" if artist else f"One artwork, {count} sounds", "seed": seed, "steps": steps, "guidance_scale": 1.0,
        "artist_context": context,
        "prompt": prompt, "controls": controls, "reference_clip_ids": analysis["reference_clip_ids"],
        "initial_image": {"path": str(image_path.resolve()), "cached_path": str(input_copy.resolve()),
                          "sha256": digest(image_path), "source_size": list(original_size), "resize": "EXIF orientation, aspect-preserving resize and white padding to 512 square"},
        "comparison_note": "Reference image, prompt template and seed fixed. CLAP selects material; common-reference RMS selects bounded edit wording. Edit amount is an artistic prompt control, not denoising strength; visual effects need not be monotonic.",
    })
