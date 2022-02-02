import os
import unittest

from bits.bits import Bits
from bits.map import Region, Map
from mapgen.flat.mapgen import create_map, delete_map, create_region, delete_region


class TestMapgen(unittest.TestCase):
    map_name = 'gaspy-unit-test-map'
    region_name = 'gaspy-unit-test-region'

    def test_1_create_map(self):
        create_map(self.map_name, 'GasPy UnitTest Map!')
        m = Bits().maps[self.map_name]
        self.assertTrue(os.path.exists(m.gas_dir.path))
        self.assertTrue(os.path.exists(os.path.join(m.gas_dir.path, 'main.gas')))

    def test_2_create_region(self):
        create_region(self.map_name, self.region_name)
        m = Bits().maps[self.map_name]
        regions = m.get_regions()
        self.assertIn(self.region_name, regions)
        region = regions[self.region_name]
        self.assertIsNotNone(region.get_data().id)

    def test_3_delete_region(self):
        region: Region = Bits().maps[self.map_name].get_region(self.region_name)
        region_dir_path = region.gas_dir.path
        delete_region(self.map_name, self.region_name)
        self.assertFalse(os.path.exists(region_dir_path))

    def test_4_delete_map(self):
        m: Map = Bits().maps[self.map_name]
        map_dir_path = m.gas_dir.path
        delete_map(self.map_name)
        self.assertFalse(os.path.exists(map_dir_path))


if __name__ == '__main__':
    unittest.main()
