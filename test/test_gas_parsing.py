import os
import unittest

from gas_file import GasFile


class MyTestCase(unittest.TestCase):
    bits_dir = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
    assert os.path.isdir(bits_dir)

    def test_map_world_main(self):
        map_world_main_file = os.path.join(self.bits_dir, 'world', 'maps', 'map_world', 'main.gas')
        gas_file = GasFile(map_world_main_file)
        self.assertEqual(1, len(gas_file.gas.items))
        section = gas_file.gas.items[0]
        self.assertEqual('t:map,n:map', section.header)
        self.assertEqual(11, len(section.items))


if __name__ == '__main__':
    unittest.main()
