import os
import time
import unittest

from bits import Bits
from gas_dir import GasDir
from map import Map


class TestMap(unittest.TestCase):
    def test_koe(self):
        bits = Bits()
        map_dir = bits.gas_dir.get_subdir('world').get_subdir('maps').get_subdir('map_world')
        m = Map(map_dir, bits)
        self.assertIsInstance(m, Map)
        self.assertEqual(map_dir, m.gas_dir)
        self.assertEqual('"Kingdom of Ehb"', m.get_screen_name())
        self.assertEqual(81, len(m.get_regions()))

    def test_init_new(self):
        bits = Bits()
        map_dir_path = os.path.join(bits.gas_dir.path, 'world', 'maps', 'gaspy-unit-test-map')
        self.assertFalse(os.path.exists(map_dir_path))
        m = Map(GasDir(map_dir_path), bits)
        self.assertIsInstance(m, Map)

    def test_save_and_delete(self):
        bits = Bits()
        map_dir_path = os.path.join(bits.gas_dir.path, 'world', 'maps', 'gaspy-unit-test-map')
        self.assertFalse(os.path.exists(map_dir_path))
        m = Map(GasDir(map_dir_path), bits)
        m.save()
        self.assertTrue(os.path.exists(map_dir_path))
        m.delete()
        time.sleep(0.1)  # shutil...
        self.assertFalse(os.path.exists(map_dir_path))
