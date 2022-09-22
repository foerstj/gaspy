import argparse
import sys

from bits.bits import Bits
from bits.map import Map
from bits.region import Region


def extract_texts_region(region: Region) -> set[str]:
    # todo conversations
    # todo actors
    # todo signs / interactives
    return set()


def extract_texts_map(m: Map) -> set[str]:
    texts = {m.get_data().screen_name, m.get_data().description}
    # todo start positions
    # todo tutorial tips
    # todo world locations
    # todo quests
    # todo lore
    for region in m.get_regions().values():
        texts |= extract_texts_region(region)
    return texts


def extract_texts_templates() -> set[str]:
    # todo screen_name (actors, interactives...)
    # todo set_name
    # todo enchantments (attr "description" in components)
    return set()


def print_missing_translations(used: set, existing: set):
    missing = used.difference(existing)
    if len(missing) > 0:
        print(f'{len(missing)} missing translations:')
        for missing_text in missing:
            print(f'  {missing_text}')


def extract_translations_map(m: Map, existing_translations: set):
    used_texts = extract_texts_map(m)
    print_missing_translations(used_texts, existing_translations)


def extract_translations_templates(existing_translations: set):
    used_texts = extract_texts_templates()
    print_missing_translations(used_texts, existing_translations)


def extract_translations(lang: str, templates: bool, map_names: list[str]):
    bits = Bits()
    lang_code = {'de': '0x0407'}[lang]
    existing_translations = set(bits.language.get_translations(lang_code).keys())
    if templates:
        extract_translations_templates(existing_translations)
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
