import argparse
import os
import sys

from bits.bits import Bits
from bits.maps.map import Map
from gas.gas_parser import GasParser
from printouts.csv import write_csv


def load_startpos_xp_regions(map_name: str):
    startpos_xp_regions = dict()
    current_startpos = None
    with open(os.path.join('input', 'startpos-xp', f'{map_name}.txt')) as file:
        for line in file.readlines():
            line = line.strip()
            if line == '':
                continue
            if line.startswith('#'):
                continue
            segs = line.split(':')
            if segs[0] == '':
                current_startpos = segs[1]
                startpos_xp_regions[current_startpos] = list()
            else:
                region = segs[0]
                weight = float(segs[1]) if len(segs) > 1 else 1
                startpos_xp_regions[current_startpos].append((region, weight))
    return startpos_xp_regions


def write_startpos_xp(map_name: str, startpos_xp: dict):
    csv_lines = list()
    for wl, wl_startpos_xp in startpos_xp.items():
        for startpos, xp in wl_startpos_xp.items():
            csv_lines.append([wl, startpos, int(xp)])
    write_csv(f'startpos-xp\\{map_name}', csv_lines)


def startpos_xp_map(m: Map):
    startpos_xp_regions = load_startpos_xp_regions(m.get_name())
    startpos_xp = dict()
    for wl in m.get_data().worlds:
        startpos_xp[wl] = dict()
        for startpos, regions in startpos_xp_regions.items():
            xp = 0
            for region_name, weight in regions:
                xp += m.get_region(region_name).get_xp(wl) * weight
            startpos_xp[wl][startpos] = xp
    write_startpos_xp(m.get_name(), startpos_xp)


def startpos_xp(bits_path: str, map_names: list[str]):
    bits = Bits(bits_path)
    GasParser.get_instance().print_warnings = False
    bits.templates.get_templates()  # preload

    for map_name in map_names:
        m = bits.maps[map_name]
        startpos_xp_map(m)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy startpos_xp')
    parser.add_argument('--maps', nargs='+')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv: list[str]):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str]):
    args = parse_args(argv)
    startpos_xp(args.bits, args.maps)


if __name__ == '__main__':
    main(sys.argv[1:])
