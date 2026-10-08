import unittest

from experiments.follow_precompute import duo_specs


class DuoSelectionTests(unittest.TestCase):
    def test_twenty_selectable_recordings_make_190_unordered_pairs(self):
        config = {"sources": [{"id": str(i)} for i in range(20)] + [{"id": "study-only", "map": False}]}
        specs = duo_specs(config, {str(i): {} for i in range(20)})
        self.assertEqual(len(specs), 190)
        pairs = {tuple(p["source"] for p in spec["parts"]) for spec in specs}
        self.assertEqual(len(pairs), 190)
        self.assertTrue(all(a != b for a, b in pairs))
        self.assertTrue(all([p["offset_s"] for p in spec["parts"]] == [0, 0] for spec in specs))

    def test_missing_sources_are_reported_before_any_rendering(self):
        config = {"sources": [{"id": "a"}, {"id": "b"}]}
        with self.assertRaisesRegex(ValueError, "Unprepared sources: b"):
            duo_specs(config, {"a": {}})
        with self.assertRaisesRegex(ValueError, "Unknown map sources: c"):
            duo_specs(config, {"a": {}, "b": {}}, ["a", "c"])
        with self.assertRaisesRegex(ValueError, "at least two"):
            duo_specs(config, {"a": {}, "b": {}}, ["a"])


if __name__ == "__main__":
    unittest.main()
