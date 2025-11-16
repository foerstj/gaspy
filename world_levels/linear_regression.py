import argparse

import numpy
import sys

from bits.bits import Bits
from printouts.common import get_wl_templates
from printouts.world_level_stats import wl_actor_dict
from world_levels.world_level_templates import STAT_ATTRS


REG_VARS_SELF = {stat: [stat] for stat in STAT_ATTRS}

REG_VARS_XP = {stat: [stat, 'experience_value' if stat != 'experience_value' else 'max_life'] for stat in STAT_ATTRS}


def calc_linear_regression(bits: Bits, wl: str, regression_vars: dict):
    actors = bits.templates.get_actor_templates()
    wls_actors = get_wl_templates(actors)

    stats_vals = {s: list() for s in STAT_ATTRS}
    for name, wl_actors in wls_actors.items():
        regular_actor = wl_actors['regular']
        wl_actor = wl_actors[wl]
        if wl_actor is None:
            continue

        regular_stats = wl_actor_dict(regular_actor)
        wl_stats = wl_actor_dict(wl_actor)

        for stat, stat_reg_vars in regression_vars.items():
            regular_value = regular_stats[stat]
            if regular_value is None:
                continue
            if not regular_value:  # skip zeroes - zero values remain zero values in V/E
                continue
            regular_values = [regular_stats[var] for var in stat_reg_vars]
            if None in regular_values or 0 in regular_values or 0.0 in regular_values:
                continue
            wl_value = wl_stats[stat]
            stats_vals[stat].append((regular_values, wl_value))

    lins = {stat: tuple() for stat in STAT_ATTRS}
    for stat in STAT_ATTRS:
        x = [v[0] for v in stats_vals[stat]]
        y = [v[1] for v in stats_vals[stat]]
        x = [[v[i] for v in x] for i in range(len(x[0]))]  # flip around
        x = numpy.vstack([x, numpy.ones(len(x[0]))]).T
        coeffs = tuple(numpy.linalg.lstsq(x, y, rcond=None)[0])
        lins[stat] = coeffs

    return lins


def linear_regression(bits_path: str, wl: str):
    bits = Bits(bits_path)

    reg_vars = REG_VARS_XP
    lins = calc_linear_regression(bits, wl, reg_vars)

    print()
    for stat, coeffs in lins.items():
        stat_reg_vars = reg_vars[stat]
        assert len(coeffs) == len(stat_reg_vars) + 1
        coeff_strs = [f'{coeffs[i]:.3f} * regular {var}' for i, var in enumerate(stat_reg_vars)] + [f'{coeffs[-1]:.3f}']
        coeffs_str = ' + '.join(coeff_strs)
        print(f'{wl} {stat} = {coeffs_str}')


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
