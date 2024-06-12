import argparse

import sys

from bits.bits import Bits


def printout_moods(bits: Bits):
    moods = bits.moods.get_moods()
    for file_key, file_moods in moods.items():
        for mood in file_moods:
            print(f'{file_key} {mood.mood_name}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printouts moods')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits = Bits(args.bits)
    printout_moods(bits)


if __name__ == '__main__':
    main(sys.argv[1:])
