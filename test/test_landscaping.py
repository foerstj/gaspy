import unittest
from argparse import Namespace

from landscaping import ruinate
from test.files import Files


class TestMap(unittest.TestCase):
    def setUp(self):
        self.files = Files()

    def test_ruinate(self):
        self.files.copy_map_region('map_world', 'path2crypts')  # map_world has no world-level sub-folders; path2crypts has both signs and torches
        ruinate.ruinate(self.files.bits_dir, 'map_world', 'path2crypts', Namespace(signs='remove', torches='extinguish'))
        self.files.cleanup_map('map_world')
        # just happy if it doesn't crash tbh
