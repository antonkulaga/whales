import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

from typer.testing import CliRunner

from experiments.data import Layout, digest, write_json
from main import app


@unittest.skipUnless(importlib.util.find_spec("soundfile"), "Run with uv run --group art")
class AudioTests(unittest.TestCase):
    def test_listening_gain_preserves_raw_audio_and_sample_timing(self):
        import numpy as np
        import soundfile as sf
        from experiments.audio import listening_copy

        with tempfile.TemporaryDirectory() as directory:
            source, playback = Path(directory) / "raw.wav", Path(directory) / "listen.wav"
            time = np.arange(48000) / 48000
            sf.write(source, .0005 * np.sin(2 * np.pi * 1000 * time), 48000, subtype="FLOAT")
            original_hash = digest(source)
            metadata = listening_copy(source, playback)
            audio, rate = sf.read(playback)
            self.assertEqual(digest(source), original_hash)
            self.assertEqual(rate, 48000)
            self.assertEqual(len(audio), 48000)
            self.assertAlmostEqual(float(np.max(np.abs(audio))), .8, delta=4e-5)
            self.assertGreater(metadata["gain"], 1000)

    def test_long_features_include_later_sound_instead_of_cropping_at_ten_seconds(self):
        import numpy as np
        import soundfile as sf
        from experiments.forms import extract_features

        rate = 48000
        time = np.arange(rate * 12) / rate
        audio = .1 * np.sin(2 * np.pi * np.where(time < 6, 5000, 12000) * time)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "long.wav"
            sf.write(path, audio, rate, subtype="FLOAT")
            feature, _ = extract_features(path)
        self.assertEqual(feature["duration_s"], 12)
        self.assertGreater(feature["time_s"][-1], 11.9)
        self.assertAlmostEqual(feature["centroid_hz"][10], 5000, delta=30)
        self.assertAlmostEqual(feature["centroid_hz"][-10], 12000, delta=30)

    def test_measured_features_change_numeric_geometry_with_shared_reference(self):
        import numpy as np
        from experiments.forms import parameters, mesh

        features = {"duration_s": 36, "time_s": np.array([0, 36]),
                    "centroid_hz": np.array([2000, 20000]), "rms_dbfs": np.array([-80, -20])}
        reference = {"centroid_hz": [2000, 20000], "rms_dbfs": [-80, -20]}
        short, full = parameters(features, 5, reference), parameters(features, 36, reference)
        self.assertEqual(short["rib_count"], 7)
        self.assertEqual(full["rib_count"], 48)
        self.assertGreater(max(full["mid_radius_mm"]), max(short["mid_radius_mm"]))
        self.assertGreater(max(full["rib_diameter_mm"]), max(short["rib_diameter_mm"]))
        self.assertTrue(all(12 <= r <= 20 for r in full["mid_radius_mm"]))
        self.assertTrue(all(.55 <= d <= 2.20 for d in full["rib_diameter_mm"]))
        vertices, faces = mesh(short)
        self.assertTrue(np.isfinite(vertices).all())
        self.assertLess(faces.max(), len(vertices))

    def test_resampling_preserves_pitch_duration_and_raw_amplitude(self):
        import numpy as np
        import soundfile as sf
        from experiments.audio import load_audio

        rate = 32000
        t = np.arange(rate * 2) / rate
        signal = 0.1 * np.sin(2 * np.pi * 1000 * t)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tone.wav"
            sf.write(path, np.column_stack([signal, signal]), rate, subtype="FLOAT")
            audio, metadata = load_audio(path, seconds=1)
        self.assertEqual(len(audio), 48000)
        self.assertEqual(metadata["source_channels"], 2)
        self.assertEqual(metadata["source_duration_s"], 2)
        peak_hz = np.argmax(np.abs(np.fft.rfft(audio)))
        self.assertEqual(peak_hz, 1000)
        self.assertAlmostEqual(metadata["rms"], 0.1 / np.sqrt(2), places=3)

    def test_shared_controls_are_bounded_and_constant_reference_has_midpoint(self):
        from experiments.audio import reference_controls

        controls, reference = reference_controls([-60, -40, -20])
        self.assertEqual(controls[0], 0.30)
        self.assertEqual(controls[-1], 0.55)
        self.assertAlmostEqual(controls[1], 0.425)
        self.assertEqual(reference["reference_range"], [-56.0, -24.0])
        for value in reference_controls([-20, -20])[0]:
            self.assertAlmostEqual(value, 0.425)
        for values, low, high in [([], 0.3, 0.5), ([float("nan")], 0.3, 0.5), ([-20], 0.6, 0.3)]:
            with self.assertRaises(ValueError):
                reference_controls(values, low, high)

    def test_silence_fails_instead_of_creating_arbitrary_controls(self):
        import numpy as np
        import soundfile as sf
        from experiments.audio import load_audio

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "silent.wav"
            sf.write(path, np.zeros(4800), 48000)
            with self.assertRaisesRegex(ValueError, "Silent"):
                load_audio(path)


