import argparse

import numpy
import sys

from bits.bits import Bits
from printouts.common import get_wl_templates
from printouts.world_level_stats import wl_actor_dict
from world_levels.world_level_templates import STAT_ATTRS


def calc_linear_regression(bits: Bits, wl: str):
    actors = bits.templates.get_actor_templates()
    wls_actors = get_wl_templates(actors)
    stats_vals = {s: list() for s in STAT_ATTRS}
    for name, wl_actors in wls_actors.items():
        regular_actor = wl_actors['regular']
        regular_stats = wl_actor_dict(regular_actor)
        wl_actor = wl_actors[wl]
        if wl_actor is None:
            continue
        wl_stats = wl_actor_dict(wl_actor)
        for stat in STAT_ATTRS:
            regular_value = regular_stats[stat]
            if regular_value is None:
                continue
            regular_value = float(regular_value)
            if not regular_value:  # skip zeroes
                continue
            wl_value = float(wl_stats[stat])
            stats_vals[stat].append((regular_value, wl_value))

    lins = {stat: tuple() for stat in STAT_ATTRS}
    for stat in STAT_ATTRS:
        x = [v[0] for v in stats_vals[stat]]
        y = [v[1] for v in stats_vals[stat]]
        m, c = numpy.polyfit(x, y, 1)
        lins[stat] = (m, c)

    return lins


def linear_regression(bits_path: str, wl: str):
    bits = Bits(bits_path)

    lins = calc_linear_regression(bits, wl)

    print()
    for stat, (m, c) in lins.items():
        print(f'{stat}: {wl} = {m:.3f} * regular + {c:.3f}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world levels regression')
    parser.add_argument('wl', choices=['veteran', 'elite'])
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    linear_regression(args.bits, args.wl)


if __name__ == '__main__':
    main(sys.argv[1:])
