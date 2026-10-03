import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import polars as pl
from typer.testing import CliRunner

from main import ROOT, app, inspect_dataset


class CliTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_json_catalog_preserves_inventory(self):
        result = self.runner.invoke(app, ["catalog", "--json"])
        self.assertEqual(result.exit_code, 0, result.output)
        expected = json.loads((ROOT / "resources/datasets.json").read_text())
        self.assertEqual(json.loads(result.output), expected)

    def test_csv_catalog_preserves_labels_and_optional_metadata(self):
        expected = json.loads((ROOT / "resources/datasets.json").read_text())["datasets"]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "datasets.csv"
            result = self.runner.invoke(app, ["catalog", "--csv", str(output)])
            self.assertEqual(result.exit_code, 0, result.output)
            rows = pl.read_csv(output).to_dicts()
        self.assertEqual(len(rows), len(expected))
        for actual, source in zip(rows, expected):
            for field, value in source.items():
                self.assertEqual(actual[field], value)

    def test_invalid_contour_options_do_not_fetch_data(self):
        with patch("main.sample_contours") as fetch:
            for options in (["--limit", "0"], ["--offset", "-1"],
                            ["--min-confidence", "nan"], ["--min-confidence", "1.1"]):
                result = self.runner.invoke(app, ["contours", *options])
                self.assertEqual(result.exit_code, 2, result.output)
            fetch.assert_not_called()

    def test_hub_sdk_metadata_and_config_specific_labels(self):
        hub = SimpleNamespace(sha="revision", gated=False, card_data={"license": "cc-by-4.0"})
        configs = {
            "balanced": {"features": {"label": {"_type": "ClassLabel", "names": ["NSW", "SW_Luna"]}}, "splits": {}},
            "all": {"features": {"label": {"_type": "ClassLabel", "names": ["SW_Luna", "NSW"]}}, "splits": {}},
        }
        with patch("main.HfApi") as api, patch("main.get_json", return_value={"dataset_info": configs}):
            api.return_value.dataset_info.return_value = hub
            result = inspect_dataset("example/dataset", config="balanced")
            api.return_value.dataset_info.assert_called_once_with("example/dataset", timeout=45)
        self.assertEqual(result["hub_revision_at_inspection"], "revision")
        self.assertEqual(result["declared_license"], "cc-by-4.0")
        self.assertEqual(result["configs"]["balanced"]["class_labels"]["label"]["1"], "SW_Luna")
        self.assertNotIn("all", result["configs"])


if __name__ == "__main__":
    unittest.main()
