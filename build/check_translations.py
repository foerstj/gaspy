import argparse
import sys

from bits.bits import Bits
from bits.language import LANGS, LANGS_REVERSE
from bits.maps.region import Region
from gas.gas_parser import GasParser


def check_translation(value: str) -> bool:
    if 'â€‹' in value:  # This is apparently how a ZWSP (zero-width space) ends up in here
        return False
    return value[0] == '"' and value[-1] == '"' and '"' not in value[1:-2]


def get_translations(bits: Bits):
    translations = dict()
    if bits.language.gas_dir is None:
        return translations
    gas_parser = GasParser.get_instance()
    assert len(gas_parser.warnings) == 0, gas_parser.warnings
    for gas_file in bits.language.gas_dir.get_gas_files().values():
        for lang_section in gas_file.get_gas().get_sections():
            assert lang_section.has_t_n_header()
            t, n = lang_section.get_t_n_header()
            if n != 'text':
                continue  # ui translations
            section_lang_code = t
            if section_lang_code not in translations:
                translations[section_lang_code] = list()
            translations_for_lang = translations[section_lang_code]
            for section in lang_section.get_sections():
                value_from = section.get_attr_value('from')
                value_to = section.get_attr_value('to')
                translations_for_lang.append((value_from, value_to))
    assert len(gas_parser.warnings) == 0, gas_parser.warnings
    return translations


def check_translations(bits: Bits) -> bool:
    all_good = True
    for lang_code, translations in get_translations(bits).items():
        lang_name = LANGS_REVERSE[lang_code].upper()
        for (value_from, value_to) in translations:
            is_from_ok = check_translation(value_from)
            if not is_from_ok:
                print(f'  {lang_name}: from = {value_from}')
            is_to_ok = check_translation(value_to)
            if not is_to_ok:
                print(f'  {lang_name}: to = {value_to}')
            all_good &= is_from_ok & is_to_ok
    return all_good


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_translations')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    bits_path = args.bits
    bits = Bits(bits_path)
    valid = check_translations(bits)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
