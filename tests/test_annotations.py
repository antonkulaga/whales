import unittest

from main import class_labels, contour_segments, polar_point


class AnnotationTests(unittest.TestCase):
    def test_class_ids_are_config_specific(self):
        balanced = {"_type": "ClassLabel", "names": ["NSW_1", "SW_Luna"]}
        broader = {"_type": "ClassLabel", "names": ["NSW_3", "NSW_2", "NSW_1", "SW_Dana", "SW_Luna"]}
        self.assertEqual(class_labels(balanced)["1"], "SW_Luna")
        self.assertEqual(class_labels(broader)["4"], "SW_Luna")

    def test_uncertain_points_break_lines(self):
        row = {"f0_ok": True, "f0_time": [0, .1, .2, .3],
               "f0_hz": [6000, 6500, 7000, 7500], "f0_conf": [.8, .1, .9, .9]}
        self.assertEqual(contour_segments(row, .3), [[(0, 6000)], [(.2, 7000), (.3, 7500)]])

    def test_rejected_track_is_not_rendered(self):
        self.assertEqual(contour_segments({"f0_ok": False}, .3), [])

    def test_list_feature_is_not_a_class_label(self):
        self.assertIsNone(class_labels([{"dtype": "float32", "_type": "Value"}]))

    def test_malformed_track_fails(self):
        with self.assertRaises(ValueError):
            contour_segments({"f0_ok": True, "f0_time": [0], "f0_hz": [], "f0_conf": []}, .3)

    def test_frequency_scale_is_shared(self):
        self.assertEqual(polar_point(0, 3000, 1), (.2, 0))
        self.assertEqual(polar_point(0, 22050, 2), (1, 0))


if __name__ == "__main__":
    unittest.main()
