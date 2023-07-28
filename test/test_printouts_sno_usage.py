import unittest

from printouts import sno_usage
from test.files import Files


class TestPrintoutsSnoUsage(unittest.TestCase):
    def setUp(self):
        self.files = Files()

    def test_bounds_camera(self):
        self.files.copy_extracts(self.files.terrain_bits_dir, 'world', 'global', 'siege_nodes')
        self.files.copy_map_region('map_world', 'fh_r1')
        self.files.copy_map_region('multiplayer_world', 'town_center')

        sno_usage.sno_usage('bounds-camera', ['map_world', 'multiplayer_world'], True, self.files.bits_dir, self.files.terrain_bits_dir)

        self.files.cleanup_map('map_world')
        self.files.cleanup_map('multiplayer_world')
        self.files.cleanup_copied_extracts('world', 'global', 'siege_nodes')
        # just happy if it doesn't crash tbh
