import sys
import argparse
from argparse import Namespace

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


def do_compare_translations(a: dict, b: dict, opts: Namespace):
    keys_a = set(a.keys())
    keys_b = set(b.keys())
    keys_a_only = keys_a.difference(keys_b)
    print(f'Keys only in a: {len(keys_a_only)}')
    if opts.print_keys_a_only:
        for key in keys_a_only:
            print(f'  {key}')
    keys_b_only = keys_b.difference(keys_a)
    print(f'Keys only in b: {len(keys_b_only)}')
    if opts.print_keys_b_only:
        for key in keys_b_only:
            print(f'  {key}')
    keys_common = keys_a.intersection(keys_b)
    print(f'Keys common: {len(keys_common)}')


def compare_translations(filename_a: str, filename_b: str, opts: Namespace):
    print(f"Comparing translations\nfile a: {filename_a}\nfile b: {filename_b}")
    a = load_lang_file(filename_a)
    print(f'File a: {len(a)} translations')
    b = load_lang_file(filename_b)
    print(f'File b: {len(b)} translations')
    do_compare_translations(a, b, opts)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy compare_translations')
    parser.add_argument('file_a')
    parser.add_argument('file_b')
    parser.add_argument('--print-keys-a-only', action='store_true')
    parser.add_argument('--print-keys-b-only', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    compare_translations(args.file_a, args.file_b, args)


if __name__ == '__main__':
    main(sys.argv[1:])
