"""Typer commands; ML imports stay lazy so the metadata CLI stays lightweight."""

from pathlib import Path
from typing import Annotated

import typer

from .data import DEFAULT_DATA, ROOT, Layout, fetch_samples

app = typer.Typer(help="Run CLAP → material studies and sound-controlled image edits.", no_args_is_help=True)
DataOption = Annotated[Path, typer.Option(help="Root containing input/, interim/, output/.")]
DeviceOption = Annotated[str, typer.Option(help="auto, cuda, or cpu.")]
AnalysisOption = Annotated[Path | None, typer.Option(exists=True, dir_okay=False, help="Cached CLAP analysis JSON; defaults to data/interim/analysis.json.")]
OutputOption = Annotated[Path | None, typer.Option(help="Output directory.")]
SeedOption = Annotated[int, typer.Option(min=0, max=2**32 - 1, help="Identical seed across recordings.")]
ImageOption = Annotated[Path, typer.Option(exists=True, dir_okay=False, help="Initial artwork or jewelry photograph.")]
LiviaOption = Annotated[Path, typer.Option(exists=True, file_okay=False, help="Livia site checkout: source texts and original jewelry photos.")]
LivistoneOption = Annotated[Path, typer.Option(exists=True, file_okay=False, help="Livistone checkout: architectural context and catalogue.")]


@app.command("livia")
def livia_command(
    data_dir: DataOption = DEFAULT_DATA,
    livia_dir: LiviaOption = ROOT.parent / "livia",
    livistone_dir: LivistoneOption = ROOT.parent / "livistone",
    seed: SeedOption = 20261004,
    device: DeviceOption = "auto",
    revision: Annotated[str | None, typer.Option(help="Optional FLUX.2 klein commit or tag.")] = None,
):
    """Generate both experiments from Livia's real jewelry and Livistone context."""
    dependencies()
    from .artist import prepare_artist
    from .audio import analyze, release_models
    from .images import load_pipeline, materials, painting

    layout = Layout(data_dir)
    layout.create()
    artist = prepare_artist(layout, livia_dir, livistone_dir)
    if not any((layout.input / "audio").glob("*.wav")):
        fetch_samples(layout)
    analysis = analyze(layout, device=device)
    image = next(Path(ref["cached_path"]) for ref in artist["references"] if ref.get("edit_reference"))
    runtime = load_pipeline(layout, device, revision=revision)
    try:
        materials(layout, analysis, seed=seed, artist=artist, runtime=runtime)
        painting(layout, analysis, image, seed=seed, artist=artist, runtime=runtime)
    finally:
        del runtime
        release_models()


@app.command("gallery")
def gallery_command(
    data_dir: DataOption = DEFAULT_DATA,
    include_baseline: Annotated[bool, typer.Option(help="Also show the earlier CLAP/FLUX experiments.")] = False,
):
    """Build one HTML overview with inputs, schema, Listen buttons and outputs."""
    from .gallery import write_gallery

    write_gallery(Layout(data_dir).output, include_baseline=include_baseline)


@app.command("jewelry")
def jewelry_command(
    data_dir: DataOption = DEFAULT_DATA,
    analysis: AnalysisOption = None,
    livia_dir: LiviaOption = ROOT.parent / "livia",
    livistone_dir: LivistoneOption = ROOT.parent / "livistone",
    seed: SeedOption = 20261004,
    device: DeviceOption = "auto",
    revision: Annotated[str | None, typer.Option(help="Optional FLUX.2 klein commit or tag.")] = None,
):
    """Use CLAP to substantially redesign two real jewelry photographs."""
    dependencies()
    from .artist import prepare_artist
    from .jewelry import generate_jewelry

    layout = Layout(data_dir)
    layout.create()
    artist = prepare_artist(layout, livia_dir, livistone_dir)
    generate_jewelry(layout, analysis or layout.interim / "analysis.json", artist, seed, device, revision)


