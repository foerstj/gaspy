import argparse
import os
import sys

from printouts.level_xp import load_level_xp, get_level


def read_startpos_xp(map_name: str):
    current_wl = None
    data = dict()
    with open(os.path.join('input', 'startpos-xp', f'{map_name}.csv')) as f:
        for line in f.readlines():
            cells = line.strip().split(';')
            wl, startpos, reqlvl, xp = [c.strip('"') for c in cells]
            if wl:
                current_wl = wl
            if current_wl not in data:
                data[current_wl] = dict()
            data[current_wl][startpos] = (int(reqlvl), int(xp))
    return data


def filter_flatten_sort(startpos_xp: dict, maps: list[str]):
    journey = list()
    for map_name, map_data in startpos_xp.items():
        if maps is not None and map_name not in maps:
            continue
        for wl, map_wl_data in map_data.items():
            for startpos, (reqlvl, xp) in map_wl_data.items():
                journey.append((reqlvl, map_name, wl, startpos, xp))
    journey.sort(key=lambda x: x[0])
    return journey


def continuous_journey(maps: list[str]):
    startpos_xp = {map_name: read_startpos_xp(map_name) for map_name in maps}
    level_xp = load_level_xp()
    journey = filter_flatten_sort(startpos_xp, maps)
    for step in journey:
        print(repr(step))

    my_xp = 0
    lvl = 0
    for step in journey:
        lvl = get_level(my_xp, level_xp)
        reqlvl, map_name, wl, startpos, step_xp = step
        step_xp = int(step_xp * 0.35)  # xp factor applied when playing alone in multiplayer
        print(f'At level {lvl} ({my_xp} xp), next step: {map_name} {wl} {startpos}, required level {reqlvl} ({step_xp} xp)')
        if reqlvl > lvl:
            print(f'The End - required level too high')
            break
        my_xp += step_xp
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
