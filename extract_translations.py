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
    texts = {m.get_data().name, m.get_data().description}
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


def extract_translations(map_name, lang):
    bits = Bits()
    lang_code = {'de': '0x0407'}[lang]
    m = bits.maps[map_name]
    existing_translations = bits.language.get_translations(lang_code)
    used_texts_map = extract_texts_map(m)
    used_texts_templates = extract_texts_templates()


def main(argv):
    map_name = argv[0]
    lang = argv[1]
    extract_translations(map_name, lang)


if __name__ == '__main__':
    main(sys.argv[1:])
