import argparse

import sys

from bits.bits import Bits


def equipment(bits_path: str):
    bits = Bits(bits_path)
    for armor_template_name, armor_template in bits.templates.get_leaf_templates('armor').items():
        print(f'{armor_template_name}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Equipment')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    equipment(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
