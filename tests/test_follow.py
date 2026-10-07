import importlib.util
from pathlib import Path
import tempfile
import unittest

from typer.testing import CliRunner

from main import app

ART = all(importlib.util.find_spec(name) for name in ("numpy", "scipy", "soundfile"))
RATE = 48000


def tonal(start, end, hz_start, hz_end, label="unit"):
    return {"kind": "tonal", "start_s": start, "end_s": end, "time_s": [start, end], "hz": [hz_start, hz_end], "label": label, "origin": "test"}


class FollowCliTests(unittest.TestCase):
    def test_follow_commands_are_registered(self):
        result = CliRunner().invoke(app, ["follow", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)
        for command in ("fetch", "prepare", "generate", "evaluate", "page", "run"):
            self.assertIn(command, result.output)

    def test_unknown_condition_is_rejected_before_any_work(self):
        result = CliRunner().invoke(app, ["follow", "generate", "--condition", "remix"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("remix", result.output)

    def test_selection_table_keeps_units_inside_the_excerpt(self):
        from experiments.follow import read_units

        table = ("Selection\tBegin Time (s)\tEnd Time (s)\tLow Freq (Hz)\tHigh Freq (Hz)\tCall Type\n"
                 "1\t9.0\t11.0\t100\t900\tMoan\n2\t12.5\t14.0\t200\t1500\tGrowl\n3\t39.0\t41.0\t50\t800\tWhup\n")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "table.txt"
            path.write_text(table, encoding="utf-8")
            units = read_units(path, 10.0, 30.0)
        self.assertEqual([u["label"] for u in units], ["Growl"])
        self.assertAlmostEqual(units[0]["start_s"], 2.5)
        self.assertAlmostEqual(units[0]["end_s"], 4.0)

    def test_jobs_fix_caption_and_seed_and_route_sources(self):
        from experiments.data import Layout
        from experiments.follow import CONDITIONS, ace_jobs, load_config

        config = load_config()
        prepared = {"sources": [{"id": "humpback-a", "species": "humpback", "duration_s": 30.0,
                                 "stems": {"animal": "humpback-a/animal.wav", "guide": "humpback-a/guide.wav", "perturbed": "humpback-a/perturbed.wav"}}]}
        jobs = {job["condition"]: job for job in ace_jobs(Layout(Path("/tmp/follow-test")), config, prepared)}
        self.assertEqual(set(jobs), set(CONDITIONS))
        self.assertEqual(len({(job["caption"], job["seed"], job["inference_steps"]) for job in jobs.values()}), 1)
        self.assertIsNone(jobs["prompt"]["src_audio"])
        self.assertTrue(jobs["raw"]["src_audio"].endswith("animal.wav"))
        self.assertTrue(jobs["cover-perturbed"]["src_audio"].endswith("perturbed.wav"))
        self.assertEqual(jobs["guide"]["track"], "keyboard")
        self.assertIsNone(jobs["cover-guide"]["track"])


@unittest.skipUnless(ART, "Run with uv run --group art")
class FollowSignalTests(unittest.TestCase):
    def test_perturbation_mirrors_order_and_inverts_contours(self):
        from experiments.follow import onsets, perturb

        events = [tonal(1.0, 2.0, 400, 800), {"kind": "click", "time_s": 5.0, "group": 0}, tonal(6.0, 6.5, 300, 300)]
        mirrored = perturb(events, 10.0)
        self.assertEqual(onsets(mirrored), [3.5, 5.0, 8.0])
        rise = next(e for e in mirrored if e["kind"] == "tonal" and e["start_s"] == 8.0)
        self.assertGreater(rise["hz"][0], rise["hz"][-1])  # a rise becomes a fall
        self.assertAlmostEqual(rise["hz"][0] * rise["hz"][-1], 400 * 800, places=3)  # around the same geometric median
        self.assertEqual(perturb(mirrored, 10.0)[0]["start_s"], 1.0)

    def test_guide_transposes_the_contour_by_whole_octaves(self):
        import numpy as np

        from experiments.follow import register_shift, render_guide

        events = [tonal(0.5, 1.5, 8000, 8000)]
        shift = register_shift(events, 523)
        self.assertEqual(shift, -4)
        instrument = {"harmonics": [1, .3], "attack_s": .01, "release_s": .01, "level": .5}
        audio = render_guide(events, 2.0, RATE, instrument, shift)
        window = audio[round(.8 * RATE):round(1.2 * RATE)]
        spectrum = np.abs(np.fft.rfft(window * np.hanning(len(window))))
        self.assertAlmostEqual(np.fft.rfftfreq(len(window), 1 / RATE)[np.argmax(spectrum)], 500, delta=5)
        self.assertLess(np.abs(audio[:round(.4 * RATE)]).max(), 1e-9)

    def test_f0_tracker_finds_the_fundamental_under_a_louder_harmonic(self):
        import numpy as np

        from experiments.follow import f0_track

        t = np.arange(2 * RATE) / RATE
        tone = .2 * np.sin(2 * np.pi * 150 * t) + .5 * np.sin(2 * np.pi * 300 * t) + .9 * np.sin(2 * np.pi * 450 * t)
        settings = {"range_hz": [60, 1200], "harmonics": 6, "decay": .84, "n_fft": 4096, "hop": 480, "median_frames": 11}
        times, hz = f0_track(tone, RATE, .5, 1.5, settings)
        self.assertAlmostEqual(float(np.median(hz)), 150, delta=3)
        self.assertGreaterEqual(min(times), .5)
        self.assertLessEqual(max(times), 1.5)

    def test_timing_score_separates_following_from_unrelated_music(self):
        import numpy as np

        from experiments.follow import onsets, respond
        from experiments.follow_metrics import onset_envelope, timing

        rng = np.random.default_rng(7)
        starts = np.sort(rng.uniform(.5, 19, 14))
        events = [tonal(s, s + .4, 300, 450) for s in starts]
        rules = {"tonal": {"chord_semitones": [-12, -5, 0], "pad_harmonics": [1, .4], "pad_attack_s": .02, "pad_release_s": .3, "pad_level": .2,
                           "bass_semitones": -24, "bass_decay_s": .3, "bass_level": .3}, "clicks": {}}
        env = onset_envelope(respond(events, 20.0, RATE, 0, rules), RATE, 100)
        own = timing(env, onsets(events), 100, .04, 1.0)
        other = timing(env, list(np.sort(rng.uniform(.5, 19, 14))), 100, .04, 1.0)
        self.assertGreater(own["z"], 3)
        self.assertLess(abs(other["z"]), 3)
        self.assertGreater(own["z"], other["z"] + 3)

    def test_event_f1_matches_within_tolerance_once(self):
        from experiments.follow_metrics import f1

        self.assertEqual(f1([1.0, 2.0], [1.05, 2.0], .075), 1.0)
        self.assertEqual(f1([1.0, 1.02], [1.0], .075), 2 / 3)
        self.assertEqual(f1([], [1.0], .075), 0.0)

    def test_pitch_agreement_prefers_the_rendered_contour(self):
        import numpy as np

        from experiments.follow import render_guide
        from experiments.follow_metrics import chroma, guide_chroma, pitch

        steps = [220, 247, 262, 294, 330, 262, 196, 220, 349, 330]
        events = [tonal(.2 + i * .9, .2 + i * .9 + .7, hz, hz) for i, hz in enumerate(steps)]
        instrument = {"harmonics": [1, .3], "attack_s": .02, "release_s": .05, "level": .5}
        audio = render_guide(events, 9.5, RATE, instrument, 0)
        out = chroma(audio, RATE, 100, (60, 4000))
        own = pitch(out, guide_chroma(events, 0, out.shape[1], 100), 1.0, 100)
        shuffled = [dict(e, hz=[h, h]) for e, h in zip(events, np.random.default_rng(3).permutation(steps))]
        other = pitch(out, guide_chroma(shuffled, 0, out.shape[1], 100), 1.0, 100)
        self.assertGreater(own["value"], .8)
        self.assertGreater(own["z"], 3)
        self.assertGreater(own["value"], other["value"])

    def test_leakage_detects_a_copied_source(self):
        import numpy as np

        from experiments.follow_metrics import leakage

        rng = np.random.default_rng(1)
        source, music = rng.normal(size=RATE), rng.normal(size=RATE)
        self.assertGreater(leakage(np.roll(source, 480) + .5 * music, source, RATE), .8)
        self.assertLess(leakage(music, source, RATE), .05)


if __name__ == "__main__":
    unittest.main()
