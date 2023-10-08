import sys
import argparse

from bits.language import Language
from gas.gas import Section
from gas.gas_file import GasFile


def load_lang_file(filename: str) -> dict:
    file = GasFile(filename)
    gas = file.get_gas()
    assert len(gas.items) == 1
    assert isinstance(gas.items[0], Section)
    lang_section: Section = gas.items[0]
    assert lang_section.has_t_n_header()
    t, n = lang_section.get_t_n_header()
    assert n == 'text'
    return Language.load_text_translations(lang_section)


def compare_translations(filename_a: str, filename_b: str):
    print(f"Comparing translations\nfile a: {filename_a}\nfile b: {filename_b}")
    a = load_lang_file(filename_a)
    print(f'File a: {len(a)} translations')
    b = load_lang_file(filename_b)
    print(f'File b: {len(b)} translations')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy compare_translations')
    parser.add_argument('file_a')
    parser.add_argument('file_b')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    compare_translations(args.file_a, args.file_b)


if __name__ == '__main__':
    main(sys.argv[1:])
