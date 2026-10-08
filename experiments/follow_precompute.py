"""Precompute unordered duos, loading ACE-Step once and preserving completed work on restart."""

from itertools import combinations
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .data import Layout, now, read_json, write_json
from .follow import directories, run_ace
from .follow_combine import RENDER_VERSION, ace_job, catalog, combine, plan, prepared_sources, saved_render


def duo_specs(config: dict, prepared: dict, only=None):
    ids = {s["id"] for s in config["sources"] if s.get("map") is not False}
    if only:
        unknown = set(only) - ids
        if unknown:
            raise ValueError(f"Unknown map sources: {', '.join(sorted(unknown))}")
        ids &= set(only)
    missing = ids - prepared.keys()
    if missing:
        raise ValueError(f"Unprepared sources: {', '.join(sorted(missing))}; run 'main.py follow prepare' first")
    if len(ids) < 2:
        raise ValueError("Choose at least two prepared map sources")
    return [{"arrangement": "layer", "gap_s": 1,
             "parts": [{"source": a, "offset_s": 0}, {"source": b, "offset_s": 0}], "ace": {"task": "cover"}}
            for a, b in combinations(sorted(ids), 2)]


def render_piece(args):
    layout, config, spec, finalize = args
    if finalize:
        folder = directories(layout)[1] / "combos" / plan(spec, config, prepared_sources(layout))["id"]
        if not (folder / "ace.wav").exists():
            raise ValueError(f"Missing generated music in {folder}; rerun the batch to resume")
    return combine(layout, config, spec, run_model=finalize)


def render_pieces(layout, config, specs, finalize, workers):
    args = ((layout, config, spec, finalize) for spec in specs)
    if workers == 1:
        yield from map(render_piece, args)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            yield from pool.map(render_piece, args)


def precompute_duos(layout: Layout, config: dict, only=None, ace_root: Path | None = None, offload: bool = False, workers: int = 1):
    interim, output = directories(layout)
    prepared = prepared_sources(layout)
    specs = duo_specs(config, prepared, only)
    combos = [plan(spec, config, prepared) for spec in specs]
    results_path = interim / "duos-ace-results.json"
    previous = read_json(results_path) if results_path.exists() else {"jobs": {}}
    jobs = []
    unfinished = [(spec, combo) for spec, combo in zip(specs, combos)
                  if not saved_render(output / "combos" / combo["id"], output, needs_ace=True)]
    print(f"Precomputing {len(specs)} duos; both players start at 0 s, seed {config['seed']}", flush=True)
    pending_specs = [spec for spec, _ in unfinished]
    for index, (_, (_, combo)) in enumerate(zip(render_pieces(layout, config, pending_specs, False, workers), unfinished), 1):
        folder = output / "combos" / combo["id"]
        job = ace_job(combo, config, folder)
        own_results = folder / "ace-results.json"
        # A stopped batch already saves timings after each job. Restore them before resuming.
        if (folder / "ace.wav").exists() and not own_results.exists() and job["id"] in previous["jobs"]:
            write_json(own_results, {**previous, "jobs": {job["id"]: previous["jobs"][job["id"]]}})
        if not (folder / "ace.wav").exists() or not own_results.exists():
            jobs.append(job)
        if index % 10 == 0 or index == len(unfinished):
            print(f"Guides ready: {index}/{len(unfinished)}; {len(jobs)} music jobs pending", flush=True)
    if jobs:
        results = run_ace(layout, config, jobs, interim / "duos-ace-jobs.json", results_path, ace_root, offload)
        for job in jobs:
            write_json(Path(job["output"]).parent / "ace-results.json", {**results, "jobs": {job["id"]: results["jobs"][job["id"]]}})
    for index, _ in enumerate(render_pieces(layout, config, pending_specs, True, workers), 1):
        if index % 10 == 0 or index == len(unfinished):
            print(f"Playback files ready: {index}/{len(unfinished)}", flush=True)
    catalog(layout, config)
    index_path = output / "duos.json"
    write_json(index_path, {"created_at_utc": now(), "config_sha256": config["config_sha256"], "render_version": RENDER_VERSION,
                            "pieces": [{"id": c["id"], "spec": c} for c in combos]})
    print(f"All {len(combos)} duos ready → {index_path}", flush=True)
    return index_path
