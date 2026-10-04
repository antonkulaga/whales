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
