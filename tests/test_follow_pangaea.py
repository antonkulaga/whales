from datetime import datetime, timezone
import importlib.util
import io
import tarfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from experiments.follow_pangaea import cut, day_types, decoded, detection_units, member_bytes, member_start, presence, staged, trimmed

ART = all(importlib.util.find_spec(name) for name in ("numpy", "scipy", "soundfile"))


def archive(members: dict[str, bytes]):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    buffer.seek(0)
    return buffer


class StagingTests(unittest.TestCase):
    def test_retries_while_the_archive_is_on_tape(self):
        busy = HTTPError("https://example.org/a.tar", 503, "loading from tape", {}, None)
        with patch("experiments.follow_pangaea.urlopen", side_effect=[busy, busy, "stream"]) as fetch, \
                patch("experiments.follow_pangaea.time.sleep") as sleep:
            self.assertEqual(staged("https://example.org/a.tar", wait_s=1), "stream")
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_other_errors_are_not_retried(self):
        missing = HTTPError("https://example.org/a.tar", 404, "not found", {}, None)
        with patch("experiments.follow_pangaea.urlopen", side_effect=missing), patch("experiments.follow_pangaea.time.sleep") as sleep:
            with self.assertRaises(HTTPError):
                staged("https://example.org/a.tar")
        sleep.assert_not_called()


class ArchiveTests(unittest.TestCase):
    def test_reads_one_member_from_a_tar_stream(self):
        stream = archive({"day/20120325-000000.wav": b"first", "day/20120325-010000.wav": b"second"})
        self.assertEqual(member_bytes(stream, "20120325-010000.wav"), b"second")

    def test_missing_member_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "not in the archive"):
            member_bytes(archive({"a.wav": b"x"}), "b.wav")

    def test_member_start_comes_from_the_file_name(self):
        expected = datetime(2012, 3, 25, 1, 0, tzinfo=timezone.utc)
        for name in ("20120325-010000_AWI209-6_AU0086.wav", "AU0086_20120325_010000.wav", "20120325T010000.wav"):
            self.assertEqual(member_start(name), expected, name)
        with self.assertRaisesRegex(ValueError, "No start time"):
            member_start("recording.wav")


class LabelTests(unittest.TestCase):
    def test_detections_become_calls_around_each_logged_time(self):
        begin = datetime(2012, 3, 25, 1, 0, tzinfo=timezone.utc)
        rows = [{"ID": "AWI209-06_AU0086", "Date/Time": t, "SPL [dB re 1 µPa]": spl}
                for t, spl in (("2012-03-25T01:00:09", "110"), ("2012-03-25T01:01:09", "114"),
                               ("2012-03-25T01:01:16", "112"), ("2012-03-25T01:01:54", "109"))]
        labels = {"call_window_s": [-4, 16], "band_hz": [17.5, 29]}
        units, inside = detection_units(rows, begin, 60, 60, labels)
        # Calls span 4 s before to 16 s after the logged time. 01:01:09 and 01:01:16 overlap by more than half a call
        # and merge; the call logged at 01:01:54 runs past the window's end, so only its inside part is kept, marked
        # as cut; 01:00:09 is before the window.
        self.assertEqual([(u["start_s"], u["end_s"], u["rows_merged"], u.get("cut")) for u in units], [(5.0, 32.0, 2, None), (50.0, 60, 1, "end")])
        self.assertEqual((units[0]["low_hz"], units[0]["high_hz"]), (17.5, 29))
        self.assertEqual(inside, [{"offset_s": 9.0, "spl_db": 114.0}, {"offset_s": 16.0, "spl_db": 112.0},
                                  {"offset_s": 54.0, "spl_db": 109.0}])

    def test_presence_finds_the_logged_hour(self):
        column = "B. mysticetus pres (Emtpy cells denote hours with...)"
        rows = [{"Date/Time (Start recording)": "2012-11-11T00:00", "Date/Time (End recording)": "2012-11-11T01:00", column: "1"},
                {"Date/Time (Start recording)": "2012-11-11T01:00", "Date/Time (End recording)": "2012-11-11T02:00", column: ""}]
        self.assertTrue(presence(rows, datetime(2012, 11, 11, 0, 30, tzinfo=timezone.utc))["present"])
        self.assertFalse(presence(rows, datetime(2012, 11, 11, 1, 30, tzinfo=timezone.utc))["present"])
        self.assertIsNone(presence(rows, datetime(2012, 11, 11, 3, 0, tzinfo=timezone.utc)))

    def test_song_types_of_one_day_in_numeric_order(self):
        rows = [{"Date/Time": "2016-11-22", "Type": t, "Presence/absence": p}
                for t, p in (("3.3", "1"), ("1.2", "1"), ("10", "1"), ("2.1", "0"), ("3.1", "1"))]
        rows.append({"Date/Time": "2016-11-23", "Type": "4", "Presence/absence": "1"})
        self.assertEqual(day_types(rows, "2016-11-22"), ["1.2", "3.1", "3.3", "10"])


