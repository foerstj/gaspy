import argparse

import sys

from bits.bits import Bits
from printouts.csv import write_csv


def printout_moods(bits: Bits):
    moods = bits.moods.get_moods()
    csv = [
        [
            'file',
            'mood',
            'transition',
            'interior',
            'fog color',
            'fog near_dist',
            'fog far_dist',
            'frustum width',
            'frustum height',
        ]
    ]
    for file_key, file_moods in moods.items():
        for mood in file_moods:
            row = [
                file_key,
                mood.mood_name,
                mood.transition_time,
                mood.interior,
                mood.fog.color if mood.fog else None,
                mood.fog.near_dist if mood.fog else None,
                mood.fog.far_dist if mood.fog else None,
                mood.frustum.width if mood.frustum else None,
                mood.frustum.height if mood.frustum else None,
            ]
            csv.append(row)
    write_csv('moods', csv)


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
