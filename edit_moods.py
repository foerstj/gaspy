import argparse
import sys

from bits.bits import Bits
from bits.maps.light import Color
from bits.moods import Moods
from gas.molecules import Hex


def half_float(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = float(value.rstrip('f'))
    return float(value) / 2


def half_gray(color):
    if color is None:
        return None
    if isinstance(color, str):
        color = Hex.parse(color)
    color = Color(color)
    a, r, g, b = color.get_argb()
    rgb_avg = (r + g + b) / 3
    r = int((r + rgb_avg) / 2)
    g = int((g + rgb_avg) / 2)
    b = int((b + rgb_avg) / 2)
    return Color.from_argb(a, r, g, b)


def edit_fog(moods: Moods, edit: list[str]):
    if edit == ['near-dists', 'half']:
        for mood in moods.get_all_moods():
            mood.fog.near_dist = half_float(mood.fog.near_dist)
            mood.fog.lowdetail_near_dist = half_float(mood.fog.lowdetail_near_dist)
    if edit == ['color', 'half-gray']:
        for mood in moods.get_all_moods():
            mood.fog.color = half_gray(mood.fog.color)


def do_edit_moods(moods: Moods, edit: str):
    edit = edit.split(':')
    if edit[0] == 'fog':
        edit_fog(moods, edit[1:])


def edit_moods(bits_path: str, edits: list[str]):
    bits = Bits(bits_path)
    bits.moods.load_moods()
    for edit in edits:
        do_edit_moods(bits.moods, edit)
    bits.moods.save()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit moods')
    parser.add_argument('--edit', action='append')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    edit_moods(args.bits, args.edit or [])


if __name__ == '__main__':
    main(sys.argv[1:])
