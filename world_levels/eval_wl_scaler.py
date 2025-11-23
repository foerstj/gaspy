import argparse
import math

import sys

from bits.bits import Bits
from printouts.common import get_wl_templates
from printouts.world_level_stats import wl_actor_dict
from world_levels.linear_regression import read_linregs_file, read_enemy_occurrence
from world_levels.wl_scaler import SimpleWLInventoryScaler, SimpleWLStatsScaler, CompositeWLScaler, AbstractWLScaler, MultiLinearWLStatsScaler
from world_levels.world_level_templates import STAT_ATTRS


def get_wl_scaler(wl: str, source: str) -> AbstractWLScaler:
    inv_scaler = SimpleWLInventoryScaler(wl)
    linregs = read_linregs_file()
    stats_scaler = SimpleWLStatsScaler(wl) if source == 'code' else SimpleWLStatsScaler(wl, linregs)
    stats_scaler = MultiLinearWLStatsScaler(linregs[wl])
    return CompositeWLScaler(stats_scaler, inv_scaler)


def eval_wl_scaler(bits_path: str, wl: str, source: str):
    bits = Bits(bits_path)

    wl_scaler = get_wl_scaler(wl, source)

    actors = bits.templates.get_enemy_templates()
    wls_actors = get_wl_templates(actors)
    enemy_occurrence = read_enemy_occurrence()

    stats_errors = {stat: list() for stat in STAT_ATTRS}
    for name, wl_actors in wls_actors.items():
        if name not in enemy_occurrence:
            continue
        regular_actor = wl_actors['regular']
        wl_actor = wl_actors[wl]
        if wl_actor is None:
            continue

        regular_stats = wl_actor_dict(regular_actor)
        wl_stats = wl_actor_dict(wl_actor)

        for stat in STAT_ATTRS:
            stat_attr_name = stat.split(':')[-1]
            regular_value = regular_stats[stat_attr_name]
            if regular_value is None:
                continue
            if not regular_value:  # skip zeroes
                continue
            wl_value = wl_stats[stat_attr_name]
            scaler_value = wl_scaler.scale_stat(stat_attr_name, regular_value, regular_stats)
            # scaler_value = wl_value * 1.1
            stats_errors[stat].append(wl_value - scaler_value)

    print()
    for stat in STAT_ATTRS:
        stat_errors = stats_errors[stat]
        stat_errors_squared = [x*x for x in stat_errors]
        mean_squared_error = sum(stat_errors_squared) / len(stat_errors_squared)
        std_error = math.sqrt(mean_squared_error)
        print(f'{stat}: {std_error:.3f} ({len(stat_errors)})')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy eval wl scaler')
    parser.add_argument('wl', choices=['veteran', 'elite'])
    parser.add_argument('--source', choices=['code', 'file'], default='code')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    eval_wl_scaler(args.bits, args.wl, args.source)


if __name__ == '__main__':
    main(sys.argv[1:])
