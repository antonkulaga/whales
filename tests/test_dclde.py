import csv
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dclde import RemoteZip, interval_union, summarize
from dclde_visuals import deployment_join
import polars as pl


class MetadataAnalysisTests(unittest.TestCase):
    def test_interval_union_handles_nesting_overlap_and_gaps(self):
        self.assertEqual(interval_union([(5, 6), (0, 2), (1, 3), (0.5, 1), (6, 7)]), 5)
        self.assertEqual(interval_union([]), 0)

    def test_summary_preserves_unknowns_and_separates_recordings_and_event_scope(self):
        fields = ["", "Soundfile", "Dataset", "Provider", "ClassSpecies", "Ecotype",
                  "AnnotationLevel", "FileBeginSec", "FileEndSec", "UTC", "KW_certain",
                  "LowFreqHz", "HighFreqHz"]
        base = {"Soundfile": "a.flac", "Dataset": "site-a", "Provider": "provider",
                "ClassSpecies": "KW", "Ecotype": "SRKW", "AnnotationLevel": "Call",
                "FileBeginSec": "0", "FileEndSec": "2", "UTC": "2020-01-01 00:00:00",
                "KW_certain": "1", "LowFreqHz": "100", "HighFreqHz": "200"}
        rows = [base.copy(), {**base, "FileBeginSec": "1", "FileEndSec": "3", "AnnotationLevel": "Detection"},
                {**base, "ClassSpecies": "HW", "Ecotype": "NA", "FileBeginSec": "5", "FileEndSec": "6"},
                {**base, "ClassSpecies": "AB", "Ecotype": "NA", "AnnotationLevel": "File", "FileEndSec": "100"},
                {**base, "Soundfile": "b.flac", "Ecotype": "NA", "FileBeginSec": "-1", "LowFreqHz": "NA"},
                {**base, "Dataset": "site-b", "Ecotype": "TKW", "FileEndSec": "1"}, base.copy()]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Annotations.csv"
            with source.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fields)
                writer.writeheader()
                writer.writerows({**row, "": str(i)} for i, row in enumerate(rows))
            stats = summarize(source, root / "out")["statistics"]
        self.assertEqual(stats["annotations"], 7)
        self.assertEqual(stats["recordings"], 3)
        self.assertEqual(stats["distinct_soundfile_names"], 2)
        self.assertEqual(stats["exact_duplicate_rows_excluding_export_index"], 1)
        self.assertEqual(stats["invalid_or_missing_time_bounds"], 1)
        self.assertEqual(stats["invalid_or_missing_frequency_bounds"], 1)
        self.assertAlmostEqual(stats["summed_annotation_hours"] * 3600, 8)
        self.assertAlmostEqual(stats["union_annotated_hours"] * 3600, 5)
        self.assertEqual(stats["orca_annotations_without_ecotype"], 1)
        self.assertEqual(next(r["annotations"] for r in stats["groups"]["Ecotype"] if r["Ecotype"] == "NA"), 3)


class ByteRangeTests(unittest.TestCase):
    def test_refuses_full_archive_response(self):
        class Response(io.BytesIO):
            status = 200
            headers = {}
        with patch("dclde.urlopen", return_value=Response(b"whole archive")):
            with self.assertRaisesRegex(ValueError, "refusing full ZIP"):
                RemoteZip("https://example.org/model.zip", 1000).read(10)

    def test_validates_content_range_and_returns_only_requested_bytes(self):
        class Response(io.BytesIO):
            status = 206
            headers = {"Content-Range": "bytes 4-6/10"}
        with patch("dclde.urlopen", return_value=Response(b"abc")) as fetch:
            remote = RemoteZip("https://example.org/model.zip", 10)
            remote.seek(4)
            self.assertEqual(remote.read(3), b"abc")
            self.assertEqual(remote.tell(), 7)
            self.assertEqual(remote.transferred_bytes, 3)
            self.assertEqual(fetch.call_args.args[0].get_header("Range"), "bytes=4-6")


class DeploymentMapTests(unittest.TestCase):
    def test_aliases_withheld_coordinates_and_sign_errors_do_not_invent_locations(self):
        frame = pl.DataFrame({'Provider': ['SMRUConsulting', 'DFO_WDLP', 'UAF_NGOS', 'other'],
                              'Dataset': ['LimeKiln', 'StrGeoN2', 'RB_67424266', 'LimeKiln'],
                              'Soundfile': ['a', 'b', 'c', 'd'], 'ClassSpecies': ['KW'] * 4})
        table = [{'provider': 'SMRU', 'dataset': 'LmKln', 'location': 'Lime Kiln',
                  'lat': '48.51', 'lon': '−123.15'},
                 {'provider': 'UAF_NGOS', 'dataset': 'RB_67424266', 'location': 'Resurrection Bay',
                  'lat': '59.733', 'lon': '149.53'}]
        rows = {r['Provider']: r for r in deployment_join(frame, table)}
        self.assertEqual(rows['SMRUConsulting']['longitude'], -123.15)
        self.assertEqual(rows['SMRUConsulting']['source_dataset'], 'LmKln')
        self.assertEqual(rows['DFO_WDLP']['coordinate_status'], 'withheld')
        self.assertIsNone(rows['DFO_WDLP']['longitude'])
        self.assertEqual(rows['UAF_NGOS']['coordinate_status'], 'inconsistent_longitude_sign')
        self.assertIsNone(rows['UAF_NGOS']['longitude'])
        self.assertEqual(rows['UAF_NGOS']['source_longitude'], '149.53')
        self.assertEqual(rows['other']['coordinate_status'], 'unmatched')


if __name__ == "__main__":
    unittest.main()
