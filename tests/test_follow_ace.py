import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from experiments import follow_ace


class AceRuntimeTests(unittest.TestCase):
    def run_job(self, cuda):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            jobs = root / "jobs.json"
            output = root / "music.wav"
            results = root / "results.json"
            jobs.write_text(json.dumps({
                "ace_root": folder, "model": "acestep-v15-base", "offload": True,
                "quantization": "int8_weight_only", "results": str(results),
                "jobs": [{"id": "test", "task": "cover", "track": None, "src_audio": "guide.wav",
                          "caption": "ambient music", "duration": 10, "seed": 42, "inference_steps": 2,
                          "guidance_scale": 7, "audio_cover_strength": .6, "output": str(output)}],
            }))
            handler = Mock()
            handler.initialize_service.return_value = ("ready", True)
            handler.generate_instruction.return_value = "test instruction"
            device_name = Mock(return_value="Test GPU") if cuda else Mock(side_effect=AssertionError("CPU must not query a CUDA device"))
            torch = SimpleNamespace(__version__="test", cuda=SimpleNamespace(is_available=lambda: cuda, get_device_name=device_name))

            def generate(*args, save_dir, progress):
                progress(.8, desc="Decoding audio…")
                audio = Path(save_dir) / "generated.wav"
                audio.write_bytes(b"generated audio")
                return SimpleNamespace(success=True, audios=[{"path": str(audio), "params": {"seed": 42}}], status_message="done")

            modules = {
                "torch": torch,
                "acestep.handler": SimpleNamespace(AceStepHandler=lambda: handler),
                "acestep.inference": SimpleNamespace(GenerationConfig=SimpleNamespace, GenerationParams=SimpleNamespace, generate_music=generate),
                "acestep.llm_inference": SimpleNamespace(LLMHandler=Mock()),
                "acestep.model_downloader": SimpleNamespace(MAIN_MODEL_COMPONENTS=["vae", "unused-lm"]),
            }
            follow_ace.report_progress.last_description = None
            with patch.dict(sys.modules, modules), patch.object(follow_ace.subprocess, "run", return_value=SimpleNamespace(stdout="revision")), \
                    patch.object(sys, "path", sys.path.copy()), contextlib.redirect_stdout(io.StringIO()) as log:
                follow_ace.main(str(jobs))
            self.assertEqual(modules["acestep.model_downloader"].MAIN_MODEL_COMPONENTS, ["vae", "Qwen3-Embedding-0.6B"])
            self.assertEqual(output.read_bytes(), b"generated audio")
            self.assertIn("Decoding audio", log.getvalue())
            self.assertEqual(json.loads(results.read_text())["jobs"]["test"]["seed_used"], 42)
            return handler.initialize_service.call_args.kwargs, json.loads(results.read_text()), device_name

    def test_cpu_renders_without_cuda_only_options_or_device_queries(self):
        options, metadata, device_name = self.run_job(False)
        self.assertEqual(options["device"], "cpu")
        self.assertIsNone(options["quantization"])
        self.assertFalse(options["offload_to_cpu"])
        self.assertFalse(options["offload_dit_to_cpu"])
        self.assertEqual(metadata["device"], "CPU")
        self.assertEqual(metadata["device_type"], "cpu")
        device_name.assert_not_called()

    def test_cuda_keeps_configured_memory_options_and_device_metadata(self):
        options, metadata, device_name = self.run_job(True)
        self.assertEqual(options["device"], "cuda")
        self.assertEqual(options["quantization"], "int8_weight_only")
        self.assertTrue(options["offload_to_cpu"])
        self.assertTrue(options["offload_dit_to_cpu"])
        self.assertEqual(metadata["device"], "Test GPU")
        device_name.assert_called_once_with(0)

    def test_repeated_progress_descriptions_do_not_flood_the_stream(self):
        follow_ace.report_progress.last_description = None
        with contextlib.redirect_stdout(io.StringIO()) as log:
            follow_ace.report_progress(.5, desc="Generating music")
            follow_ace.report_progress(.6, desc="Generating music")
            follow_ace.report_progress(.8, desc="Decoding audio")
        self.assertEqual(log.getvalue().splitlines(), ["ACE-Step: Generating music", "ACE-Step: Decoding audio"])
