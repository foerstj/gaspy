import math
import unittest

from bits.maps.decals_gas import Decal


class TestDecalsGas(unittest.TestCase):
    def assertListsAlmostEqual(self, a: list[float], b: list[float]):
        self.assertEqual(len(a), len(b))
        for i in range(len(a)):
            self.assertAlmostEqual(a[i], b[i], msg=f'i={i}')

    def test_decal_rad_to_decal_orientation(self):
        self.assertListsAlmostEqual(Decal.rad_to_decal_orientation(0.00 * math.tau), [ 0.0, -1.0, 0.0, 0.0, 0.0, -1.0,  1.0,  0.0, 0.0])
        self.assertListsAlmostEqual(Decal.rad_to_decal_orientation(0.25 * math.tau), [ 1.0,  0.0, 0.0, 0.0, 0.0, -1.0,  0.0,  1.0, 0.0])
        self.assertListsAlmostEqual(Decal.rad_to_decal_orientation(0.50 * math.tau), [ 0.0,  1.0, 0.0, 0.0, 0.0, -1.0, -1.0,  0.0, 0.0])
        self.assertListsAlmostEqual(Decal.rad_to_decal_orientation(0.75 * math.tau), [-1.0,  0.0, 0.0, 0.0, 0.0, -1.0,  0.0, -1.0, 0.0])