@app.command("explain")
def explain_command(data_dir: DataOption = DEFAULT_DATA):
    """Draw actual sound controls and an original/edited pair; needs art + viz."""
    from .explain import write_explanation
    from .gallery import write_gallery

    try:
        write_explanation(Layout(data_dir).output)
    except ImportError as error:
        raise typer.BadParameter("Use: uv run --group art --group viz main.py art explain") from error
    write_gallery(Layout(data_dir).output)


@app.command("long-forms")
def long_forms_command(
    data_dir: DataOption = DEFAULT_DATA,
    limit: Annotated[int, typer.Option(min=1, max=4)] = 2,
    minimum_seconds: Annotated[float, typer.Option(min=15, max=120)] = 30,
):
    """Fetch longer recordings and make geometry directly; requires art + viz."""
    from .data import fetch_long_samples
    from .forms import generate_forms
    from .gallery import write_gallery

    layout = Layout(data_dir)
    source = fetch_long_samples(layout, limit, minimum_seconds)
    generate_forms(layout, source)
    write_gallery(layout.output)


def dependencies():
    try:
        import diffusers  # noqa: F401
        import soundfile  # noqa: F401
        import torch  # noqa: F401
    except ImportError as error:
        raise typer.BadParameter("Install inference dependencies with: uv run --group art main.py art ...") from error


@app.command("fetch")
def fetch_command(
    data_dir: DataOption = DEFAULT_DATA,
    per_dataset: Annotated[int, typer.Option(min=1, max=12)] = 3,
    offset: Annotated[int, typer.Option(min=0)] = 0,
):
    """Download six real clips by default: three DSWP and three OpenWhistle."""
    print(fetch_samples(Layout(data_dir), per_dataset, offset))


@app.command("analyze")
def analyze_command(
    data_dir: DataOption = DEFAULT_DATA,
    audio_dir: Annotated[Path | None, typer.Option(exists=True, file_okay=False)] = None,
    vocabulary: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    device: DeviceOption = "auto",
    revision: Annotated[str | None, typer.Option(help="Optional CLAP commit or tag.")] = None,
):
    """Cache CLAP scores, audio preprocessing and shared RMS controls."""
    dependencies()
    from .audio import VOCABULARY, analyze

    print(analyze(Layout(data_dir), audio_dir, vocabulary or VOCABULARY, device, revision=revision))


@app.command("materials")
def materials_command(
    data_dir: DataOption = DEFAULT_DATA,
    analysis: AnalysisOption = None,
    output: OutputOption = None,
    seed: SeedOption = 20261004,
    steps: Annotated[int, typer.Option(min=1, max=8)] = 4,
    device: DeviceOption = "auto",
    shuffle: Annotated[bool, typer.Option(help="Shuffle descriptor assignments as a comparison.")] = False,
    revision: Annotated[str | None, typer.Option(help="Optional FLUX.2 klein commit or tag.")] = None,
    livia_dir: LiviaOption = ROOT.parent / "livia",
    livistone_dir: LivistoneOption = ROOT.parent / "livistone",
):
    """Generate jewelry and pavilion concepts using actual artist references."""
    dependencies()
    from .images import materials

    layout = Layout(data_dir)
    from .artist import prepare_artist

    artist = prepare_artist(layout, livia_dir, livistone_dir)
    materials(layout, analysis or layout.interim / "analysis.json", output, seed, steps, device, shuffle, revision, artist=artist)


@app.command("painting")
def painting_command(
    image: ImageOption,
    data_dir: DataOption = DEFAULT_DATA,
    analysis: AnalysisOption = None,
    output: OutputOption = None,
    prompt: Annotated[str | None, typer.Option(help="Fixed edit prompt template; sound adds material and degree instructions.")] = None,
    limit: Annotated[int, typer.Option(min=1, max=24)] = 4,
    seed: SeedOption = 20261004,
    steps: Annotated[int, typer.Option(min=1, max=8)] = 4,
    edit_min: Annotated[float, typer.Option(min=0.01, max=1)] = 0.30,
    edit_max: Annotated[float, typer.Option(min=0.01, max=1)] = 0.55,
    device: DeviceOption = "auto",
    revision: Annotated[str | None, typer.Option(help="Optional FLUX.2 klein commit or tag.")] = None,
):
    """Alter one artwork with bounded sound controls; retain original alongside edits."""
    dependencies()
    from .images import painting

    layout = Layout(data_dir)
    painting(layout, analysis or layout.interim / "analysis.json", image, output, prompt, limit, seed, steps,
             edit_min, edit_max, device, revision)


