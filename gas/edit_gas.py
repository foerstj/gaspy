import argparse

import sys

from bits.bits import Bits
from gas.gas_dir import GasDir
from gas.gas_file import GasFile


def find_gas_file(gas_dir: GasDir, gas_file_path: list[str]) -> GasFile:
    gas_dir = gas_dir.get_subdir(gas_file_path[:-1])
    if gas_dir is None:
        return None
    return gas_dir.get_gas_file(gas_file_path[-1])


def do_edit_gas(gas_file: GasFile, edits: list[str]):
    gas = gas_file.get_gas()
    for edit in edits:
        var, val = edit.split('=')
        attr_path = var.split(':')
        attr = gas.resolve_attr(*attr_path)
        assert attr is not None
        attr.set_value(val, attr.datatype)


def edit_gas(bits_path: str, gas_file_path: str, edits: list[str]):
    bits = Bits(bits_path)
    gas_file = find_gas_file(bits.gas_dir, gas_file_path.split('/'))
    assert gas_file is not None, gas_file_path
    do_edit_gas(gas_file, edits)
    gas_file.save()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit gas')
    parser.add_argument('gas_file', help='slash-separated gas path, e.g. config/engine')
    parser.add_argument('--edit', nargs='+', help='--edit engine_settings:minimap_max_size=144 engine_settings:default_minimap_size=108')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    edit_gas(args.bits, args.gas_file, args.edit or list())


if __name__ == '__main__':
    main(sys.argv[1:])
