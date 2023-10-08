import sys
import argparse
from argparse import Namespace

from bits.bits import Bits
from bits.language import Language
from gas.gas import Section, Gas, Attribute
from gas.gas_file import GasFile


def load_lang_file(filename: str) -> (str, dict):
    file = GasFile(filename)
    gas = file.get_gas()
    assert len(gas.items) == 1
    assert isinstance(gas.items[0], Section)
    lang_section: Section = gas.items[0]
    assert lang_section.has_t_n_header()
    t, n = lang_section.get_t_n_header()
    assert n == 'text'
    return t, Language.load_text_translations(lang_section)


def write_lang_file(translations: dict, filename_base: str, lang_code: str):
    gas = Gas([
        Section(
            Section.make_t_n_header(lang_code, 'text'),
            [Section('0x0000', [
                Attribute('from', f'"{k}"'),
                Attribute('to', f'"{v}"')
            ]) for k, v in translations.items()]
        )
    ])
    bits = Bits()
    file_dir = bits.gas_dir.get_or_create_subdir('language')
    gas_file = file_dir.create_gas_file(filename_base, gas)
    file_dir.save()
    print(f'Wrote gas file to {gas_file.path}')


def print_keys(keys: set):
    for key in keys:
        print(f'  {key}')


def do_compare_translations(a: dict, b: dict, opts: Namespace, lang_code: str):
    keys_a = set(a.keys())
    keys_b = set(b.keys())

    keys_a_only = keys_a.difference(keys_b)
    print(f'Keys only in a: {len(keys_a_only)}')
    if opts.print_keys_a_only:
        print_keys(keys_a_only)
    if opts.write_a_only:
        t_only = {k: v for k, v in a.items() if k in keys_a_only}
        write_lang_file(t_only, 'a-only', lang_code)

    keys_b_only = keys_b.difference(keys_a)
    print(f'Keys only in b: {len(keys_b_only)}')
    if opts.print_keys_b_only:
        print_keys(keys_b_only)
    if opts.write_b_only:
        t_only = {k: v for k, v in b.items() if k in keys_b_only}
        write_lang_file(t_only, 'b-only', lang_code)

    keys_common = keys_a.intersection(keys_b)
    print(f'Keys common: {len(keys_common)}')
    if opts.print_keys_common:
        print_keys(keys_common)
    a_common = {k: v for k, v in a.items() if k in keys_common}
    b_common = {k: v for k, v in b.items() if k in keys_common}
    t_common_same = {k: v for k, v in a_common.items() if v == b_common[k]}
    keys_common_same = set(t_common_same.keys())
    print(f'Keys common same: {len(keys_common_same)}')
    if opts.print_keys_common_same:
        print_keys(keys_common_same)
    if opts.write_common_same:
        write_lang_file(t_common_same, 'common-same', lang_code)


def compare_translations(filename_a: str, filename_b: str, opts: Namespace):
    print(f"Comparing translations\nfile a: {filename_a}\nfile b: {filename_b}")
    lc_a, a = load_lang_file(filename_a)
    print(f'File a: {len(a)} translations')
    lc_b, b = load_lang_file(filename_b)
    print(f'File b: {len(b)} translations')
    assert lc_a == lc_b
    do_compare_translations(a, b, opts, lc_a)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy compare_translations')
    parser.add_argument('file_a')
    parser.add_argument('file_b')
    parser.add_argument('--print-keys-a-only', action='store_true')
    parser.add_argument('--print-keys-b-only', action='store_true')
    parser.add_argument('--print-keys-common', action='store_true')
    parser.add_argument('--print-keys-common-same', action='store_true')
    parser.add_argument('--write-a-only', action='store_true')
    parser.add_argument('--write-b-only', action='store_true')
    parser.add_argument('--write-common-same', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    compare_translations(args.file_a, args.file_b, args)


if __name__ == '__main__':
    main(sys.argv[1:])
