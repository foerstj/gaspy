import argparse
import sys

from bits.bits import Bits
from gas.gas_dir import GasDir
from gas.gas_file import GasFile


def edit_moods_file(gas_file: GasFile):
    print(gas_file.path)


def edit_moods_dir(gas_dir: GasDir):
    for gas_file in gas_dir.get_gas_files().values():
        edit_moods_file(gas_file)
    for subdir in gas_dir.get_subdirs().values():
        edit_moods_dir(subdir)  # recurse


def edit_moods(bits_path: str):
    bits = Bits(bits_path)
    print(f'Edit moods in {bits.gas_dir.path}')
    edit_moods_dir(bits.moods.gas_dir)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit moods')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    edit_moods(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
