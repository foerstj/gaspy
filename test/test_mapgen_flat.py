import unittest

from bits.bits import Bits
from mapgen.basic import create_map, delete_map
from mapgen.flat.mapgen import create_region
from test.files import Files


class TestMapgenFlat(unittest.TestCase):
    map_name = 'gaspy-unit-test-map'
    region_name = 'gaspy-unit-test-region'
    files = Files()

    def setUp(self):
        create_map(self.map_name, 'GasPy UnitTest Map!', self.files.bits_dir)

    def test_create_region(self):
        create_region(self.map_name, self.region_name, bits_path=self.files.bits_dir)
        m = Bits(self.files.bits_dir).maps[self.map_name]
        regions = m.get_regions()
        self.assertIn(self.region_name, regions)
        region = regions[self.region_name]
        self.assertIsNotNone(region.get_data().id)

    def test_create_region_with_perlin_plants(self):
        region_name = 'perlin-plants'
        create_region(self.map_name, region_name, '64x64', bits_path=self.files.bits_dir, plants='perlin')  # runs perlin_noise
        m = Bits(self.files.bits_dir).maps[self.map_name]
        regions = m.get_regions()
        self.assertIn(region_name, regions)
        region = regions[region_name]
        self.assertIsNotNone(region.get_data().id)

    def tearDown(self):
        delete_map(self.map_name, self.files.bits_dir)


if __name__ == '__main__':
    unittest.main()
