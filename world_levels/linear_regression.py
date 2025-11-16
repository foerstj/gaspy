import argparse

import numpy
import sys

from bits.bits import Bits
from printouts.common import get_wl_templates
from printouts.world_level_stats import wl_actor_dict
from world_levels.world_level_templates import STAT_ATTRS


REG_VARS_SELF = {stat: [stat] for stat in STAT_ATTRS}

REG_VARS_XP = {stat: [stat, 'experience_value' if stat is not 'experience_value' else 'max_life'] for stat in STAT_ATTRS}


def calc_linear_regression(bits: Bits, wl: str):
    actors = bits.templates.get_actor_templates()
    wls_actors = get_wl_templates(actors)

    reg_vars = REG_VARS_XP

    stats_vals = {s: list() for s in STAT_ATTRS}
    for name, wl_actors in wls_actors.items():
        regular_actor = wl_actors['regular']
        wl_actor = wl_actors[wl]
        if wl_actor is None:
            continue

        regular_stats = wl_actor_dict(regular_actor)
        wl_stats = wl_actor_dict(wl_actor)

        for stat, stat_reg_vars in reg_vars.items():
            regular_value = regular_stats[stat]
            if regular_value is None:
                continue
            if not regular_value:  # skip zeroes - zero values remain zero values in V/E
                continue
            regular_values = [regular_stats[var] for var in stat_reg_vars]
            if None in regular_values:
                continue
            wl_value = wl_stats[stat]
            stats_vals[stat].append((regular_values, wl_value))

    lins = {stat: tuple() for stat in STAT_ATTRS}
    for stat in STAT_ATTRS:
        x = [v[0] for v in stats_vals[stat]]
        y = [v[1] for v in stats_vals[stat]]
        x = [[v[i] for v in x] for i in range(len(x[0]))]  # flip around
        x = numpy.vstack([x, numpy.ones(len(x[0]))]).T
        a, b, c = numpy.linalg.lstsq(x, y, rcond=None)[0]
        lins[stat] = (a, b, c)

    return lins


def linear_regression(bits_path: str, wl: str):
    bits = Bits(bits_path)

    lins = calc_linear_regression(bits, wl)

    print()
    for stat, (a, b, c) in lins.items():
        print(f'{wl} {stat} = {a:.3f} * regular {stat} + {b:.3f} * regular xp/life + {c:.3f}')


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
