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


def get_gender(base_model, texture):
    gender = {
        'fb': 'male',
        'fg': 'female',
        'pmo': None,
        'fy': 'female',
        'bk': 'male',
        'kg': 'male',
        'df': 'male',
        'dg': 'male',
        'ft': 'female',
        'ja': 'male',
    }[base_model]
    if base_model == 'pmo':
        gender = 'female' if texture == 'b_c_gbn_pmo-05' else 'male'  # b_c_gbn_pmo-05 = Verma
    return gender


def get_race(base_model):
    race = {
        'fb': 'Human',
        'fg': 'Human',
        'pmo': 'Human',
        'fy': 'Fairy',
        'bk': 'Human',
        'kg': 'Human',
        'df': 'Dwarf',
        'dg': 'Droog',
        'ft': 'Human',
        'ja': 'Human',
    }[base_model]
    return race


def printout_npc(npc: GameObject, with_convos=False):
    template_name = npc.template_name
    screen_name = npc.compute_value('common', 'screen_name').strip('"')
    model = npc.compute_value('aspect', 'model')
    texture = npc.get_template().compute_value('aspect', 'textures', '0')
    base_model, sub_model, base_model_pretty = parse_model_name(model)
    gender = get_gender(base_model, texture)
    race = get_race(base_model)
    convos_str = ''
    if with_convos:
        convo_attrs = npc.section.get_section('conversation').get_section('conversations').get_attrs()
        convo_names = [a.value for a in convo_attrs]
        convos_str = ' - ' + ', '.join(convo_names)
    print(f'{template_name} "{screen_name}" - {model} {texture} - {base_model_pretty} - {race} {gender}' + convos_str)


def has_convos(npc: GameObject):
    return npc.section.get_section('conversation') is not None


def printout_region_npcs(region: Region, with_convos=False):
    npcs = region.get_npcs()
    if with_convos:
        npcs = [npc for npc in npcs if has_convos(npc)]
    if len(npcs) > 0:
        print(f'{region.get_name()}:')
    for npc in npcs:
        printout_npc(npc, with_convos)


def printout_map_npcs(m: Map, with_convos=False):
    for region in m.get_regions().values():
        printout_region_npcs(region, with_convos)


def printout_npcs(map_name: str, bits_path: str, with_convos=False):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    print(map_name)
    printout_map_npcs(m, with_convos)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printout npcs')
    parser.add_argument('map')
    parser.add_argument('--with-convos', action='store_true')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    printout_npcs(args.map, args.bits, args.with_convos)


if __name__ == '__main__':
    main(sys.argv[1:])
