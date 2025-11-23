import argparse

import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.map import Map
from bits.maps.region import Region


def parse_model_name(model: str):
    m, c, category, base_model, pos, sub_model = model.split('_')
    assert m == 'm' and c == 'c' and pos == 'pos'
    base_model_pretty = {
        'fb': 'Farmboy',
        'fg': 'Farmgirl',
        'pmo': 'Peasant Male Old',
        'fy': 'Fairy',
        'bk': 'Blacksmith',
        'kg': 'King',
        'df': 'Dwarf',
        'dg': 'Droog',
        'ft': 'Fortuneteller',
        'ja': 'Jeriah',
    }[base_model]
    return base_model, sub_model, base_model_pretty


def printout_npc(npc: GameObject):
    template_name = npc.template_name
    screen_name = npc.compute_value('common', 'screen_name').strip('"')
    model = npc.compute_value('aspect', 'model')
    texture = npc.get_template().compute_value('aspect', 'textures', '0')
    base_model, sub_model, base_model_pretty = parse_model_name(model)
    print(f'{template_name} "{screen_name}" - {model} {texture} - {base_model_pretty}')


def printout_region_npcs(region: Region):
    npcs = region.get_npcs()
    if len(npcs) > 0:
        print(f'{region.get_name()}:')
    for npc in npcs:
        printout_npc(npc)


def printout_map_npcs(m: Map):
    for region in m.get_regions().values():
        printout_region_npcs(region)


def printout_npcs(map_name: str, bits_path: str):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    print(map_name)
    printout_map_npcs(m)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printout npcs')
    parser.add_argument('map')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    printout_npcs(args.map, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
