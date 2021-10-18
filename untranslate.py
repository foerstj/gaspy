import sys

from bits import Bits
from gas import Gas, Section
from gas_dir import GasDir


def untranslate_file(lang_dir: GasDir, lang_file_name: str):
    print(lang_file_name)
    lang_file = lang_dir.get_gas_files().get(lang_file_name)
    lang_file_gas: Gas = lang_file.get_gas()
    text_section: Section = lang_file_gas.items[0]
    for translation_section in text_section.get_sections():
        if translation_section.get_attr('from') and translation_section.get_attr('to'):
            translation_section.set_attr_value('to', translation_section.get_attr_value('from'))
    lang_file.save()


def untranslate(lang_file_name):
    bits = Bits()
    lang_dir = bits.gas_dir.get_subdir('language')
    if lang_file_name:
        untranslate_file(lang_dir, lang_file_name)
    else:
        for lang_file_name in lang_dir.get_gas_files():
            untranslate_file(lang_dir, lang_file_name)
    print('untranslated!')


def main(argv):
    lang_file_name = argv[0] if len(argv) > 0 else None
    untranslate(lang_file_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
