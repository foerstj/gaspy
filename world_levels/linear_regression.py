import argparse
import os

import numpy
import sys

from bits.bits import Bits
from printouts.common import get_wl_templates
from printouts.csv import read_csv
from printouts.world_level_stats import wl_actor_dict
from world_levels.world_level_templates import STAT_ATTRS


REG_VARS_SELF = {stat: [stat] for stat in STAT_ATTRS}

REG_VARS_XP = {stat: [stat, 'experience_value' if stat != 'experience_value' else 'max_life'] for stat in STAT_ATTRS}


def read_csv_as_dicts(name: str):
    csv = read_csv(name)
    header_row = csv[0]
    data_rows = csv[1:]
    data = list()
    for data_row in data_rows:
        row_dict = dict()
        for i, header in enumerate(header_row):
            row_dict[header] = data_row[i]
        data.append(row_dict)
    return data


def read_enemy_occurrence():
    csv = read_csv_as_dicts('Enemy Occurrence')
    enemy_occurrences = {row['template']: int(row['start lvl']) for row in csv if row['start lvl']}
    return enemy_occurrences


def calc_linear_regression(bits: Bits, wl: str, regression_vars: dict):
    actors = bits.templates.get_enemy_templates()
    wls_actors = get_wl_templates(actors)
    enemy_occurrence = read_enemy_occurrence()

    stats_vals = {s: list() for s in STAT_ATTRS}
    for name, wl_actors in wls_actors.items():
        if name not in enemy_occurrence:
            continue
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


def linear_regression(bits_path: str, wl: str, reg_vars_name: str):
    bits = Bits(bits_path)

    reg_vars = REG_VARS_SELF if reg_vars_name == 'self' else REG_VARS_XP
    lins = calc_linear_regression(bits, wl, reg_vars)

    print()
    lines = list()
    for stat, coeffs in lins.items():
        stat_reg_vars = reg_vars[stat]
        assert len(coeffs) == len(stat_reg_vars) + 1
        coeff_strs = [f'{coeffs[i]:.3f} * regular {var}' for i, var in enumerate(stat_reg_vars)] + [f'{coeffs[-1]:.3f}']
        coeffs_str = ' + '.join(coeff_strs)
        line = f'{wl} {stat} = {coeffs_str}'
        print(line)
        lines.append(line + '\n')
    filename = 'world-level-linregs.txt'
    with open(os.path.join('output', filename), 'w') as file:
        file.writelines(lines)


def read_linregs_file():
    filename = 'world-level-linregs.txt'
    with open(os.path.join('input', filename), 'r') as file:
        lines = file.readlines()
    linregs = {'veteran': dict(), 'elite': dict()}
    for line in lines:
        wl_stat, formula = line.strip().split('=', 1)
        wl, stat = wl_stat.strip().split()
        formula_parts = formula.strip().split('+')
        coeff_part, const_part = formula_parts
        coeff_const = float(const_part)
        coeff_value, coeff_name = coeff_part.split('*', 1)
        assert coeff_name.strip() == f'regular {stat}'
        coeff_value = float(coeff_value)
        coeffs = {'m': coeff_value, 'c': coeff_const}
        linregs[wl][stat] = coeffs
    return linregs


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world levels regression')
    parser.add_argument('wl', choices=['veteran', 'elite'])
    parser.add_argument('vars', nargs='?', choices=['self', 'xp'], default='self')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    linear_regression(args.bits, args.wl, args.vars)


if __name__ == '__main__':
    main(sys.argv[1:])
