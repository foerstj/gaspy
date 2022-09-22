import os
import unittest

from bits.bits import Bits
from gas.gas_dir import GasDir
from bits.map import Map


class TestMap(unittest.TestCase):
    extracts_dir = os.path.join('files', 'extracts')
    assert os.path.isdir(extracts_dir)
    maps_bits_dir = os.path.join(extracts_dir, 'Maps')
    assert os.path.isdir(maps_bits_dir)

    bits_dir = os.path.join('files', 'Bits')
    assert os.path.isdir(bits_dir)

    def test_koe(self):
        bits = Bits(self.maps_bits_dir)
        map_dir = bits.gas_dir.get_subdir('world').get_subdir('maps').get_subdir('map_world')
        m = Map(map_dir, bits)
        self.assertIsInstance(m, Map)
        self.assertEqual(map_dir, m.gas_dir)
        self.assertEqual('"Kingdom of Ehb"', m.get_data().screen_name)
        self.assertEqual(81, len(m.get_regions()))

    def test_init_new(self):
        bits = Bits(self.bits_dir)
        map_dir_path = os.path.join(bits.gas_dir.path, 'world', 'maps', 'gaspy-unit-test-map')
        self.assertFalse(os.path.exists(map_dir_path))
        m = Map(GasDir(map_dir_path), bits)
        self.assertIsInstance(m, Map)

    def test_save_and_delete(self):
        bits = Bits(self.bits_dir)
        map_dir_path = os.path.join(bits.gas_dir.path, 'world', 'maps', 'gaspy-unit-test-map')
        self.assertFalse(os.path.exists(map_dir_path))
        m = Map(GasDir(map_dir_path), bits, Map.Data(name='gaspy-unit-test-map', screen_name='GasPy UnitTest Map!'))
        m.save()
        self.assertTrue(os.path.exists(map_dir_path))
        self.assertTrue(os.path.exists(os.path.join(map_dir_path, 'main.gas')))
        m.delete()
        self.assertFalse(os.path.exists(map_dir_path))
