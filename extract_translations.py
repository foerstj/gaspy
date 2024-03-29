import argparse
import os
import sys

from bits.bits import Bits
from bits.language import LANGS
from bits.maps.conversations_gas import ConversationsGas
from bits.maps.map import Map
from bits.maps.region import Region
from gas.gas import Gas, Section, Attribute
from gas.gas_dir import GasDir


# lists are used instead of sets, to export translations in order
def unique_values(values: list[str]) -> list[str]:
    values_set = set()
    uniques = list()
    for value in values:
        if value not in values_set:
            uniques.append(value)
        values_set.add(value)
    return uniques


def filter_texts(attr_values: list[str]) -> list[str]:
    texts = [value for value in attr_values if value is not None]
    texts = [text.strip('"') for text in texts]
    return unique_values([text for text in texts if text])


def extract_texts_region(region: Region) -> tuple[list[str], list[str]]:
    texts_general = list()
    texts_convos = list()

    region.load_conversations()
    if region.conversations:
        assert isinstance(region.conversations, ConversationsGas)
        for convo in region.conversations.conversations.values():
            for item in convo:
                texts_convos.append(item.screen_text)
                if item.buttons is not None:
                    for button in item.buttons.values():
                        texts_convos.append(button.text)

    region.objects.load_objects()
    for game_objects in region.objects.get_objects_dict().values():
        if game_objects is None:
            continue  # go file not present in this region. e.g. map_world ac_r1 inventory.gas
        for game_object in game_objects:
            texts_general.append(game_object.get_own_value('common', 'screen_name'))
            texts_general.append(game_object.get_own_value('screen_report', 'description'))  # cmd_region_message

    return texts_general, texts_convos


def extract_texts_map(m: Map) -> dict[str, list[str]]:
    texts: dict[str, list[str]] = {
        'general': list(),
        'lore': list(),
        'convos': list()
    }
    texts['general'].extend([m.get_data().screen_name, m.get_data().description])

    m.load_start_positions()
    for start_group in m.start_positions.start_groups.values():
        texts['general'].append(start_group.screen_name)
        texts['general'].append(start_group.description)

    m.load_world_locations()
    for loc in m.world_locations.locations.values():
        texts['general'].append(loc.screen_name)

    m.load_quests()
    for chapter in m.quests.chapters.values():
        texts['general'].append(chapter.screen_name)
        for update in chapter.updates:
            texts['general'].append(update.description)
    for quest in m.quests.quests.values():
        texts['general'].append(quest.screen_name)
        for update in quest.updates:
            texts['general'].append(update.description)

    m.load_lore()
    for lore_text in m.lore.lore.values():
        lore_text = lore_text.replace('\\n', '\n')  # weird special behavior of newlines in lore...
        texts['lore'].append(lore_text)

    m.load_tips()
    for tip in m.tips.tips.values():
        for tip_text in tip.texts:
            texts['general'].append(tip_text)

    for region in m.get_regions().values():
        region_texts_general, region_texts_convos = extract_texts_region(region)
        texts['general'] += region_texts_general
        texts['convos'] += region_texts_convos

    return {key: filter_texts(value) for key, value in texts.items()}


def extract_texts_templates(bits: Bits) -> list[str]:
    texts = list()

    for template in bits.templates.get_leaf_templates().values():
        texts.append(template.compute_value('common', 'screen_name'))

    for template in bits.templates.get_leaf_templates().values():
        texts.append(template.compute_value('set_item', 'set_name'))

    for template in bits.templates.get_leaf_templates().values():
        # a bit lazy / too broad - descriptions or component subsections could be overwritten by descendants:
        for base_template in template.base_templates([template]):
            # a bit lazy again, but we need to find common.description, spell_*.description, and magic.enchantments."*".description:
            for desc_attr in base_template.section.find_attrs_recursive('description'):
                texts.append(desc_attr.value)
            # even more texts in spell_ components:
            for desc_attr_name in ['state_description', 'caster_description', 'other_description', 'freeze_description']:
                for desc_attr in base_template.section.find_attrs_recursive(desc_attr_name):
                    texts.append(desc_attr.value)

    for template in bits.templates.get_leaf_templates().values():
        if not template.has_component('messages'):
            continue
        # a bit lazy / too broad - descriptions or component subsections could be overwritten by descendants:
        for base_template in template.base_templates([template]):
            for messages_section in base_template.section.get_sections('messages'):
                for message_section in messages_section.get_sections():
                    texts.append(message_section.get_attr_value('screen_text'))

    return filter_texts(texts)


