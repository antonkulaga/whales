import importlib.util
import math
import unittest

MESH = all(importlib.util.find_spec(name) for name in ("trimesh", "scipy", "embreex"))


@unittest.skipUnless(MESH, "Run with uv run --group art --group mesh")
class SilverTests(unittest.TestCase):
    def setUp(self):
        import trimesh

        from experiments.silver import load_config, ring_frame

        self.config = load_config()
        # A plain band: 9 mm to the tube centre, 1.2 mm tube radius, finger axis along z.
        self.mesh = trimesh.creation.torus(major_radius=9.0, minor_radius=1.2, major_sections=96, minor_sections=24)
        self.frame = ring_frame(self.mesh, self.config)

    def feature(self, pitch, level, slope, duration=1.0, hop=0.005):
        times = [i * hop for i in range(round(duration / hop))]
        return {"time_s": times, "duration_s": duration, "hop_s": hop,
                "pitch": [pitch(t) for t in times], "level": [level(t) for t in times], "slope": [slope(t) for t in times]}

    def test_frame_finds_axis_bore_and_closed_ring(self):
        import numpy as np

        self.assertAlmostEqual(abs(self.frame["axis"][2]), 1.0, places=3)
        self.assertAlmostEqual(float(np.nanmedian(self.frame["bore_raw"])), 7.8, delta=0.1)
        self.assertAlmostEqual(self.frame["span"], 2 * math.pi)

    def test_profile_reaches_a_held_value(self):
        from experiments.silver import profiles

        held = profiles(self.feature(lambda t: 0.5, lambda t: 1.0, lambda t: 0.0), self.frame, self.config)
        self.assertAlmostEqual(float(held["lift"].min()), 0.5, places=3)
        self.assertAlmostEqual(float(held["swell"].max()), 1.0, places=3)
        partial = profiles(self.feature(lambda t: 0.5, lambda t: 1.0, lambda t: 0.0), self.frame, self.config, until_s=0.25)
        self.assertLess(float(partial["lift"].min()), 0.01)  # the part of the ring the sound has not reached yet

    def test_bend_keeps_angle_and_bore_and_order(self):
        import numpy as np

        from experiments.silver import cylindrical, deform, profiles

        profile = profiles(self.feature(lambda t: math.sin(6 * t), lambda t: t, lambda t: math.cos(9 * t)), self.frame, self.config)
        vertices = np.asarray(self.mesh.vertices)
        moved = deform(vertices, self.frame, profile, 3.0, self.config)
        r0, theta0, _ = cylindrical(vertices, self.frame)
        r1, theta1, _ = cylindrical(moved, self.frame)
        turn = np.angle(np.exp(1j * (theta1 - theta0)))
        self.assertLess(float(np.abs(turn).max()), 1e-9)
        self.assertTrue(np.all(r1 >= r0 - 1e-9))  # nothing moves toward the finger
        inner = r0 <= r0.min() + 1e-6
        self.assertLess(float(np.abs(r1[inner] - r0[inner]).max()), 1e-9)
        self.assertGreater(float(np.abs(moved - vertices).max()), 1.0)
        # Along one radial line, order is kept: no two points can swap or meet.
        line = np.array([[r, 0.0, 0.3] for r in np.linspace(7.8, 10.2, 40)]) + self.frame["center"]
        r_line, _, _ = cylindrical(deform(line, self.frame, profile, 3.0, self.config), self.frame)
        self.assertTrue(np.all(np.diff(r_line) > 0))

    def test_casting_check_passes_the_bend_and_fails_the_naive_push(self):
        import numpy as np

        from experiments.silver import baseline, check, deform, naive, profiles

        profile = profiles(self.feature(lambda t: -1.0, lambda t: 0.2, lambda t: 0.0), self.frame, self.config)
        base = baseline(self.mesh, self.frame, self.config)
        bent, _ = check(self.mesh, deform(self.mesh.vertices, self.frame, profile, 1.0, self.config), self.frame, base, self.config)
        self.assertTrue(bent["casts"], bent)
        self.assertLess(bent["bore_change_mm"], 1e-3)  # finger hole kept to a micrometre
        # Pitch below the median pushes inward along the normal: the 2.4 mm tube erodes away.
        pushed = naive(np.asarray(self.mesh.vertices), np.asarray(self.mesh.vertex_normals), self.frame, profile, 1.0, self.config)
        eroded, _ = check(self.mesh, pushed, self.frame, base, self.config)
        self.assertFalse(eroded["casts"])
        self.assertLess(eroded["min_wall_mm"], self.config["casting"]["min_wall_mm"])

    def test_page_template_has_data_slot_and_command_exists(self):
        from typer.testing import CliRunner

        from experiments.silver import PAGE
        from main import app

        self.assertIn('<script id="silver-data" type="application/json">/*SILVER_DATA*/null</script>', PAGE.read_text())
        result = CliRunner().invoke(app, ["art", "silver", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("stoneless rings", result.output)


    def test_motion_page_has_data_slot_and_five_studies(self):
        from experiments.silver_motion import PAGE

        page = PAGE.read_text()
        self.assertIn('<script id="motion-data" type="application/json">/*MOTION_DATA*/null</script>', page)
        for study in ("cast", "ferro", "nitinol", "fins", "memory"):
            self.assertIn(f'id: "{study}"', page)


if __name__ == "__main__":
    unittest.main()
