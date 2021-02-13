import os
import sys

from gas_dir import GasDir
from map import Map


class Bits:
    def __init__(self, path=None):
        if path is None:
            path = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
        assert os.path.isdir(path)
        self.gas_dir = GasDir(path)

    def get_maps(self):
        maps_dir = self.gas_dir.get_subdir(['world', 'maps'])
        map_dirs = maps_dir.get_subdirs() if maps_dir is not None else {}
        return {name: Map(map_dir) for name, map_dir in map_dirs.items()}


def main(argv):
    path = argv[0] if len(argv) > 0 else None
    bits = Bits(path)
    maps = bits.get_maps()
    print('Maps: ' + str(len(maps)))
    for map in maps.values():
        map.print()


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