def write_translations_file(missing_translations: list[str], lang: str, file_dir: GasDir, name: str, attr='from'):
    lang_code = LANGS[lang]
    write_into_from_attr = attr != 'to'
    write_into_to_attr = attr != 'from'
    gas = Gas([
        Section(
            Section.make_t_n_header(lang_code, 'text'),
            [Section('0x0000', [
                Attribute('from', f'"{mt}"' if write_into_from_attr else '""'),
                Attribute('to', f'"{mt}"' if write_into_to_attr else '""')
            ]) for mt in missing_translations]
        )
    ])
    file_name = f'extracted-translations-{name}.{lang}'
    assert not file_dir.has_gas_file(file_name), f'Gas file {file_name} already exists'
    gas_file = file_dir.create_gas_file(file_name, gas)
    file_dir.save()
    print(f'\nWrote gas file to {gas_file.path}')


def write_missing_translations(used: list[str], existing: set[str], proper_names: set[str], lang: str, bits: Bits, name: str, attr='from'):
    missing = [s for s in used if s not in existing and s not in proper_names]
    if len(missing) == 0:
        print(f'No missing translations.')
        return
    print(f'{len(missing)} missing translations:')
    for missing_text in missing:
        print(missing_text.replace('\n', '\\n'))
    file_dir = bits.gas_dir.get_or_create_subdir('language')
    write_translations_file(missing, lang, file_dir, name, attr)


def extract_translations_map(m: Map, existing_translations: set[str], proper_names: set[str], lang: str, splits: set[str], attr='from'):
    used_texts_dict: dict[str, list[str]] = extract_texts_map(m)
    for split in splits:
        assert split in ['convos', 'lore']
        used_texts_split = used_texts_dict.pop(split)
        write_missing_translations(used_texts_split, existing_translations, proper_names, lang, m.bits, f'map-{m.get_name()}-{split}', attr)
    used_texts_general = list()
    for used_texts in used_texts_dict.values():
        used_texts_general += used_texts
    file_name = f'map-{m.get_name()}-general' if len(splits) > 0 else f'map-{m.get_name()}'
    write_missing_translations(unique_values(used_texts_general), existing_translations, proper_names, lang, m.bits, file_name, attr)


def extract_translations_templates(bits: Bits, existing_translations: set[str], proper_names: set[str], lang: str, attr='from'):
    used_texts = extract_texts_templates(bits)
    write_missing_translations(used_texts, existing_translations, proper_names, lang, bits, 'templates', attr)


def load_proper_names(file_names: list[str]) -> set[str]:
    names: set[str] = set([])
    for file_name in file_names:
        with open(os.path.join('input', file_name)) as f:
            lines = f.readlines()
        lines = {line.rstrip('\n').replace('\\n', '\n') for line in lines}
        names.update({line for line in lines if line})
    print(f'{len(names)} proper names loaded')
    return names


def extract_translations(bits_path: str, lang: str, templates: bool, map_names: list[str], proper_names_files: list[str] = None, split: list[str] = None, attr='from'):
    bits = Bits(bits_path)
    lang_code = LANGS[lang]
    if split is None:
        split = list()

    existing_translations = set(bits.language.get_translations(lang_code).keys())
    if bits.language.gas_dir:
        bits.language.gas_dir.clear_cache()  # don't save loaded files
    print(f'{len(existing_translations)} existing translations loaded')

    proper_names = load_proper_names(proper_names_files) if proper_names_files else set()

    if templates:
        print('\ntemplates:')
        extract_translations_templates(bits, existing_translations, proper_names, lang, attr)

    for map_name in map_names:
        print(f'\nmap {map_name}:')
        extract_translations_map(bits.maps[map_name], existing_translations, proper_names, lang, set(split), attr)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy extract_translations')
    parser.add_argument('--templates', action='store_true', help='Extract strings from contentdb/templates')
    parser.add_argument('--map', action='append', dest='map_names')
    parser.add_argument('--lang', required=True, choices=['de', 'fr', 'es'])
    parser.add_argument('--names', nargs='*', help='File with proper names that don\'t need translating')
    parser.add_argument('--split', nargs='+', choices=['convos', 'lore'], help='Write types of text to separate files')
    parser.add_argument('--attr', choices=['from', 'to', 'both'], default='from', help='Write existing texts in "to" attributes (for i18n of non-English maps)')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_names = args.map_names or []
    extract_translations(args.bits, args.lang, args.templates, map_names, args.names, args.split, args.attr)


if __name__ == '__main__':
    main(sys.argv[1:])
