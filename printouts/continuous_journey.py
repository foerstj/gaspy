import argparse
import os
import sys


def read_startpos_xp():
    current_map = None
    current_wl = None
    data = dict()
    with open(os.path.join('input', 'startpos-xp.csv')) as f:
        for line in f.readlines():
            cells = line.strip().split(';')
            map_name, wl, startpos, reqlvl, xp = cells
            if map_name:
                current_map = map_name
            if wl:
                current_wl = wl
            if current_map not in data:
                data[current_map] = dict()
            if current_wl not in data[current_map]:
                data[current_map][current_wl] = dict()
            data[current_map][current_wl][startpos] = (reqlvl, xp)
    return data


def continuous_journey(maps: list[str]):
    startpos_xp = read_startpos_xp()
    print(repr(maps))
    print(repr(startpos_xp))


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy continuous_journey')
    parser.add_argument('--maps', nargs='+')
    return parser


def parse_args(argv: list[str]):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str]):
    args = parse_args(argv)
    continuous_journey(args.maps)


if __name__ == '__main__':
    main(sys.argv[1:])
