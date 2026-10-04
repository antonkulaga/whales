"""Snapshot the actual artist references and the documents supporting the brief."""

import copy
from pathlib import Path
import shutil

from .data import Layout, ROOT, digest, read_json, write_json

PROFILE = ROOT / "resources" / "livia-profile.json"


def prepare_artist(layout: Layout, livia_dir: Path, livistone_dir: Path, profile_path: Path = PROFILE):
    roots = {"livia": livia_dir, "livistone": livistone_dir}
    profile = read_json(profile_path)
    profile["profile_sha256"] = digest(profile_path)
    destination = layout.input / "artist"
    destination.mkdir(parents=True, exist_ok=True)
    for source in profile["sources"]:
        path = roots[source["root"]] / source["path"]
        source.update(absolute_path=str(path.resolve()), sha256=digest(path))
    for reference in profile["references"]:
        path = roots[reference["root"]] / reference["path"]
        cached = destination / f"{reference['id']}{path.suffix.lower()}"
        shutil.copy2(path, cached)
        reference.update(source_path=str(path.resolve()), cached_path=str(cached.resolve()), sha256=digest(path))
    write_json(destination / "profile.json", profile)
    return profile


def snapshot_references(profile: dict | None, output: Path):
    """Portable display copies and exactly the padded images supplied to FLUX."""
    if profile is None:
        return None, {}
    from PIL import Image, ImageOps

    copied = copy.deepcopy(profile)
    directory = output / "references"
    directory.mkdir(parents=True, exist_ok=True)
    images = {}
    for reference in copied["references"]:
        source = Path(reference["cached_path"])
        if digest(source) != reference["sha256"]:
            raise ValueError(f"Artist reference changed: {source}")
        destination = directory / source.name
        shutil.copy2(source, destination)
        reference["display_image"] = f"references/{source.name}"
        with Image.open(source) as image:
            padded = ImageOps.pad(ImageOps.exif_transpose(image).convert("RGB"), (512, 512),
                                  color="white", method=Image.Resampling.LANCZOS)
        inference = directory / f"{reference['id']}-model.png"
        padded.save(inference)
        reference["model_image"] = f"references/{inference.name}"
        reference["model_image_sha256"] = digest(inference)
        for style in reference["model_styles"]:
            images.setdefault(style, []).append((reference["id"], padded))
    write_json(directory / "profile.json", copied)
    return copied, images
