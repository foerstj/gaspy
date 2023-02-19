import argparse
import os
import sys

from bits.bits import Bits
from bits.maps.conversations_gas import ConversationsGas
from bits.maps.map import Map
from bits.maps.region import Region


def filter_texts(attr_values: set[str]) -> set[str]:
    texts = {value for value in attr_values if value is not None}
    texts = {text.strip('"') for text in texts}
    return {text for text in texts if text}


def extract_texts_region(region: Region) -> set[str]:
    texts = set()

    region.load_conversations()
    if region.conversations:
        assert isinstance(region.conversations, ConversationsGas)
        for convo in region.conversations.conversations.values():
            for item in convo:
                texts.add(item.screen_text)

    region.objects.load_objects()
    for game_objects in region.objects.get_objects_dict().values():
        for game_object in game_objects:
            texts.add(game_object.get_own_value('common', 'screen_name'))

    return texts


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
        for update in quest.updates:
            texts.add(update.description)

    m.load_lore()
    for lore_text in m.lore.lore.values():
        texts.add(lore_text)

    m.load_tips()
    for tip in m.tips.tips.values():
        for tip_text in tip.texts:
            texts.add(tip_text)

    for region in m.get_regions().values():
        texts |= extract_texts_region(region)

    return filter_texts(texts)


def extract_texts_templates(bits: Bits) -> set[str]:
    texts = set()

    for template in bits.templates.get_leaf_templates().values():
        texts.add(template.compute_value('common', 'screen_name'))

    for template in bits.templates.get_leaf_templates().values():
        texts.add(template.compute_value('set_item', 'set_name'))

    # todo enchantments (attr "description" in components)

    return filter_texts(texts)


def print_missing_translations(used: set[str], existing: set[str], proper_names: set[str]):
    missing = used.difference(existing).difference(proper_names)
    if len(missing) > 0:
        print(f'{len(missing)} missing translations:')
        for missing_text in missing:
            print(missing_text.replace('\n', '\\n'))
    else:
        print(f'No missing translations.')


def extract_translations_map(m: Map, existing_translations: set, proper_names: set):
    used_texts = extract_texts_map(m)
    print_missing_translations(used_texts, existing_translations, proper_names)


def extract_translations_templates(bits: Bits, existing_translations: set, proper_names: set):
    used_texts = extract_texts_templates(bits)
    print_missing_translations(used_texts, existing_translations, proper_names)


def load_proper_names(file_name) -> set[str]:
    with open(os.path.join('input', file_name)) as f:
        lines = f.readlines()
    lines = {line.rstrip('\n').replace('\\n', '\n') for line in lines}
    names = {line for line in lines if line}
    print(f'{len(names)} proper names loaded')
    return names


def extract_translations(bits_path: str, lang: str, templates: bool, map_names: list[str], proper_names_file: str = None):
    bits = Bits(bits_path)
    lang_code = {'de': '0x0407', 'fr': '0x040c'}[lang]
    existing_translations = set(bits.language.get_translations(lang_code).keys())
    proper_names = load_proper_names(proper_names_file) if proper_names_file else set()
    if templates:
        print('\ntemplates:')
        extract_translations_templates(bits, existing_translations, proper_names)
    for map_name in map_names:
        print(f'\nmap {map_name}:')
        extract_translations_map(bits.maps[map_name], existing_translations, proper_names)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy extract_translations')
    parser.add_argument('--templates', action='store_true', help='Extract strings from contentdb/templates')
    parser.add_argument('--map', action='append', dest='map_names')
    parser.add_argument('--lang', required=True, choices=['de', 'fr'])
    parser.add_argument('--names', help='File with proper names that don\'t need translating')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_names = args.map_names or []
    extract_translations(args.bits, args.lang, args.templates, map_names, args.names)


if __name__ == '__main__':
    main(sys.argv[1:])
