import argparse
import sys

from bits.bits import Bits


def edit_moods(bits_path: str):
    bits = Bits(bits_path)
    for path, moods in bits.moods.get_moods().items():
        print(path)
        for mood in moods:
            print(f'  {mood.mood_name}')


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
