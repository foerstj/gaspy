import argparse
import sys

from bits.bits import Bits
from gas.gas import Gas, Section
from gas.gas_dir import GasDir


def untranslate_file(lang_dir: GasDir, lang_file_name: str):
    print(lang_file_name)
    lang_file = lang_dir.get_gas_files().get(lang_file_name)
    lang_file_gas: Gas = lang_file.get_gas()
    text_section: Section = lang_file_gas.items[0]
    for translation_section in text_section.get_sections():
        if translation_section.get_attr('from') and translation_section.get_attr('to'):
            value = translation_section.get_attr_value('from')
            value_enc = bytes(value, 'utf8').decode('ansi')  # 'from' must remain ANSI encoded to match the string; 'to' must be in UTF8 to be displayed properly
            translation_section.set_attr_value('to', value_enc)
    lang_file.save()


def untranslate(lang_file_name, bits_path=None):
    bits = Bits(bits_path)
    lang_dir = bits.gas_dir.get_subdir('language')
    if lang_file_name:
        untranslate_file(lang_dir, lang_file_name)
    else:
        for lang_file_name in lang_dir.get_gas_files():
            untranslate_file(lang_dir, lang_file_name)
    print('untranslated!')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy untranslate')
    parser.add_argument('lang_file', nargs='?', default=None)
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    untranslate(args.lang_file, args.bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
