import unittest

from bits.bits import Bits
from mapgen.basic import create_map, delete_map
from mapgen.flat.mapgen import create_region


class TestMapgen(unittest.TestCase):
    map_name = 'gaspy-unit-test-map'
    region_name = 'gaspy-unit-test-region'

    def setUp(self):
        create_map(self.map_name, 'GasPy UnitTest Map!')

    def test_1_create_region(self):
        create_region(self.map_name, self.region_name)
        m = Bits().maps[self.map_name]
        regions = m.get_regions()
        self.assertIn(self.region_name, regions)
        region = regions[self.region_name]
        self.assertIsNotNone(region.get_data().id)

    def tearDown(self):
        delete_map(self.map_name)


if __name__ == '__main__':
    unittest.main()