@app.command("demo")
def demo_command(
    image: ImageOption,
    data_dir: DataOption = DEFAULT_DATA,
    prompt: Annotated[str | None, typer.Option(help="Fixed image-to-image prompt.")] = None,
    seed: SeedOption = 20261004,
    device: DeviceOption = "auto",
    livia_dir: LiviaOption = ROOT.parent / "livia",
    livistone_dir: LivistoneOption = ROOT.parent / "livistone",
):
    """Fetch six clips, analyze them, generate both experiments sequentially."""
    dependencies()
    from .audio import analyze
    from .images import materials, painting
    from .artist import prepare_artist

    layout = Layout(data_dir)
    fetch_samples(layout)
    analysis = analyze(layout, device=device)
    artist = prepare_artist(layout, livia_dir, livistone_dir)
    materials(layout, analysis, seed=seed, device=device, artist=artist)
    painting(layout, analysis, image, prompt=prompt, seed=seed, device=device, artist=artist)
    from .gallery import write_gallery

    write_gallery(layout.output)


@app.command("silver")
def silver_command(
    data_dir: DataOption = DEFAULT_DATA,
    drive: Annotated[Path, typer.Option(exists=True, file_okay=False, help="Livia's STL archive (drive-folder).")] = Path.home() / "Downloads" / "drive-folder",
    livia_dir: LiviaOption = ROOT.parent / "livia",
    piece: Annotated[list[str] | None, typer.Option(help="Piece id from resources/sound-silver.json; repeatable. Default: all.")] = None,
    sound: Annotated[list[str] | None, typer.Option(help="Sound id; repeatable. Default: all.")] = None,
    output: OutputOption = None,
    stl: Annotated[bool, typer.Option(help="Write full-resolution STLs at each safe limit.")] = True,
):
    """Bend Livia's stoneless rings with sound; casting checks, safe limits and a live 3D viewer. Needs art + mesh."""
    from .silver import run

    print(f"Viewer: {run(Layout(data_dir), drive, livia_dir, piece, sound, output, stl) / 'index.html'}")


@app.command("silver-motion")
def silver_motion_command(
    data_dir: DataOption = DEFAULT_DATA,
    drive: Annotated[Path, typer.Option(exists=True, file_okay=False, help="Livia's STL archive (drive-folder).")] = Path.home() / "Downloads" / "drive-folder",
    output: OutputOption = None,
):
    """Animated studies of moving versions (ferrofluid, nitinol hinges, magnetic fins, memory cells). Run `art silver` first."""
    from .silver_motion import run

    print(f"Motion studies: {run(Layout(data_dir), drive, output)}")


brush_app = typer.Typer(help="Human-operated sound brush: keys → emitted audio → measured contour → stroke.", no_args_is_help=True)
app.add_typer(brush_app, name="brush")
StoneOption = Annotated[str, typer.Option(help="Stone at the centre: mitoring (amber) or mycelium (opal).")]


@brush_app.command("keys")
def brush_keys_command():
    """Print the keyboard map: which key plays which recording or synthesized contour."""
    from .brush import load_config

    config = load_config()
    for pitch_class, source in config["keyboard"]["pitch_classes"].items():
        family = source.get("family")
        title = config["families"][family]["title"] if family else f"recorded {source['recording']}"
        command = config["commands"].get(family, "beads" if family == "clicks" else "—") if family else "measured, not designed"
        print(f"{pitch_class:3s} {title:36s} designed command: {command}")
    print("\nPhrase syntax: NOTE:SECONDS[@VELOCITY][~BEND] and rest:SECONDS, e.g. 'C4:0.8@100 E4:1.0~-0.5 rest:0.4 F4:0.9'")


