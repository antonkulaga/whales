"""Substantial reference-image redesigns selected by real CLAP scores."""

from pathlib import Path

from .artist import snapshot_references
from .audio import release_models
from .data import Layout, ROOT, digest, read_json
from .images import finish_report, generator, load_analysis, load_pipeline, save_image

TRANSFORMATIONS = ROOT / "resources" / "jewelry-transformations.json"


def representative_clips(analysis: dict, operations: dict):
    """One actual winning clip per direction, preferring a clear score margin."""
    selected = []
    for direction in operations:
        candidates = [c for c in analysis["clips"] if c["selected_descriptor"]["id"] == direction]
        if candidates:
            def margin(clip):
                ordered = sorted(clip["scores"].values(), reverse=True)
                return ordered[0] - ordered[1] if len(ordered) > 1 else ordered[0]
            selected.append(max(candidates, key=margin))
    if not selected:
        raise ValueError("No CLAP winners match the jewelry transformation vocabulary")
    return selected


def generate_jewelry(layout: Layout, analysis_path: Path, artist: dict,
                     seed: int = 20261004, device: str = "auto", revision: str | None = None):
    from PIL import Image

    analysis = load_analysis(analysis_path)
    vocabulary = read_json(TRANSFORMATIONS)
    clips = representative_clips(analysis, vocabulary["operations"])
    output = layout.output / "jewelry"
    output.mkdir(parents=True, exist_ok=True)
    context, _ = snapshot_references(artist, output)
    references = [ref for ref in context["references"] if ref["id"] in ("mitoring", "mycelium")]
    if len(references) != 2:
        raise ValueError("Both Mitoring and Mycelium references are required")
    pipe, model = load_pipeline(layout, device, revision)
    entries = []
    try:
        for reference in references:
            with Image.open(output / reference["model_image"]) as image:
                initial = image.convert("RGB")
            # Identical redesign freedom, reference, seed and settings: only the
            # acoustic operation differs from this no-sound comparison.
            for clip in [None, *clips]:
                direction = clip["selected_descriptor"]["id"] if clip else "neutral"
                operation = vocabulary["operations"].get(direction)
                prompt = vocabulary["prompt"].format(operation=operation["operation"] if operation else vocabulary["neutral"])
                image = pipe(prompt=prompt, image=initial, generator=generator(seed),
                             num_inference_steps=4, guidance_scale=1.0, height=512, width=512).images[0]
                filename = f"{reference['id']}-{direction}.png"
                save_image(image, output / filename, prompt, seed)
                entry = {"image": filename, "prompt": prompt, "reference_ids": [reference["id"]],
                         "input_image": reference["model_image"], "reference_title": reference["title"],
                         "direction": direction, "caption": f"{reference['id']} / {operation['title'] if operation else 'No-sound redesign'}"}
                if clip:
                    entry.update(clip_id=clip["id"], transformation=operation,
                                 neutral_image=f"{reference['id']}-neutral.png")
                entries.append(entry)
                print(f"Rendered bold jewelry: {filename}", flush=True)
    finally:
        del pipe
        release_models()
    return finish_report(output, analysis_path, analysis, model, entries, {
        "kind": "bold-jewelry", "title": "Jewelry + sound → substantial silver redesigns",
        "artist_context": context, "seed": seed, "steps": 4, "guidance_scale": 1.0, "resolution": [512, 512],
        "transformations": vocabulary, "transformations_sha256": digest(TRANSFORMATIONS),
        "comparison_note": "Same photo, seed and substantial redesign template for the no-sound and sound-directed outputs. Only the operation text changes. CLAP selects among three descriptions; its vector is not passed to FLUX. RMS does not limit redesign freedom. These are generated concept images, not fabrication geometry.",
    })
