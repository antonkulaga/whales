"""An annotated diagram of the actual prompt controls, using a generated pair."""

from pathlib import Path

from .data import digest, read_json, write_json


def write_explanation(output: Path, clip_id: str | None = None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    import numpy as np
    from PIL import Image

    from .audio import load_audio
    from .images import edit_instruction

    directory = output / "painting"
    report = read_json(directory / "manifest.json")
    candidates = [entry for entry in report["artifacts"] if entry.get("clip_id")]
    entry = next(item for item in candidates if item["clip_id"] == clip_id) if clip_id else max(candidates, key=lambda item: item["edit_amount"])
    clip = next(item for item in report["analysis"]["clips"] if item["id"] == entry["clip_id"])
    audio_path = directory / entry["audio"]
    if digest(audio_path) != entry["audio_sha256"]:
        raise ValueError(f"Audio changed: {audio_path}")
    waveform, preprocessing = load_audio(audio_path)
    amount = entry["edit_amount"]
    degree = "very subtle" if amount < .38 else "subtle" if amount < .47 else "moderate"
    descriptor = clip["selected_descriptor"]
    controls = report["parameters"]["controls"]
    low, high = controls["reference_range"]
    color, accent, bg = "#39352f", "#916428", "#f4f0e5"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": color})
    fig = plt.figure(figsize=(17, 11), facecolor=bg)
    canvas = fig.add_axes([0, 0, 1, 1], frameon=False, xlim=(0, 1), ylim=(0, 1))
    canvas.set_axis_off()

    def text(x, y, value, size=12, weight="normal", **kwargs):
        canvas.text(x, y, value, fontsize=size, fontweight=weight, va="top", **kwargs)

    def card(x, y, width, height, heading):
        canvas.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.008", linewidth=1,
                                       edgecolor="#c6bba4", facecolor="white"))
        text(x + .014, y + height - .015, heading, 14, "bold")

    def arrow(start, end, bend=0):
        canvas.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18,
                                        linewidth=2, color=accent, connectionstyle=f"arc3,rad={bend}"))

    text(.04, .975, "How this sound changes Mitoring", 26, "bold")
    text(.04, .933, f"Actual example: {clip['id']}  |  original photo + recorded sound + fixed seed {report['parameters']['seed']}", 13)
    card(.04, .60, .27, .28, "1. Real recording")
    wave = fig.add_axes([.06, .705, .23, .105], facecolor="white")
    stride = max(1, len(waveform) // 4000)
    wave.plot(np.arange(len(waveform))[::stride] / 48000, waveform[::stride], color=accent, linewidth=.8)
    wave.set_xlabel("Time (seconds)", fontsize=10)
    wave.set_ylabel("Amplitude", fontsize=10)
    wave.tick_params(labelsize=9)
    for spine in ("top", "right"):
        wave.spines[spine].set_visible(False)
    text(.055, .658, "Mono 48 kHz; no pitch shift.\nTwo different paths leave this waveform.", 11)

    card(.38, .68, .25, .20, "2. CLAP description scores")
    score_axes = fig.add_axes([.445, .713, .165, .10], facecolor="white")
    labels, values = list(clip["scores"]), list(clip["scores"].values())
    bars = score_axes.barh(labels, values, color=[accent if name == descriptor["id"] else "#c9c5bc" for name in labels])
    score_axes.invert_yaxis()
    score_axes.set_xlim(min(0, min(values)) - .015, max(values) + .065)
    for bar, value in zip(bars, values):
        score_axes.text(max(0, value) + .007, bar.get_y() + bar.get_height() / 2, f"{value:.3f}", va="center", fontsize=10)
    score_axes.tick_params(axis="y", labelsize=10, length=0)
    score_axes.set_xticks([])
    score_axes.spines[["top", "right", "bottom", "left"]].set_visible(False)
    text(.393, .704, "Waveform → log-mel → embedding → cosine scores", 9)
    card(.71, .68, .25, .20, "Control A: geometry family")
    families = {"clicks": "Repeated open cells", "whistle": "Continuous silver ribbons", "wavering": "Undulating silver folds"}
    text(.725, .825, f"Winner: {descriptor['id']}", 14, "bold")
    text(.725, .785, families.get(descriptor["id"], descriptor["id"]), 13)
    text(.725, .750, "Our mapping becomes text in the prompt.\nNo numeric curve or rib dimensions.", 10)

    card(.38, .485, .25, .145, "3. Recording RMS (separate)")
    text(.393, .585, f"{preprocessing['rms_dbfs']:.2f} dBFS", 17, "bold")
    text(.393, .548, f"Shared p10–p90: {low:.2f} to {high:.2f} dBFS\nScaled + clipped to 0.30–0.55.", 11)
    card(.71, .485, .25, .145, "Control B: edit wording")
    text(.725, .585, f"{amount:.3f} → {degree}", 17, "bold")
    text(.725, .547, "0.30–<0.38: very subtle; <0.47: subtle\n0.47–0.55: moderate. Prompt control only.", 10)
    arrow((.315, .785), (.373, .785))
    arrow((.635, .785), (.703, .785))
    arrow((.315, .665), (.373, .57), .15)
    arrow((.635, .56), (.703, .56))

    image_axes = []
    for x, filename, heading, annotation, target in [
        (.04, "original.png", "Original Mitoring photograph", "Original silver folds", (192, 228)),
        (.69, entry["image"], "Generated setting variation", "Longer, smoother ribbons", (181, 242)),
    ]:
        text(x, .441, heading, 15, "bold")
        axes = fig.add_axes([x, .09, .27, .335])
        with Image.open(directory / filename) as image:
            axes.imshow(image.convert("RGB"))
        axes.set_axis_off()
        if descriptor["id"] == "whistle":
            axes.annotate(annotation, xy=target, xytext=(14, 60), fontsize=10,
                          bbox=dict(boxstyle="round,pad=.3", fc="white", ec="#c6bba4"),
                          arrowprops=dict(arrowstyle="->", color=accent, lw=1.5))
        image_axes.append(axes)

    card(.38, .12, .25, .30, "4. FLUX.2 klein reference edit")
    text(.393, .372, f"Geometry: {families.get(descriptor['id'], descriptor['id'])}\nDegree: {degree}", 12, "bold")
    text(.393, .309, "Requested change: silver setting only.\nKeep amber, viewpoint and background.\n\nFixed: input photo, seed, 4 steps.\nSound changes the instruction text.\nThe model interprets the final shape.", 11)
    arrow((.315, .26), (.373, .26))
    arrow((.635, .26), (.683, .26))
    canvas.plot([.969, .982, .982, .51, .51], [.785, .785, .462, .462, .439], color=accent, linewidth=2)
    arrow((.51, .439), (.51, .425))
    canvas.plot([.835, .835, .60, .60], [.478, .449, .449, .439], color=accent, linewidth=2)
    arrow((.60, .439), (.60, .425))
    text(.04, .054, "Current limits: three broad sound families; no direct audio-to-FLUX embedding; no measured thickness/curvature control.", 12, "bold")
    text(.04, .027, "CLAP uses 64 log-mel bands over 50 Hz–14 kHz. RMS depends on recording gain/distance. Requested edits are not guaranteed geometric constraints.", 11)
    fig.savefig(output / "sound-controls.png", dpi=160, facecolor=bg)
    fig.savefig(output / "sound-controls.svg", facecolor=bg)
    plt.close(fig)
    write_json(output / "sound-controls.json", {
        "clip_id": clip["id"], "audio": f"painting/{entry['audio']}", "audio_sha256": entry["audio_sha256"],
        "original": "painting/original.png", "edited": f"painting/{entry['image']}", "edited_sha256": entry["image_sha256"],
        "scores": clip["scores"], "descriptor": descriptor, "rms_dbfs": preprocessing["rms_dbfs"],
        "controls": controls, "edit_amount": amount, "degree": degree,
        "instruction": edit_instruction(descriptor, amount), "actual_prompt": entry["prompt"],
        "diagram_sha256": digest(output / "sound-controls.png"),
    })
    print(f"Saved annotated sound-control diagram to {output / 'sound-controls.png'}")
    return output / "sound-controls.png"
