import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

from typer.testing import CliRunner

from experiments.data import Layout
from main import app

ART = all(importlib.util.find_spec(name) for name in ("numpy", "scipy", "soundfile", "matplotlib"))


class BrushPhraseTests(unittest.TestCase):
    def test_keys_command_lists_synthesized_and_recorded_keys(self):
        result = CliRunner().invoke(app, ["art", "brush", "keys"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Rising sweep", result.output)
        self.assertIn("recorded openwhistle-0002", result.output)

    def test_phrase_grammar_rests_velocity_and_bend(self):
        from experiments.brush import load_config, parse_phrase

        config = load_config()
        events = parse_phrase("C4:0.5@90~+0.5 rest:0.25 F#4:1.0", config)
        self.assertEqual([e["note"] for e in events], [60, 66])
        self.assertEqual(events[0]["source"], {"family": "rise"})
        self.assertEqual(events[1]["source"], {"recording": "openwhistle-0002"})
        self.assertEqual(events[1]["start_s"], 0.75)
        self.assertEqual(events[0]["bend"][-1], [1.0, 0.5])
        for bad in ("H4:1", "C4:9", "C4:0.5@200", "C4:0.5~2", "rest:0.2"):
            with self.assertRaises(ValueError):
                parse_phrase(bad, config)

    @unittest.skipUnless(importlib.util.find_spec("mido"), "Run with uv run --group midi")
    def test_midi_messages_keep_timing_velocity_and_step_bends(self):
        import mido

        from experiments.brush import events_from_messages, load_config

        messages = [(10.0, mido.Message("note_on", note=62, velocity=80)), (10.3, mido.Message("pitchwheel", pitch=4096)),
                    (10.6, mido.Message("note_off", note=62)), (11.0, mido.Message("note_on", note=64, velocity=120)),
                    (11.5, mido.Message("note_on", note=64, velocity=0))]
        events = events_from_messages(messages, load_config())
        self.assertEqual([(e["name"], e["start_s"], e["velocity"]) for e in events], [("D4", 0.0, 80), ("E4", 1.0, 120)])
        self.assertAlmostEqual(events[0]["duration_s"], 0.6)
        values = [value for _, value in events[0]["bend"]]
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[-1], 0.5)
        self.assertEqual(events[1]["bend"][0][1], 0.5)


@unittest.skipUnless(ART, "Run with uv run --group art --group viz")
class BrushSoundTests(unittest.TestCase):
    def setUp(self):
        from experiments.brush import load_config

        self.config = load_config()
        self.directory = Path(tempfile.mkdtemp())
        self.layout = Layout(self.directory / "data")

    def tearDown(self):
        shutil.rmtree(self.directory)

    def play(self, phrase, name="phrase"):
        from experiments.brush import parse_phrase, perform

        return perform(self.layout, parse_phrase(phrase, self.config), self.config, self.directory / "out", name, "mitoring", name,
                       phrase=phrase, figure=False)

    def test_measured_contour_matches_the_synthesized_sweep(self):
        record = self.play("C4:0.8@100")
        (segment,) = record["segments"]
        self.assertAlmostEqual(segment["summary"]["start_hz"], 7000, delta=150)
        self.assertAlmostEqual(segment["summary"]["end_hz"], 14000, delta=300)
        self.assertAlmostEqual(segment["summary"]["net_octaves"], 1.0, delta=.05)

    def test_designed_contours_are_recognized_and_others_rejected(self):
        expected = {"C4": "grow", "D4": "branch", "E4": "fold", "F4": "open", "G4": "beads", "A4": "none", "B4": "none",
                    "C3": "grow", "E5": "fold"}
        for key, command in expected.items():
            record = self.play(f"{key}:0.8@100", key)
            self.assertEqual([s["recognition"]["command"] for s in record["segments"]], [command], key)

    def test_legato_notes_split_at_level_valley(self):
        record = self.play("C4:0.6@100 E4:0.8@100 C4:0.6@100")
        self.assertEqual([s["recognition"]["command"] for s in record["segments"]], ["grow", "fold", "grow"])
        self.assertEqual(record["metrics"]["lifts"], 0)
        record = self.play("C4:0.6@100 rest:0.4 C4:0.6@100", "rest")
        self.assertEqual(record["metrics"]["lifts"], 1)

    def test_one_feature_changes_have_the_designed_effects(self):
        base = self.play("C4:0.9@100", "base")["stroke_events"][0]
        bent = self.play("C4:0.9@100~+1", "bent")["stroke_events"][0]
        longer = self.play("C4:1.8@100", "longer")["stroke_events"][0]
        louder = self.play("C4:0.9@127", "louder")["stroke_events"][0]
        quieter = self.play("C4:0.9@40", "quieter")["stroke_events"][0]
        self.assertAlmostEqual(bent["turn_degrees_first_tip"] - base["turn_degrees_first_tip"], 45, delta=3)
        self.assertAlmostEqual(longer["path_length_units"] / base["path_length_units"], 2, delta=.05)
        self.assertGreater(louder["mean_width_units"], quieter["mean_width_units"] + 6)

    def test_identical_audio_reproduces_the_identical_stroke_without_key_data(self):
        from experiments.brush import analyze_file, stroke_hash

        record = self.play("C4:0.6@100 D4:0.7@90 rest:0.3 F4:0.8@100 G4:0.6@80")
        copy = self.directory / "anonymous.wav"
        shutil.copy2(self.directory / "out" / "phrase.wav", copy)
        *_, first, _ = analyze_file(copy, self.config, "mitoring")
        *_, second, _ = analyze_file(copy, self.config, "mitoring")
        self.assertEqual(stroke_hash(first), record["stroke_sha256"])
        self.assertEqual(stroke_hash(second), record["stroke_sha256"])
        again = self.play("C4:0.6@100 D4:0.7@90 rest:0.3 F4:0.8@100 G4:0.6@80", "again")
        self.assertEqual(again["audio_sha256"], record["audio_sha256"])
        nudged = self.play("C4:0.6@99 D4:0.7@90 rest:0.3 F4:0.8@100 G4:0.6@80", "nudged")
        self.assertNotEqual(nudged["stroke_sha256"], record["stroke_sha256"])

    def test_draw_command_reads_only_the_audio_file(self):
        self.play("E4:0.8@100", "fold")
        output = self.directory / "drawn"
        result = CliRunner().invoke(app, ["art", "brush", "draw", str(self.directory / "out" / "fold.wav"), "--output", str(output),
                                          "--data-dir", str(self.layout.root)])
        self.assertEqual(result.exit_code, 0, result.output)
        for suffix in (".svg", "-explained.png", "-guide.wav", "-stroke.json", "-record.json"):
            self.assertTrue((output / f"fold{suffix}").exists(), suffix)

    def test_svg_keeps_the_stone_exposed_above_the_strokes(self):
        self.play("C4:0.6@100 F4:0.9@100", "svg")
        svg = (self.directory / "out" / "svg.svg").read_text()
        self.assertGreater(svg.index("<ellipse"), svg.rindex("<polygon"))
        self.assertIn('fill-rule="evenodd"', svg)


if __name__ == "__main__":
    unittest.main()
