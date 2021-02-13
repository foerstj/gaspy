import os
import sys

from gas_dir import GasDir
from gas_dir_handler import GasDirHandler
from map import Map
from templates import Templates


class Bits(GasDirHandler):
    def __init__(self, path=None):
        if path is None:
            path = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
        assert os.path.isdir(path)
        super().__init__(GasDir(path))
        self.maps = self.init_maps()
        self.templates = self.init_templates()

    def init_maps(self):
        maps_dir = self.gas_dir.get_subdir(['world', 'maps'])
        map_dirs = maps_dir.get_subdirs() if maps_dir is not None else {}
        return {name: Map(map_dir) for name, map_dir in map_dirs.items()}

    def init_templates(self):
        templates_dir = self.gas_dir.get_subdir(['world', 'contentdb', 'templates'])
        return Templates(templates_dir)


def print_maps(bits: Bits):
    maps = bits.maps
    print('Maps: ' + str(len(maps)))
    for map in maps.values():
        map.print()


def print_templates(bits: Bits):
    templates = bits.templates.get_templates()
    print('Templates: ' + str(len(templates)))
    for template in templates.values():
        template.print()


def main(argv):
    path = argv[0] if len(argv) > 0 else None
    bits = Bits(path)
    # print_maps(bits)
    print_templates(bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
