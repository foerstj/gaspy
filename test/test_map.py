import os
import unittest

from bits.bits import Bits
from gas.gas_dir import GasDir
from bits.maps.map import Map
from test.files import Files


class TestMap(unittest.TestCase):
    def setUp(self):
        self.files = Files()

    def test_koe(self):
        bits = Bits(self.files.maps_bits_dir)
        map_dir = bits.gas_dir.get_subdir('world').get_subdir('maps').get_subdir('map_world')
        m = Map(map_dir, bits)
        self.assertIsInstance(m, Map)
        self.assertEqual(map_dir, m.gas_dir)
        self.assertEqual('"Kingdom of Ehb"', m.get_data().screen_name)
        self.assertEqual(81, len(m.get_regions()))

    def test_init_new(self):
        bits = Bits(self.files.bits_dir)
        map_dir_path = os.path.join(bits.gas_dir.path, 'world', 'maps', 'gaspy-unit-test-map')
        self.assertFalse(os.path.exists(map_dir_path))
        m = Map(GasDir(map_dir_path), bits)
        self.assertIsInstance(m, Map)

    def test_save_and_delete(self):
        bits = Bits(self.files.bits_dir)
        map_dir_path = os.path.join(bits.gas_dir.path, 'world', 'maps', 'gaspy-unit-test-map')
        self.assertFalse(os.path.exists(map_dir_path))
        m = Map(GasDir(map_dir_path), bits, Map.Data(screen_name='GasPy UnitTest Map!', description='gaspy-unit-test-map'))
        m.save()
        self.assertTrue(os.path.exists(map_dir_path))
        self.assertTrue(os.path.exists(os.path.join(map_dir_path, 'main.gas')))
        m.delete()
        self.assertFalse(os.path.exists(map_dir_path))
