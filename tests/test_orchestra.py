import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import orchestra


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


if __name__ == "__main__":
    unittest.main()
