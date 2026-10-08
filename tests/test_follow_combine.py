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

    def test_plan_accepts_eight_players_and_rejects_a_ninth(self):
        from experiments.follow_combine import plan

        self.assertEqual(self.config["combination"]["max_parts"], 8)
        parts = [{"source": "hb", "offset_s": i * 4} for i in range(8)]
        combo = plan({"parts": parts}, self.config, self.prepared())
        self.assertEqual(len(combo["parts"]), 8)
        with self.assertRaisesRegex(ValueError, "between 1 and 8 parts"):
            plan({"parts": parts + [{"source": "sp"}]}, self.config, self.prepared())

    def test_simultaneous_pairs_have_the_same_id_in_either_selection_order(self):
        from experiments.follow_combine import plan

        spec = {"parts": [{"source": "sp"}, {"source": "hb"}], "ace": {"task": "cover"}}
        combo = plan(spec, self.config, self.prepared())
        reversed_combo = plan({**spec, "parts": list(reversed(spec["parts"]))}, self.config, self.prepared())
        self.assertEqual(combo, reversed_combo)
        self.assertEqual([p["offset_s"] for p in combo["parts"]], [0.0, 0.0])
        self.assertEqual(combo["duration_s"], 20.5)
        self.assertEqual([p["index"] for p in combo["parts"]], [0, 1])

    def test_layer_order_is_ignored_but_timing_balance_and_takes_are_preserved(self):
        from experiments.follow_combine import plan

        parts = [{"source": "sp", "offset_s": 7, "gain_db": -3, "shift_octaves": -1},
                 {"source": "hb"}, {"source": "sp", "offset_s": 2, "trim_s": [3, 10]}]
        spec = {"parts": parts, "ace": {"task": "cover"}}
        combo = plan(spec, self.config, self.prepared())
        self.assertEqual(combo, plan({**spec, "parts": list(reversed(parts))}, self.config, self.prepared()))
        sp = [p for p in combo["parts"] if p["source"] == "sp"]
        self.assertEqual([(p["offset_s"], p["trim_s"], p["gain_db"], p["shift_octaves"]) for p in sp],
                         [(2.0, [3.0, 10.0], 0.0, 0), (7.0, [0.0, 12.0], -3.0, -1)])
        for change in ({"offset_s": 8}, {"gain_db": -6}, {"trim_s": [0, 10]}, {"shift_octaves": -2}):
            with self.subTest(change=change):
                changed = [{**parts[0], **change}, *parts[1:]]
                self.assertNotEqual(combo["id"], plan({**spec, "parts": changed}, self.config, self.prepared())["id"])
        self.assertNotEqual(combo["id"], plan({**spec, "ace": {"task": "cover", "seed": 7}}, self.config, self.prepared())["id"])

    def test_sequence_order_changes_the_piece(self):
        from experiments.follow_combine import plan

        spec = {"arrangement": "sequence", "parts": [{"source": "sp"}, {"source": "hb"}]}
        combo = plan(spec, self.config, self.prepared())
        self.assertEqual([p["source"] for p in combo["parts"]], ["sp", "hb"])
        self.assertEqual([p["offset_s"] for p in combo["parts"]], [0.0, 13.0])
        self.assertNotEqual(combo["id"], plan({**spec, "parts": list(reversed(spec["parts"]))}, self.config, self.prepared())["id"])

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
        self.assertEqual(combine(self.layout, self.config, {**spec, "parts": list(reversed(spec["parts"]))}, run_model=False), first)
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
        from experiments.follow_combine import RENDER_VERSION
        self.assertEqual(read_json(first)["render_version"], RENDER_VERSION)  # renders from older code are rebuilt

    def test_catalog_lists_located_sources_and_dataset_points(self):
        from experiments.data import read_json
        from experiments.follow_combine import catalog

        data = read_json(catalog(self.layout, self.config))
        self.assertEqual([s["id"] for s in data["sources"]], ["hb", "sp"])
        self.assertEqual(data["sources"][1]["location"]["precision"], "approximate")
        self.assertGreater(len(data["points"]), 100)
        self.assertTrue((self.layout.output / "follow" / data["countries"]).exists())
        self.assertTrue((self.layout.output / "follow" / data["sources"][0]["files"]["animal"]["audio"]).exists())

    def test_duo_batch_loads_the_model_once_and_reuses_finished_pairs(self):
        from unittest.mock import patch

        from experiments.data import read_json, write_json
        from experiments.follow_precompute import precompute_duos

        prepared_path = self.layout.interim / "follow" / "prepared.json"
        prepared = read_json(prepared_path)
        prepared["sources"].append({**prepared["sources"][0], "id": "hb2"})
        write_json(prepared_path, prepared)
        self.config["sources"].append({**self.config["sources"][0], "id": "hb2"})

        def fake_ace(layout, config, jobs, jobs_path, results_path, ace_root, offload):
            results = {"jobs": {}, "model_load_s": 0}
            for job in jobs:
                shutil.copyfile(job["src_audio"], job["output"])
                results["jobs"][job["id"]] = {**job, "seconds": 0}
            write_json(results_path, results)
            return results

        with patch("experiments.follow_precompute.run_ace", side_effect=fake_ace) as model:
            index = read_json(precompute_duos(self.layout, self.config))
            self.assertEqual(len(index["pieces"]), 3)
            model.assert_called_once()
            self.assertEqual(len(model.call_args.args[2]), 3)
            for piece in index["pieces"]:
                manifest = read_json(self.layout.output / "follow" / "combos" / piece["id"] / "manifest.json")
                self.assertIn("ace", manifest["stems"])
                self.assertEqual([p["offset_s"] for p in manifest["parts"]], [0.0, 0.0])
            self.assertEqual(read_json(precompute_duos(self.layout, self.config))["pieces"], index["pieces"])
            model.assert_called_once()  # a rerun does not load ACE-Step

    def test_duo_batch_restores_a_job_completed_before_an_interruption(self):
        from unittest.mock import patch

        from experiments.data import write_json
        from experiments.follow_combine import ace_job, combine, plan
        from experiments.follow_precompute import duo_specs, precompute_duos

        spec = duo_specs(self.config, self.prepared())[0]
        combo = plan(spec, self.config, self.prepared())
        path = combine(self.layout, self.config, spec, run_model=False)
        job = ace_job(combo, self.config, path.parent)
        shutil.copyfile(job["src_audio"], job["output"])
        write_json(self.layout.interim / "follow" / "duos-ace-results.json", {"jobs": {job["id"]: {**job, "seconds": 0}}})
        with patch("experiments.follow_precompute.run_ace") as model:
            precompute_duos(self.layout, self.config)
            model.assert_not_called()
        self.assertTrue((path.parent / "ace-results.json").exists())


if __name__ == "__main__":
    unittest.main()