@unittest.skipUnless(ART, "needs numpy, scipy and soundfile")
class WindowTests(unittest.TestCase):
    def test_window_is_cut_and_resampled_to_the_declared_rate(self):
        import numpy as np
        import soundfile as sf

        rate = 32768
        t = np.arange(10 * rate) / rate
        buffer = io.BytesIO()
        sf.write(buffer, .5 * np.sin(2 * np.pi * 25 * t), rate, format="WAV", subtype="PCM_24")
        whole, out_rate, native = decoded(buffer.getvalue(), 2000)
        samples, start_s, total_s = cut(whole, out_rate, 9.0, 4.0)
        self.assertEqual((out_rate, native, total_s), (2000, rate, 10.0))
        self.assertEqual(start_s, 6.0)  # moved back so the whole window fits
        self.assertEqual(len(samples), 8000)
        spectrum = np.abs(np.fft.rfft(samples))
        self.assertAlmostEqual(np.fft.rfftfreq(len(samples), 1 / out_rate)[np.argmax(spectrum)], 25, delta=.5)

    def test_calls_are_trimmed_to_where_their_band_rises_and_silent_ones_dropped(self):
        import numpy as np

        rate = 2000
        t = np.arange(60 * rate) / rate
        rng = np.random.default_rng(1)
        samples = .01 * rng.standard_normal(len(t)) + np.where((t >= 10) & (t < 18), .2 * np.sin(2 * np.pi * 25 * t), 0)
        units = [{"selection": 1, "start_s": 5.0, "end_s": 25.0, "low_hz": 17.5, "high_hz": 29},
                 {"selection": 2, "start_s": 35.0, "end_s": 55.0, "low_hz": 17.5, "high_hz": 29}]
        out = trimmed(samples, rate, units, 6)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0]["start_s"], 10, delta=.6)
        self.assertAlmostEqual(out[0]["end_s"], 18, delta=.6)
        self.assertEqual(out[0]["logged_span_s"], [5.0, 25.0])
        self.assertIsInstance(out[0]["start_s"], float)

    def test_a_window_that_is_mostly_call_is_trimmed_against_the_whole_recording(self):
        import numpy as np

        rate = 2000
        t = np.arange(120 * rate) / rate
        rng = np.random.default_rng(2)
        whole = .01 * rng.standard_normal(len(t)) + np.where((t >= 62) & (t < 84), .2 * np.sin(2 * np.pi * 25 * t), 0)
        window = whole[60 * rate:90 * rate]  # 22 s of call in a 30 s window
        units = [{"selection": 1, "start_s": 0.0, "end_s": 30.0, "low_hz": 17.5, "high_hz": 29}]
        alone, (against_whole,) = trimmed(window, rate, units, 6), trimmed(window, rate, units, 6, whole)
        self.assertAlmostEqual(against_whole["start_s"], 2, delta=.6)
        self.assertAlmostEqual(against_whole["end_s"], 24, delta=.6)
        # Against its own median the call is its own background: it is lost or cut short.
        self.assertTrue(not alone or alone[0]["end_s"] - alone[0]["start_s"] < 20)


if __name__ == "__main__":
    unittest.main()
