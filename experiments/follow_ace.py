"""ACE-Step 1.5 runner for the follow-the-phrase experiment.

Runs inside ACE-Step's own uv environment, never this project's:
    <ace_root>/.venv/bin/python experiments/follow_ace.py data/interim/follow/ace-jobs.json
It imports nothing from `experiments`, loads the DiT once and writes one WAV per
job plus a results JSON with the exact parameters and timings.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def runtime_info():
    import torch

    cuda = torch.cuda.is_available()
    return {"cuda_available": cuda, "device": "cuda" if cuda else "cpu"}


def main(jobs_path: str):
    spec = json.loads(Path(jobs_path).read_text(encoding="utf-8"))
    root = spec["ace_root"]
    sys.path.insert(0, root)
    import torch
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    from acestep.llm_inference import LLMHandler
    from acestep.model_downloader import MAIN_MODEL_COMPONENTS

    # This runner never initializes the LM and loads the selected DiT separately.
    # Limit upstream's download preflight to the main components we actually use;
    # otherwise it downloads the unused turbo and LM checkpoints on CPU servers.
    MAIN_MODEL_COMPONENTS[:] = ["vae", "Qwen3-Embedding-0.6B"]

    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    handler = AceStepHandler()
    started = time.perf_counter()
    device = runtime_info()["device"]
    offload = spec["offload"] if device == "cuda" else False
    quantization = spec["quantization"] if device == "cuda" else None
    print(f"ACE-Step: loading the music model on {device.upper()}" + ("; CPU generation is slower" if device == "cpu" else ""), flush=True)
    status, ready = handler.initialize_service(project_root=root, config_path=spec["model"], device=device,
                                               offload_to_cpu=offload, offload_dit_to_cpu=offload,
                                               quantization=quantization)
    if not ready:
        raise SystemExit(f"ACE-Step did not initialize: {status}")
    load_s = time.perf_counter() - started
    results_path = Path(spec["results"])
    previous = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {"jobs": {}}
    llm = LLMHandler()  # never initialized: lego skips the LM, text2music runs DiT-only
    for job in spec["jobs"]:
        instruction = handler.generate_instruction(job["task"], track_name=job["track"])
        params = GenerationParams(
            task_type=job["task"], instruction=instruction, src_audio=job["src_audio"], caption=job["caption"],
            lyrics="[Instrumental]", instrumental=True, duration=job["duration"], seed=job["seed"],
            inference_steps=job["inference_steps"], guidance_scale=job["guidance_scale"],
            thinking=False, use_cot_metas=False, use_cot_caption=False, use_cot_language=False,
            repainting_start=0.0, repainting_end=-1, audio_cover_strength=job["audio_cover_strength"],
        )
        config = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[job["seed"]], audio_format="wav")
        with tempfile.TemporaryDirectory() as scratch:
            began = time.perf_counter()
            result = generate_music(handler, llm, params, config, save_dir=scratch, progress=report_progress)
            elapsed = time.perf_counter() - began
            if not result.success or not result.audios:
                raise SystemExit(f"{job['id']}: {result.error or result.status_message}")
            output = Path(job["output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(result.audios[0]["path"], output)
        previous["jobs"][job["id"]] = job | {
            "instruction": instruction, "seconds": round(elapsed, 2), "seed_used": result.audios[0]["params"].get("seed"),
            "status": result.status_message,
        }
        print(f"{job['id']}: {elapsed:.0f} s → {output.name}", flush=True)
        previous |= {"ace_root": root, "ace_git_revision": revision, "model": spec["model"], "offload": offload,
                     "quantization": quantization, "model_load_s": round(load_s, 1), "torch": torch.__version__,
                     "device_type": device, "device": torch.cuda.get_device_name(0) if device == "cuda" else "CPU",
                     "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
        results_path.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")


def report_progress(_value=None, desc=None, **_kwargs):
    if desc and desc != report_progress.last_description:
        print(f"ACE-Step: {desc}", flush=True)
        report_progress.last_description = desc


report_progress.last_description = None


if __name__ == "__main__":
    if sys.argv[1] == "--runtime":
        print(json.dumps(runtime_info()))
    else:
        main(sys.argv[1])