class ProvenanceTests(unittest.TestCase):
    def test_jewelry_uses_actual_clap_winners_and_clearest_margin(self):
        from experiments.jewelry import representative_clips

        clips = [
            {"id": "ambiguous", "selected_descriptor": {"id": "clicks"}, "scores": {"clicks": .21, "whistle": .20}},
            {"id": "clear", "selected_descriptor": {"id": "clicks"}, "scores": {"clicks": .24, "whistle": .10}},
            {"id": "whistling", "selected_descriptor": {"id": "whistle"}, "scores": {"clicks": .08, "whistle": .20}},
        ]
        selected = representative_clips({"clips": clips}, {"clicks": {}, "whistle": {}, "wavering": {}})
        self.assertEqual([c["id"] for c in selected], ["clear", "whistling"])
        with self.assertRaises(ValueError):
            representative_clips({"clips": clips}, {"unknown": {}})

    def test_bold_gallery_hides_stale_forms_and_keeps_audio_in_inputs(self):
        from experiments.gallery import write_gallery

        class Parser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack = []
                self.audio_parents = []

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == "audio":
                    self.audio_parents.append(self.stack.copy())
                if tag == "div":
                    self.stack.append(attributes.get("class", ""))

            def handle_endtag(self, tag):
                if tag == "div":
                    self.stack.pop()

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_json(output / "long-forms" / "studies.json", {"clips": []})
            write_json(output / "painting" / "manifest.json", {"parameters": {"title": "Stale small edits"}})
            write_json(output / "jewelry" / "manifest.json", {
                "parameters": {"kind": "bold-jewelry", "title": "Bold jewelry", "comparison_note": "Same seed",
                    "artist_context": {"references": [], "sources": [], "name": "Livia", "summary": "Artist", "experiment_note": "Concept"}},
                "analysis": {"clips": [{"id": "clicking", "source": {"dataset": "test"},
                    "preprocessing": {"analyzed_duration_s": 1.0}, "scores": {"clicks": .3},
                    "selected_descriptor": {"text": "Clicks"}}]},
                "artifacts": [{"clip_id": "clicking", "transformation": {"title": "Terraces", "operation": "Stepped plates", "connection": "Silver"},
                    "input_image": "original.png", "reference_title": "Mitoring", "audio": "input.wav",
                    "image": "edited.png", "neutral_image": "neutral.png", "caption": "Result", "prompt": "Transform"}],
            })
            page = write_gallery(output).read_text()
            self.assertNotIn("Stale small edits", page)
            self.assertNotIn("Rib count / radius", page)
            self.assertIn("jewelry/original.png", page)
            self.assertIn("jewelry/neutral.png", page)
            parser = Parser()
            parser.feed(page)
            self.assertEqual(len(parser.audio_parents), 1)
            self.assertIn("input", parser.audio_parents[0])
            self.assertNotIn("outputs", parser.audio_parents[0])

    def test_artist_reference_roles_and_hashes_survive_portable_snapshot(self):
        from PIL import Image
        from experiments.artist import prepare_artist, snapshot_references

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "artist"
            source.mkdir()
            Image.new("RGB", (600, 300), "orange").save(source / "ring.jpg")
            (source / "pieces.md").write_text("Silver around amber.")
            profile_path = root / "profile.json"
            write_json(profile_path, {"sources": [{"root": "livia", "path": "pieces.md"}],
                "references": [{"id": "ring", "root": "livia", "path": "ring.jpg", "model_styles": ["jewelry", "pavilion"]}]})
            layout = Layout(root / "data")
            profile = prepare_artist(layout, source, source, profile_path)
            output = root / "output"
            context, images = snapshot_references(profile, output)
            reference = context["references"][0]
            self.assertEqual(reference["sha256"], digest(output / reference["display_image"]))
            self.assertEqual(reference["model_image_sha256"], digest(output / reference["model_image"]))
            self.assertEqual(images["jewelry"][0][0], "ring")
            self.assertEqual(images["pavilion"][0][1].size, (512, 512))
            self.assertNotIn("display_image", profile["references"][0])
            Path(reference["cached_path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Artist reference changed"):
                snapshot_references(profile, output)

    def test_gallery_listen_button_targets_portable_audio_and_shows_schema(self):
        from experiments.gallery import write_gallery

        class Parser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.elements = []

            def handle_starttag(self, tag, attrs):
                self.elements.append((tag, dict(attrs)))

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            experiment = output / "materials"
            (experiment / "audio").mkdir(parents=True)
            (experiment / "audio" / "input.wav").write_bytes(b"audio")
            (experiment / "result.png").write_bytes(b"image")
            write_json(experiment / "manifest.json", {
                "analysis": {"clips": [{"id": "clip", "source": {"dataset": "test", "row_index": 0},
                    "preprocessing": {"source_sample_rate": 48000, "analyzed_duration_s": 1.0},
                    "scores": {"clicks": 0.2}, "selected_descriptor": {"text": "<clicks>", "material": "paper"}}]},
                "image_model": {"id": "model"}, "parameters": {"title": "Test", "seed": 1, "steps": 4},
                "artifacts": [{"clip_id": "clip", "audio": "audio/input.wav", "image": "result.png", "caption": "Print", "prompt": "Paper"}],
            })
            page = write_gallery(output).read_text()
            parser = Parser()
            parser.feed(page)
            button = next(attrs for tag, attrs in parser.elements if tag == "button")
            audio = next(attrs for tag, attrs in parser.elements if tag == "audio")
            self.assertEqual(button["data-audio"], audio["id"])
            self.assertTrue((output / audio["src"]).exists())
            self.assertIn("Schema / transformation", page)
            self.assertIn("&lt;clicks&gt;", page)
            self.assertTrue(all(tag != "clicks" for tag, _ in parser.elements))

    def test_audio_edit_amount_uses_bounded_instruction_vocabulary(self):
        from experiments.images import edit_instruction

        descriptor = {"material": "fine threads"}
        self.assertIn("very subtle", edit_instruction(descriptor, 0.30))
        self.assertIn("subtle", edit_instruction(descriptor, 0.425))
        self.assertIn("moderate", edit_instruction(descriptor, 0.55))
        self.assertIn("fine threads", edit_instruction(descriptor, 0.30))

    def test_changed_audio_invalidates_cached_analysis(self):
        from experiments.images import load_analysis

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "recording.wav"
            source.write_bytes(b"original")
            report = root / "analysis.json"
            write_json(report, {"clips": [{"source": {"path": str(source), "sha256": digest(source)}}]})
            self.assertEqual(len(load_analysis(report)["clips"]), 1)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "changed since analysis"):
                load_analysis(report)

    def test_layout_is_created_at_requested_root(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = Layout(Path(directory))
            layout.create()
            for path in [layout.input, layout.interim, layout.output, layout.cache]:
                self.assertTrue(path.is_dir())

    def test_invalid_cli_ranges_fail_before_network(self):
        runner = CliRunner()
        for arguments in [["art", "fetch", "--per-dataset", "0"],
                          ["art", "materials", "--steps", "0"],
                          ["art", "materials", "--seed", "-1"]]:
            result = runner.invoke(app, arguments)
            self.assertEqual(result.exit_code, 2, result.output)


if __name__ == "__main__":
    unittest.main()
