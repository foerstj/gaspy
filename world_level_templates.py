# Script to generate the veteran & elite templates from the regular ones
import argparse
import sys

from bits.bits import Bits
from bits.templates_cli import print_enemies


def world_level_templates(bits_dir=None):
    bits = Bits(bits_dir)
    print_enemies(bits)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world level templates')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    world_level_templates(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
