import argparse

import sys

from bits.bits import Bits
from bits.maps.conversations_gas import ConversationItem
from bits.maps.game_object import GameObject
from bits.maps.map import Map
from bits.maps.region import Region
from gas.gas_parser import GasParser


def parse_model_name(model: str):
    assert model.startswith('m_c_')
    model = model[4:]
    category, model = model.split('_', 1)
    if '_' not in model:
        base_model = model
        sub_model = None
    else:
        parts = model.split('_')
        base_model = parts[0]
        sub_model = model[-1]
    base_model_pretty = {
        'gah': {
            'fb': 'Farmboy',
            'fg': 'Farmgirl',
        },
        'gan': {
            'df': 'Dwarf',
            'hg': 'Half-Giant',
        },
        'gbn': {
            'pmo': 'Peasant Male Old',
            'fy': 'Fairy',
            'bk': 'Barkeeper',
            'kg': 'King',
            'ft': 'Fortuneteller',
            'ja': 'Jeriah',
            'bs': 'Blacksmith',
        },
        'eam': {
            'dg': 'Droog',
            'dsckrg': 'Disco Krug',
            'HM': 'Hassat Mage',
            'ggt': 'Goblin Grunt',
            'kg': 'Krug Grunt',
        },
        'ecm': {
            'sk': 'Skeleton',
        },
    }[category][base_model]
    return category, base_model, sub_model, base_model_pretty


def get_gender(base_model: str, texture: str):
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
        'bs': 'male',
        'hg': 'male',
        'dsckrg': 'male',
        'sk': 'male?',
        'HM': 'male',
        'ggt': 'male',
    }[base_model]
    if base_model == 'pmo':
        gender = 'female' if texture == 'b_c_gbn_pmo-05' else 'male'  # b_c_gbn_pmo-05 = Verma
    return gender


def get_race(base_model: str, texture: str):
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
        'bs': 'Human',
        'hg': 'Half-Giant',
        'dsckrg': 'Krug',
        'sk': 'Skeleton',
        'HM': 'Hassat',
        'ggt': 'Goblin',
    }[base_model]
    if base_model in ['fb', 'fg']:
        if 'utraean' in texture:
            race = 'Utraean'
    return race


def printout_npc(npc: GameObject, region: Region, with_silent_convos=False):
    template_name = npc.template_name
    screen_name = npc.compute_value('common', 'screen_name').strip('"')
    model = npc.compute_value('aspect', 'model')
    texture = npc.get_template().compute_value('aspect', 'textures', '0')
    model_category, base_model, sub_model, base_model_pretty = parse_model_name(model)
    gender = get_gender(base_model, texture)
    race = get_race(base_model, texture)
    silent_convos_str = ''
    if with_silent_convos:
        convo_attrs = npc.section.get_section('conversation').get_section('conversations').get_attrs()
        convo_names = [a.value for a in convo_attrs]
        region_convos: dict[str, list[ConversationItem]] = region.conversations.conversations
        convos = {name: region_convos[name] for name in convo_names if name in region_convos}
        silent_convos = {name: convo for name, convo in convos.items() if is_silent_convo(convo)}
        silent_convos_str = ' - ' + ', '.join(silent_convos.keys())
    print(f'{template_name} "{screen_name}" - {model} {texture} - {base_model_pretty} - {race} {gender}' + silent_convos_str)


def is_silent_convo(convo: list[ConversationItem]) -> bool:
    for convo_item in convo:
        if not convo_item.sample:
            return True


def has_silent_convos(npc: GameObject, region: Region):
    convo_section = npc.section.get_section('conversation')
    if convo_section is None:
        return False
    convo_attrs = convo_section.get_section('conversations').get_attrs()
    convo_names = [a.value for a in convo_attrs]
    region_convos: dict[str, list[ConversationItem]] = region.conversations.conversations
    convos = [region_convos[name] for name in convo_names if name in region_convos]
    for convo in convos:
        if is_silent_convo(convo):
            return True
    return False


def printout_region_npcs(region: Region, with_silent_convos=False):
    region.load_conversations()
    npcs = region.get_npcs()
    if with_silent_convos:
        npcs = [npc for npc in npcs if has_silent_convos(npc, region)]
    if len(npcs) > 0:
        print(f'{region.get_name()}:')
    for npc in npcs:
        printout_npc(npc, region, with_silent_convos)


def printout_map_npcs(m: Map, with_silent_convos=False):
    for region in m.get_regions().values():
        printout_region_npcs(region, with_silent_convos)


def printout_npcs(map_name: str, bits_path: str, with_silent_convos=False):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    GasParser.get_instance().print_warnings = False
    bits.templates.ignore_duplicate_template_names = True
    bits.templates.get_templates()
    print()
    print(map_name)
    printout_map_npcs(m, with_silent_convos)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printout npcs')
    parser.add_argument('map')
    parser.add_argument('--with-silent-convos', action='store_true')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    printout_npcs(args.map, args.bits, args.with_silent_convos)


if __name__ == '__main__':
    main(sys.argv[1:])
