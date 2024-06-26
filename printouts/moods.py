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
            'music ambient track',
            'music standard track',
            'rain density',
            'snow density',
            'has sun',
            'wind velocity',
            'wind direction'
        ]
    ]
    for file_key, file_moods in moods.items():
        for mood in file_moods:
            row = [
                file_key,
                mood.mood_name,
                mood.transition_time,
                'interior' if mood.interior else None,
                mood.fog.color if mood.fog else None,
                mood.fog.near_dist if mood.fog else None,
                mood.fog.far_dist if mood.fog else None,
                mood.frustum.width if mood.frustum else None,
                mood.frustum.height if mood.frustum else None,
                mood.music.ambient.track if mood.music else None,
                mood.music.standard.track if mood.music else None,
                mood.rain.density if mood.rain else None,
                mood.snow.density if mood.snow else None,
                'sun' if mood.sun else None,
                mood.wind.velocity if mood.wind else None,
                mood.wind.direction if mood.wind else None,
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
