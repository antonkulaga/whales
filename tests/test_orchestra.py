import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import orchestra
from experiments.data import Layout


class EnvTests(unittest.TestCase):
    def load(self, text: str, environ: dict | None = None) -> dict:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text(text, encoding="utf-8")
            with mock.patch.object(orchestra, "ENV", path), mock.patch.dict(os.environ, environ or {}, clear=True):
                orchestra.load_env()
                return dict(os.environ)

    def test_values_quotes_and_comments(self):
        env = self.load('A=1 # note\nexport B="two words"\n# C=3\nD=\nE=\'x # y\'\n')
        self.assertEqual(env["A"], "1")
        self.assertEqual(env["B"], "two words")
        self.assertEqual(env["E"], "x # y")
        self.assertNotIn("C", env)
        self.assertNotIn("D", env)  # blank values stay unset, so HF_TOKEN= means no token

    def test_environment_wins_over_the_file(self):
        self.assertEqual(self.load("ORCHESTRA_PORT=3071\n", {"ORCHESTRA_PORT": "4000"})["ORCHESTRA_PORT"], "4000")

    def test_relative_hf_home_resolves_against_the_repository(self):
        self.assertEqual(self.load("HF_HOME=data/interim/huggingface\n")["HF_HOME"], str(orchestra.ROOT / "data/interim/huggingface"))

    def test_template_sets_every_orchestra_setting(self):
        keys = orchestra.env_keys(orchestra.TEMPLATE, commented=False)
        self.assertLessEqual({"ORCHESTRA_PORT", "ORCHESTRA_HOST", "ORCHESTRA_ACE"}, keys)
        self.assertNotIn("CUDA_VISIBLE_DEVICES", keys)  # optional, shown commented out


class AceSetupTests(unittest.TestCase):
    def test_weight_downloads_exclude_unused_turbo_and_language_model(self):
        download = mock.Mock()
        modules = {
            "huggingface_hub": SimpleNamespace(snapshot_download=download),
            "acestep.model_downloader": SimpleNamespace(check_model_exists=lambda name, root: False),
        }
        with mock.patch.dict(sys.modules, modules), \
                mock.patch.object(sys, "argv", ["weights", "/ace", "base", "model-repo", "model-revision", "main-repo", "main-revision"]):
            exec(orchestra.WEIGHTS, {})
        self.assertEqual(download.call_count, 2)
        main, model = download.call_args_list
        self.assertEqual(main.args, ("main-repo",))
        self.assertEqual(main.kwargs["revision"], "main-revision")
        self.assertEqual(main.kwargs["allow_patterns"], ["vae/*", "Qwen3-Embedding-0.6B/*"])
        self.assertEqual(model.args, ("model-repo",))
        self.assertEqual(model.kwargs["revision"], "model-revision")

    def setup_cpu(self, folder, existing=False, install_ok=True):
        layout = Layout(Path(folder))
        root = layout.interim / orchestra.ACE_DIR
        root.mkdir(parents=True)
        python = root / ".venv" / "bin" / "python"
        if existing:
            python.parent.mkdir(parents=True)
            python.touch()
        report = orchestra.Report()

        def execute(command, **kwargs):
            if command[1:2] == ["venv"]:
                python.parent.mkdir(parents=True, exist_ok=True)
                python.touch()
            return install_ok

        with mock.patch.object(orchestra, "ROOT", Path(folder)), \
                mock.patch.object(orchestra, "gpu", return_value=None), \
                mock.patch.object(orchestra, "output", return_value=orchestra.ACE_COMMIT), \
                mock.patch.object(orchestra, "run", side_effect=execute) as run:
            orchestra.ace_step(report, orchestra.Ace.yes, layout)
        return run, report

    def test_cpu_setup_uses_cpu_wheels_without_upstream_cuda_sync(self):
        with tempfile.TemporaryDirectory() as folder:
            run, report = self.setup_cpu(folder)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0][:4], [orchestra.UV, "venv", "--python", "3.12"])
        self.assertIn("--no-cache", commands[1])
        self.assertEqual(commands[1][6:8], ["--torch-backend", "cpu"])
        self.assertTrue(commands[1][-1].endswith("ace-cpu-requirements.txt"))
        self.assertEqual(len(commands), 3)  # environment, dependencies, pinned weights
        self.assertEqual(report.warnings, [])

    def test_cpu_setup_retries_dependencies_in_an_existing_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            run, report = self.setup_cpu(folder, existing=True)
        self.assertEqual(run.call_args_list[0].args[0][1:3], ["pip", "install"])
        self.assertEqual(run.call_count, 2)
        self.assertEqual(report.warnings, [])

    def test_failed_cpu_install_stops_before_weight_downloads(self):
        with tempfile.TemporaryDirectory() as folder:
            run, report = self.setup_cpu(folder, existing=True, install_ok=False)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("Installing ACE-Step dependencies failed", report.warnings[0])


class RecordingSetupTests(unittest.TestCase):
    def test_fresh_setup_downloads_metadata_without_installing_models(self):
        config = {"sources": [{"id": "dolphin", "file": "long-audio/dolphin.wav"}]}
        with tempfile.TemporaryDirectory() as folder:
            report = orchestra.Report()
            with mock.patch.object(orchestra, "load_config", return_value=config), \
                    mock.patch.object(orchestra, "run", return_value=True) as run:
                orchestra.recordings(report, Layout(Path(folder)))
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0], [orchestra.UV, "run", "main.py", "dclde", "metadata"])
        self.assertEqual(commands[1][:4], [orchestra.UV, "run", "python", "-c"])
        self.assertEqual(commands[2:], [
            [orchestra.UV, "run", "--group", "audio", "main.py", "follow", step]
            for step in ("fetch", "prepare", "catalog")
        ])
        self.assertEqual(report.warnings, [])

    def test_failed_metadata_stops_before_audio_setup_and_reports_the_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            report = orchestra.Report()
            with mock.patch.object(orchestra, "load_config", return_value={"sources": []}), \
                    mock.patch.object(orchestra, "run", return_value=False) as run:
                orchestra.recordings(report, Layout(Path(folder)))
        run.assert_called_once_with([orchestra.UV, "run", "main.py", "dclde", "metadata"])
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("Until then the app plays the demo bundle", report.warnings[0])


if __name__ == "__main__":
    unittest.main()
