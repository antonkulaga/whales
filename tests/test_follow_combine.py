import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ART = all(importlib.util.find_spec(name) for name in ("numpy", "scipy", "soundfile", "matplotlib", "PIL")) and shutil.which("ffmpeg")
RATE = 48000


def tonal(start, end, hz, label="moan"):
    return {"kind": "tonal", "start_s": start, "end_s": end, "time_s": [start, end], "hz": [hz, hz * 1.3], "label": label, "origin": "test"}


@unittest.skipUnless(ART, "Run with uv run --group art --group viz (needs ffmpeg)")
class CombineTests(unittest.TestCase):
    def setUp(self):
        import numpy as np
        import soundfile as sf

        from experiments.data import Layout, write_json
        from experiments.follow import load_config, onsets

        self.folder = tempfile.TemporaryDirectory()
        self.layout = Layout(Path(self.folder.name))
        self.config = load_config()
        locations = {"humpback": {"label": "Test Strait", "lon": -123.0, "lat": 48.5, "precision": "published"},
                     "sperm whale": {"label": "Test Island", "lon": -61.4, "lat": 15.3, "precision": "approximate"}}
        self.config["sources"] = [{"id": "hb", "species": "humpback", "location": locations["humpback"]},
                                  {"id": "sp", "species": "sperm whale", "location": locations["sperm whale"]}]
        rng = np.random.default_rng(5)
        hb = [tonal(s, s + .8, 300 + 40 * i) for i, s in enumerate([1.0, 3.5, 6.2, 9.0, 12.4, 15.1, 18.3])]
        sp = [{"kind": "click", "time_s": round(c + k * .12, 3), "group": g, "origin": "test"}
              for g, c in enumerate([.8, 4.1, 7.7, 10.2]) for k in range(4)]
        sources = []
        for sid, species, events, duration in (("hb", "humpback", hb, 20.0), ("sp", "sperm whale", sp, 12.0)):
            folder = self.layout.output / "follow" / sid
            folder.mkdir(parents=True)
            for stem in ("animal", "guide"):
                sf.write(folder / f"{stem}.wav", .1 * rng.normal(size=round(duration * RATE)), RATE)
            sources.append({"id": sid, "species": species, "title": sid, "note": "synthetic", "duration_s": duration,
                            "events": events, "onsets_s": onsets(events), "register_shift_octaves": 0,
                            "stems": {"animal": f"{sid}/animal.wav", "guide": f"{sid}/guide.wav"}})
        write_json(self.layout.interim / "follow" / "prepared.json", {"sources": sources})
        self.config["config_sha256"] = "test"

    def tearDown(self):
        self.folder.cleanup()

    def prepared(self):
        from experiments.follow_combine import prepared_sources

        return prepared_sources(self.layout)

    def test_plan_places_sequences_and_hashes_the_result(self):
        from experiments.follow_combine import plan

        spec = {"arrangement": "sequence", "gap_s": 2, "parts": [{"source": "hb", "trim_s": [0, 10]}, {"source": "sp"}]}
        combo = plan(spec, self.config, self.prepared())
        self.assertEqual([p["offset_s"] for p in combo["parts"]], [0.0, 12.0])
        self.assertEqual(combo["duration_s"], 24.5)
        self.assertEqual(combo["title"], "hb + sp")
        self.assertEqual(plan(spec, self.config, self.prepared())["id"], combo["id"])
        moved = plan({**spec, "gap_s": 3}, self.config, self.prepared())
        self.assertNotEqual(moved["id"], combo["id"])

    def test_plan_rejects_what_cannot_be_rendered(self):
        from experiments.follow_combine import plan

        bad = [
            {"parts": []},
            {"parts": [{"source": "nope"}]},
            {"arrangement": "shuffle", "parts": [{"source": "hb"}]},
            {"parts": [{"source": "hb", "gain_db": 12}]},
            {"parts": [{"source": "hb", "trim_s": [5, 5.5]}]},
            {"parts": [{"source": "hb", "offset_s": 400}]},
            {"parts": [{"source": "hb", "offset_s": float("nan")}]},
            {"parts": [{"source": "hb"}], "ace": {"task": "remix"}},
        ]
        for spec in bad:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                plan(spec, self.config, self.prepared())

    def test_placed_moves_events_and_drops_those_cut_by_the_trim(self):
        from experiments.follow_combine import placed

        events = [tonal(1.0, 2.0, 300), tonal(4.5, 5.5, 300), {"kind": "click", "time_s": 6.0, "group": 0}]
        moved = placed(events, [2.0, 7.0], 10.0)
        self.assertEqual(len(moved), 2)
        self.assertEqual(moved[0]["start_s"], 12.5)
        self.assertEqual(moved[0]["time_s"], [12.5, 13.5])
        self.assertEqual(moved[1]["time_s"], 14.0)

    def test_layered_combination_scores_each_part_and_keeps_levels_unclipped(self):
        import soundfile as sf

        from experiments.data import read_json
        from experiments.follow_combine import combine

        spec = {"title": "Two seas", "arrangement": "layer",
                "parts": [{"source": "hb"}, {"source": "sp", "offset_s": 3, "gain_db": -3}], "ace": {"task": "cover"}}
        path = combine(self.layout, self.config, spec, run_model=False)
        manifest = read_json(path)
        self.assertEqual(manifest["title"], "Two seas")
        self.assertEqual(set(manifest["stems"]), {"animal", "guide", "response"})  # no ACE without the model
        self.assertLessEqual(manifest["scale"], 1.0)
        for stem in manifest["stems"].values():
            self.assertTrue((self.layout.output / "follow" / stem["audio"]).exists())
            self.assertTrue((self.layout.output / "follow" / stem["image"]).exists())
        audio, rate = sf.read(path.parent / "guide.wav")
        self.assertEqual(rate, RATE)
        self.assertAlmostEqual(len(audio) / rate, manifest["duration_s"], places=2)
        self.assertLess(abs(audio).max(), .95)
        sp = manifest["parts"][1]
        self.assertEqual(sp["onsets_s"][0], round(.8 + 3, 4))
        self.assertEqual(sp["location"]["label"], "Test Island")
        response = manifest["scores"]["response"]
        self.assertTrue(all(part["z"] >= 3 for part in response["parts"]), response["parts"])
        self.assertTrue((self.layout.output / "follow" / sp["files"]["guide"]).exists())

    def test_repeated_combination_reuses_the_saved_render(self):
        from experiments.data import read_json
        from experiments.follow_combine import combine

        spec = {"arrangement": "layer", "parts": [{"source": "hb"}, {"source": "sp", "offset_s": 2}]}
        first = combine(self.layout, self.config, spec, run_model=False)
        manifest = read_json(first)
        guide = first.parent / "guide.wav"
        stamp = guide.stat().st_mtime_ns
        self.assertEqual(combine(self.layout, self.config, spec, run_model=False), first)
        self.assertEqual(guide.stat().st_mtime_ns, stamp)  # nothing was rendered again
        self.assertEqual(read_json(first)["created_at_utc"], manifest["created_at_utc"])
        missing = self.layout.output / "follow" / manifest["stems"]["response"]["audio"]
        missing.unlink()
        combine(self.layout, self.config, spec, run_model=False)
        self.assertTrue(missing.exists())  # an incomplete render is rebuilt
        combine(self.layout, self.config, spec, run_model=False, reuse=False)
        self.assertNotEqual(guide.stat().st_mtime_ns, stamp)  # --rerender rebuilds on request
        stale = read_json(first) | {"render_version": 0}
        from experiments.data import write_json
        write_json(first, stale)
        combine(self.layout, self.config, spec, run_model=False)
        self.assertEqual(read_json(first)["render_version"], 1)  # renders from older code are rebuilt

    def test_catalog_lists_located_sources_and_dataset_points(self):
        from experiments.data import read_json
        from experiments.follow_combine import catalog

        data = read_json(catalog(self.layout, self.config))
        self.assertEqual([s["id"] for s in data["sources"]], ["hb", "sp"])
        self.assertEqual(data["sources"][1]["location"]["precision"], "approximate")
        self.assertGreater(len(data["points"]), 100)
        self.assertTrue((self.layout.output / "follow" / data["countries"]).exists())
        self.assertTrue((self.layout.output / "follow" / data["sources"][0]["files"]["animal"]["audio"]).exists())


if __name__ == "__main__":
    unittest.main()
