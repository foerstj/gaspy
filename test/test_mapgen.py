import os
import time
import unittest

from bits import Bits
from mapgen import create_map, delete_map, create_region


class TestMapgen(unittest.TestCase):
    def test_create_map(self):
        create_map('gaspy-unit-test-map', 'GasPy UnitTest Map!')
        m = Bits().maps['gaspy-unit-test-map']
        self.assertTrue(os.path.exists(m.gas_dir.path))
        self.assertTrue(os.path.exists(os.path.join(m.gas_dir.path, 'main.gas')))

    def test_create_region(self):
        create_region('gaspy-unit-test-map', 'gaspy-unit-test-region')
        m = Bits().maps['gaspy-unit-test-map']
        self.assertIn('gaspy-unit-test-region', m.get_regions())

    def test_delete_map(self):
        m = Bits().maps['gaspy-unit-test-map']
        map_dir_path = m.gas_dir.path
        delete_map('gaspy-unit-test-map')
        time.sleep(0.1)  # shutil...
        self.assertFalse(os.path.exists(map_dir_path))


if __name__ == '__main__':
    unittest.main()
