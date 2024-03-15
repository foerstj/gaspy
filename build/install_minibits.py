import argparse
import os
import sys

from bits.bits import Bits


def install_minibits(bits_path: str, minibits_path: str):
    print('Here we go!')
    assert os.path.exists(minibits_path)
    bits = Bits(bits_path)
    minibits_txt_path = os.path.join(bits.gas_dir.path, 'minibits.txt')
    assert os.path.exists(minibits_txt_path)
    print('That\'s it folks!')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy install_minibits')
    parser.add_argument('--bits', default='DSLOA')
    parser.add_argument('--minibits', required=True)
    return parser


def parse_args(argv: list[str]):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str]):
    args = parse_args(argv)
    install_minibits(args.bits, args.minibits)


if __name__ == '__main__':
    main(sys.argv[1:])
