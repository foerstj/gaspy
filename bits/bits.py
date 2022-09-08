import argparse
import os
import sys

from bits.moods import Moods
from bits.snos import SNOs
from gas.gas_dir import GasDir

from .gas_dir_handler import GasDirHandler
from .map import Map
from .templates import Templates


class Bits(GasDirHandler):
    DSLOA_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
    DS1_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege', 'Bits')
    DS2_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'My Games', 'Dungeon Siege 2', 'Bits')  # I'm not sure this is correct
    DS2BW_PATH = os.path.join(os.path.expanduser("~"), 'Documents', 'My Games', 'Dungeon Siege 2', 'Bits BW')  # I'm sure this is not correct

    def __init__(self, path: str = None):
        if path is None or path.upper() == 'DSLOA':
            path = Bits.DSLOA_PATH
        elif path.upper() == 'DS1':
            path = Bits.DS1_PATH
        elif path.upper() == 'DS2':
            path = Bits.DS2_PATH
        elif path.upper() == 'DS2BW':
            path = Bits.DS2BW_PATH
        assert os.path.isdir(path), path
        super().__init__(GasDir(path))
        self.templates = self.init_templates()
        self.maps: dict[str, Map] = self.init_maps()
        self.snos = self.init_snos()
        self.moods = self.init_moods()

    def init_maps(self):
        maps_dir = self.gas_dir.get_subdir(['world', 'maps'])
        map_dirs = maps_dir.get_subdirs() if maps_dir is not None else {}
        return {name: Map(map_dir, self) for name, map_dir in map_dirs.items()}

    def init_templates(self):
        templates_dir = self.gas_dir.get_subdir(['world', 'contentdb', 'templates'])
        return Templates(templates_dir)

    def init_moods(self):
        moods_dir = self.gas_dir.get_subdir(['world', 'global', 'moods'])
        return Moods(moods_dir)

    def init_snos(self):
        snos_dir = self.gas_dir.get_subdir(['art', 'terrain'])
        return SNOs(snos_dir.path) if snos_dir is not None else None


def print_maps(bits: Bits, map_info=None, region_info=None):
    maps = bits.maps
    print('Maps: ' + str(len(maps)))
    for m in maps.values():
        m.print(map_info, region_info)


def print_templates(bits: Bits, template_info=None):
    templates = bits.templates.get_templates()
    print('Templates: ' + str(len(templates)))
    for template in templates.values():
        template.print(template_info)


def print_snos(bits: Bits):
    bits.snos.print()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Bits')
    parser.add_argument('--bits', default='DSLOA')
    parser.add_argument('--print', choices=['maps', 'templates', 'snos'])
    parser.add_argument('--print-map-info', nargs='?', choices=['npcs'])
    parser.add_argument('--print-region-info', nargs='?', choices=['actors', 'stitches', 'xp', 'plants', 'data'])
    parser.add_argument('--print-template-info', nargs='?', choices=['base', 'children'])
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits = Bits(args.bits)
    if args.print == 'maps':
        print_maps(bits, args.print_map_info, args.print_region_info)
    if args.print == 'templates':
        print_templates(bits, args.print_template_info)
    if args.print == 'snos':
        print_snos(bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
