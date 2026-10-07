"""Earlier DCLDE releases: call logs, silbido whistle contours, and traced contours as measured events."""

import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

ART = all(importlib.util.find_spec(name) for name in ("numpy", "scipy", "soundfile"))


def silbido(tonals, mask=3, version=4):
    """A minimal .ann file: header, then per tonal a graph id, the node count and (time, freq) doubles."""
    header = b"silbido!" + struct.pack(">HHHI", version, mask, 0, 18)
    body = b"".join(struct.pack(">qi", 7, len(points)) + b"".join(struct.pack(">dd", t, f) for t, f in points) for points in tonals)
    return header + body


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def table(self, name: str, text: str | bytes):
        path = self.root / name
        path.write_bytes(text if isinstance(text, bytes) else text.encode())
        return path

    def test_silbido_contours_read_time_and_frequency(self):
        from experiments.follow_dclde import silbido_contours

        tonals = list(silbido_contours(silbido([[(1.0, 8000.0), (1.1, 9000.0)], [(2.0, 12000.0)]])))
        self.assertEqual(tonals, [[(1.0, 8000.0), (1.1, 9000.0)], [(2.0, 12000.0)]])

    def test_traced_whistles_keep_whole_audible_contours_relative_to_the_window(self):
        from experiments import follow_dclde

        path = self.table("w.ann", silbido([
            [(10.0, 8000.0), (10.004, 8100.0), (10.01, 8200.0), (10.5, 9000.0)],  # inside, thinned to 5 ms steps
            [(9.5, 8000.0), (10.2, 8000.0)],                                        # starts before the window
            [(12.0, 30000.0), (12.3, 31000.0)],                                     # centred above the stems
        ]))
        with mock.patch.object(follow_dclde, "annotation_file", return_value=path):
            units = follow_dclde.traced_whistles(None, {"tables": [{}], "max_hz": 23500}, 10.0, 30.0)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["contour"]["time_s"], [0.0, 0.01, 0.5])
        self.assertEqual((units[0]["low_hz"], units[0]["high_hz"], units[0]["selection"]), (8000.0, 9000.0, 1))

    def test_raven_log_rows_are_timed_from_the_file_start_and_filtered(self):
        from experiments import follow_dclde

        path = self.table("log.csv", '"Selection","Start_DateTime_ISO8601","End_DateTime_ISO8601","Low.Freq..Hz.","High.Freq..Hz.","Species","Detection_Confidence"\n'
                                     '1,"2009-04-01T16:45:10-05:00","2009-04-01T16:45:12-05:00",70,180,"RIWH","Detected"\n'
                                     '2,"2009-04-01T16:45:20-05:00","2009-04-01T16:45:21-05:00",70,180,"RIWH","Possibly_Detected"\n'
                                     '3,"2009-04-01T16:45:30-05:00","2009-04-01T16:45:31-05:00",15,30,"FIWH","Detected"\n')
        spec = {"format": "raven-log", "tables": [{}], "species": "RIWH", "confidence": ["Detected"], "file_start": "2009-04-01T16:45:00-05:00"}
        with mock.patch.object(follow_dclde, "annotation_file", return_value=path):
            rows = follow_dclde.logged_calls(None, spec)
        self.assertEqual(rows, [{"FileBeginSec": 10.0, "FileEndSec": 12.0, "LowFreqHz": "70", "HighFreqHz": "180"}])

    def test_harp_log_reads_utc_times_without_frequencies(self):
        from experiments import follow_dclde

        path = self.table("harp.csv", "CINMS,B,Bm,2012-06-22T06:00:01.5,2012-06-22T06:00:04.0,D\nCINMS,B,Bp,2012-06-22T06:00:10,2012-06-22T06:00:11,40Hz\n")
        spec = {"format": "harp-log", "tables": [{}], "species": "Bm", "file_start": "2012-06-22T05:57:31+00:00"}
        with mock.patch.object(follow_dclde, "annotation_file", return_value=path):
            rows = follow_dclde.logged_calls(None, spec)
        self.assertEqual(rows, [{"FileBeginSec": 150.5, "FileEndSec": 153.0, "LowFreqHz": "NA", "HighFreqHz": "NA"}])
        units = follow_dclde.units_for(rows, 150.0, 30.0)
        self.assertEqual((units[0]["start_s"], units[0]["end_s"], units[0]["low_hz"]), (0.5, 3.0, None))

    def test_a_call_cut_by_the_window_keeps_its_inside_part(self):
        from experiments.follow_dclde import units_for

        row = lambda b, e: {"FileBeginSec": b, "FileEndSec": e, "LowFreqHz": 500, "HighFreqHz": 4000}
        units = units_for([row(8, 11), row(15, 17), row(20, 20.1), row(38, 41), row(39.9, 41)], 10, 30)
        self.assertEqual([(u["start_s"], u["end_s"], u.get("cut")) for u in units],
                         [(0, 1, "start"), (5, 7, None), (10, 10.1, None), (28, 30, "end")])  # short whole calls stay; short cut ends go

    def test_encounter_level_sources_have_no_units(self):
        from experiments.follow_dclde import release_units

        self.assertEqual(release_units(None, {"annotations": None, "duration_s": 30.0}, 0.0), (None, 0))


@unittest.skipUnless(ART, "Needs numpy, scipy and soundfile")
class TracedContourEventTests(unittest.TestCase):
    def test_a_traced_contour_becomes_the_event_and_detected_events_take_the_call_name(self):
        import numpy as np

        from experiments.follow import load_config, measure_events

        species = load_config()["species"]["spinner dolphin"]
        rate = 48000
        t = np.arange(2 * rate) / rate
        waveform = .3 * np.sin(2 * np.pi * 9000 * t) * (t > .5) * (t < 1.2) + 1e-4 * np.random.default_rng(0).standard_normal(len(t))
        unit = {"start_s": .5, "end_s": 1.2, "selection": 1, "label": "Spinner dolphin whistle",
                "contour": {"time_s": [.5, .8, 1.2], "hz": [8000.0, 9000.0, 10000.0]}}
        events, counts = measure_events(waveform, rate, species, [unit])
        self.assertEqual(events[0]["hz"], [8000.0, 9000.0, 10000.0])
        self.assertEqual(events[0]["contour"], "analyst-traced contour (silbido)")
        self.assertEqual(counts["annotated_units"], 1)
        detected, _ = measure_events(waveform, rate, species, None, label="Striped dolphin whistle")
        self.assertTrue(detected and all(e["label"] == "Striped dolphin whistle (detected)" for e in detected))


class TrimTests(unittest.TestCase):
    def test_a_call_cut_by_a_trim_keeps_its_inside_contour_and_adds_no_onset_when_its_start_is_cut(self):
        from experiments.follow import onsets
        from experiments.follow_combine import placed

        call = lambda s, e: {"kind": "tonal", "start_s": s, "end_s": e, "time_s": [s, (s + e) / 2, e], "hz": [400.0, 500.0, 600.0], "label": "call"}
        events = placed([call(1, 3), call(9, 12), call(14.95, 16)], [2, 10], 20)
        self.assertEqual([(e["start_s"], e["end_s"], e.get("cut")) for e in events], [(20, 21, "start"), (27, 28, "end")])
        self.assertEqual((events[0]["time_s"], events[0]["hz"]), ([20.0, 21.0], [500.0, 600.0]))
        self.assertEqual(onsets(events), [27])


if __name__ == "__main__":
    unittest.main()