@brush_app.command("play")
def brush_play_command(
    phrase: Annotated[str | None, typer.Argument(help="Typed phrase, e.g. 'C4:0.8@100 E4:1.0 rest:0.4 F4:0.9'.")] = None,
    midi: Annotated[Path | None, typer.Option(exists=True, dir_okay=False, help="MIDI file recorded from a keyboard.")] = None,
    name: Annotated[str, typer.Option(help="Output file stem.")] = "phrase",
    stone: StoneOption = "mitoring",
    data_dir: DataOption = DEFAULT_DATA,
    output: OutputOption = None,
):
    """Render a phrase or MIDI file to audio, then draw from that audio alone; needs art + viz (+ midi)."""
    from .brush import load_config, parse_midi, parse_phrase, perform

    if (phrase is None) == (midi is None):
        raise typer.BadParameter("Give either a PHRASE or --midi")
    config = load_config()
    layout = Layout(data_dir)
    events = parse_midi(midi, config) if midi else parse_phrase(phrase, config)
    record = perform(layout, events, config, output or layout.output / "brush" / "played", name, stone, name, phrase=phrase, midi=midi)
    for segment in record["segments"]:
        print(f"{segment['index']:2d} {segment['kind']:6s} {segment['start_s']:6.2f}s  {segment['recognition']['command']:7s} {segment['recognition']['reason']}")
    print(f"Stroke {record['stroke_sha256'][:16]} · {record['metrics']} · {record['timing_ms']}")


@brush_app.command("draw")
def brush_draw_command(
    audio: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Any WAV/FLAC: a saved performance or a recording.")],
    name: Annotated[str | None, typer.Option(help="Output file stem; defaults to the audio stem.")] = None,
    stone: StoneOption = "mitoring",
    data_dir: DataOption = DEFAULT_DATA,
    output: OutputOption = None,
):
    """Draw from an audio file without any keyboard data; identical audio gives an identical stroke."""
    from .brush import load_config, save_drawing
    from .data import write_json

    layout = Layout(data_dir)
    directory = output or layout.output / "brush" / "drawn"
    record = save_drawing(directory, name or audio.stem, audio, load_config(), stone, audio.name)
    write_json(directory / f"{name or audio.stem}-record.json", record)
    print(f"Stroke {record['stroke_sha256']} · {record['metrics']}")


@brush_app.command("study")
def brush_study_command(
    data_dir: DataOption = DEFAULT_DATA,
    learned: Annotated[bool, typer.Option(help="Also compare OpenWhistle embeddings with measured contours.")] = True,
    device: DeviceOption = "auto",
):
    """Keys, performances, one-feature changes, replay checks, learned comparison and gallery."""
    from .brush_study import study

    print(f"Gallery: {study(Layout(data_dir), learned, device)}")


@brush_app.command("live")
def brush_live_command(
    port: Annotated[str | None, typer.Option(help="MIDI input port name; list with --list-ports.")] = None,
    virtual: Annotated[bool, typer.Option(help="Open a virtual input port named whales-sound-brush.")] = False,
    list_ports: Annotated[bool, typer.Option(help="Print available MIDI inputs and exit.")] = False,
    phrase_gap: Annotated[float, typer.Option(min=0.2, max=10, help="Seconds of silence that end a phrase.")] = 1.5,
    phrases: Annotated[int, typer.Option(min=1, max=100)] = 1,
    stone: StoneOption = "mitoring",
    play: Annotated[bool, typer.Option(help="Play the emitted audio with pw-play/paplay/aplay after each phrase.")] = False,
    figures: Annotated[bool, typer.Option(help="Also draw the slower spectrogram explanation for each phrase.")] = False,
    data_dir: DataOption = DEFAULT_DATA,
):
    """Phrase-level live loop from a MIDI keyboard; needs art + viz + midi."""
    if list_ports:
        import mido

        print("\n".join(mido.get_input_names()) or "No MIDI inputs")
        return
    if port is None and not virtual:
        raise typer.BadParameter("Give --port NAME or --virtual")
    from .brush_study import live

    print(f"Saved {live(Layout(data_dir), port, virtual, phrase_gap, phrases, stone, play, figures)}")
