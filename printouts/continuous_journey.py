import argparse
import os
import sys

from printouts.common import load_level_xp, get_level


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
            data[current_map][current_wl][startpos] = (int(reqlvl), int(xp))
    return data


def filter_flatten_sort(startpos_xp: dict, maps: list[str]):
    journey = list()
    for map_name, map_data in startpos_xp.items():
        if map_name not in maps:
            continue
        for wl, map_wl_data in map_data.items():
            for startpos, (reqlvl, xp) in map_wl_data.items():
                journey.append((reqlvl, map_name, wl, startpos, xp))
    journey.sort(key=lambda x: x[0])
    return journey


def continuous_journey(maps: list[str]):
    startpos_xp = read_startpos_xp()
    level_xp = load_level_xp()
    journey = filter_flatten_sort(startpos_xp, maps)

    xp = 0
    lvl = 0
    for step in journey:
        lvl = get_level(xp, level_xp)
        reqlvl, map_name, wl, startpos, xp = step
        print(f'At level {lvl}, next step: {map_name} {wl} {startpos}, required level {reqlvl}')
        if reqlvl > lvl:
            print(f'The End - required level too high')
            break
    print(f'Reached level {lvl}')


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
