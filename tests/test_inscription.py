import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("torch") and importlib.util.find_spec("scipy"), "Run with uv run --group art")
class InscriptionTests(unittest.TestCase):
    def clip(self, rising=True):
        import numpy as np
        from experiments.inscription import Clip, RATE, tone

        times = np.linspace(0.1, 0.7, 120)
        freqs = np.linspace(6_000, 14_000, 120) if rising else np.linspace(14_000, 6_000, 120)
        audio = tone(times, freqs, 0.8) + 0.001 * np.random.default_rng(0).standard_normal(round(0.8 * RATE))
        return Clip(id="t", split="test", label=0, name="SW_test", session="s", audio=audio.astype("float32"), duration=0.8,
                    f0_time=times, f0_hz=freqs, f0_conf=np.ones_like(times), f0_ok=True)

    def test_contour_bits_and_decoded_pitch(self):
        import numpy as np
        from experiments.inscription import PLACEMENT_BITS, RATE, decode_contour, encode_contour

        clip = self.clip()
        payload = encode_contour(clip, 32, 8)
        self.assertEqual(payload["bits"], 32 * 8 + PLACEMENT_BITS)
        audio = decode_contour(payload, clip.duration)
        self.assertEqual(len(audio), round(clip.duration * RATE))
        # Zero crossings in the middle of the whistle give the decoded frequency.
        middle = audio[round(0.39 * RATE):round(0.41 * RATE)]
        crossings = np.sum(np.diff(np.signbit(middle).astype(int)) != 0) / 2 / 0.02
        self.assertAlmostEqual(crossings, 10_000, delta=400)
        reversed_audio = decode_contour(payload, clip.duration, reverse=True)
        start = reversed_audio[round(0.11 * RATE):round(0.13 * RATE)]
        self.assertGreater(np.sum(np.diff(np.signbit(start).astype(int)) != 0) / 2 / 0.02, 12_000)

    def test_groove_round_trip_recovers_contour_after_casting_blur(self):
        import numpy as np
        from experiments.inscription import Band, cast_and_scan, contour, engrave, read_groove

        clip, band = self.clip(), Band()
        times, freqs = contour(clip)
        depth, geometry = engrave(times, freqs, band)
        self.assertAlmostEqual(depth.max(), band.groove_depth, places=3)
        _, read_t, read_f = read_groove(cast_and_scan(depth, 0.1, band), geometry, band, clip.duration)
        expected = np.interp(read_t, times, freqs)
        self.assertLess(np.median(np.abs(np.log2(read_f / expected))), 0.02)
        self.assertAlmostEqual(read_t[0], times[0], delta=0.01)
        self.assertAlmostEqual(read_t[-1], times[-1], delta=0.01)

    def test_band_mesh_is_watertight(self):
        from collections import Counter
        from experiments.inscription import Band, cast_and_scan, contour, engrave, ring_mesh

        clip, band = self.clip(), Band()
        depth, _ = engrave(*contour(clip), band)
        vertices, faces = ring_mesh(cast_and_scan(depth, 0.1, band), band, step=0.2)
        edges = Counter(tuple(sorted(edge)) for face in faces.tolist() for edge in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])))
        self.assertTrue(all(count == 2 for count in edges.values()))
        # Simulated surface roughness (0.005 mm RMS) may sit slightly proud of the nominal radius.
        self.assertAlmostEqual(abs(vertices[:, :2]).max(), band.outer_radius, delta=0.03)

    def test_capacity_shrinks_with_blur_and_respects_casting_floor(self):
        from experiments.inscription import BLURS_MM, Band, digital_capacity

        band = Band()
        capacities = [digital_capacity(blur, band) for blur in BLURS_MM]
        self.assertTrue(all(c["pitch_mm"] >= 0.35 for c in capacities))
        self.assertEqual([c["payload_bits"] for c in capacities], sorted((c["payload_bits"] for c in capacities), reverse=True))

    def test_relief_and_amplitude_bits(self):
        from experiments.inscription import amplitude_only, relief

        clip = self.clip()
        audio, bits = relief(clip, 8, 8, 2)
        self.assertEqual(bits, 8 * 8 * 2 + 16)
        self.assertEqual(len(audio), len(clip.audio))
        audio, bits = amplitude_only(clip, 32)
        self.assertEqual(bits, 32 * 3 + 16)
        self.assertEqual(len(audio), len(clip.audio))


if __name__ == "__main__":
    unittest.main()
