import argparse
import sys

from bits.bits import Bits
from bits.conversations import ConversationsGas
from bits.map import Map
from bits.region import Region


def extract_texts_region(region: Region) -> set[str]:
    texts = set()

    region.load_conversations()
    if region.conversations:
        assert isinstance(region.conversations, ConversationsGas)
        for convo in region.conversations.conversations.values():
            for item in convo:
                texts.add(item.screen_text)

    for game_objects in [region.get_actors(), region.do_load_objects_interactive()]:
        for game_object in game_objects:
            texts.add(game_object.get_own_value('common', 'screen_name'))

    return {x for x in texts if x is not None}


def extract_texts_map(m: Map) -> set[str]:
    texts = {m.get_data().screen_name, m.get_data().description}

    m.load_start_positions()
    for start_group in m.start_positions.start_groups.values():
        texts.add(start_group.screen_name)
        texts.add(start_group.description)

    m.load_world_locations()
    for loc in m.world_locations.locations.values():
        texts.add(loc.screen_name)

    m.load_quests()
    for quest in m.quests.quests.values():
        texts.add(quest.screen_name)

    # todo tutorial tips
    # todo lore

    for region in m.get_regions().values():
        texts |= extract_texts_region(region)

    return {x for x in texts if x is not None}


def extract_texts_templates(bits: Bits) -> set[str]:
    texts = set()

    for template in bits.templates.get_leaf_templates().values():
        texts.add(template.compute_value('common', 'screen_name'))

    for template in bits.templates.get_leaf_templates().values():
        texts.add(template.compute_value('set_item', 'set_name'))

    # todo enchantments (attr "description" in components)

    return {x for x in texts if x is not None}


def print_missing_translations(used: set, existing: set):
    missing = used.difference(existing)
    if len(missing) > 0:
        print(f'{len(missing)} missing translations:')
        for missing_text in missing:
            print(f'  {missing_text}')


def extract_translations_map(m: Map, existing_translations: set):
    used_texts = extract_texts_map(m)
    print_missing_translations(used_texts, existing_translations)


def extract_translations_templates(bits: Bits, existing_translations: set):
    used_texts = extract_texts_templates(bits)
    print_missing_translations(used_texts, existing_translations)


def extract_translations(lang: str, templates: bool, map_names: list[str]):
    bits = Bits()
    lang_code = {'de': '0x0407'}[lang]
    existing_translations = set(bits.language.get_translations(lang_code).keys())
    if templates:
        extract_translations_templates(bits, existing_translations)
    for map_name in map_names:
        extract_translations_map(bits.maps[map_name], existing_translations)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy extract_translations')
    parser.add_argument('--templates', action='store_true')
    parser.add_argument('--map', action='append', dest='map_names')
    parser.add_argument('--lang', required=True, choices=['de'])
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_names = args.map_names or []
    extract_translations(args.lang, args.templates, map_names)


if __name__ == '__main__':
    main(sys.argv[1:])
