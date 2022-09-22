import sys

from bits.bits import Bits


def extract_translations(lang_code):
    bits = Bits()
    existing_translations = bits.language.get_translations(lang_code)
    for frm, to in existing_translations.items():
        print(f'{frm} -> {to}')


def main(argv):
    lang = argv[0]
    lang_code = {'de': '0x0407'}[lang]
    extract_translations(lang_code)


if __name__ == '__main__':
    main(sys.argv[1:])
