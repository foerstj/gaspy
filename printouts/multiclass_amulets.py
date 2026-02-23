import argparse
import sys

from printouts.csv import write_csv_dict
from printouts.level_xp import load_level_xp, get_level

MULTICLASSES = [
    ('m', 'r'),
    ('m', 'n'),
    ('m', 'c'),
    ('r', 'n'),
    ('r', 'c')
]
SKILL_STAT = {
    'm': 'str',
    'r': 'dex',
    'n': 'int',
    'c': 'int',
}
STAT_GAINS = {
    'm': {'str': 0.64, 'dex': 0.27, 'int': 0.09},
    'r': {'str': 0.25, 'dex': 0.62, 'int': 0.13},
    'n': {'str': 0.09, 'dex': 0.18, 'int': 0.73},
    'c': {'str': 0.13, 'dex': 0.17, 'int': 0.70},
}


def get_stats_at_skill_level(skill: str, level: int):
    stat_gain = STAT_GAINS[skill]
    return {s: g*level for s, g in stat_gain.items()}


class MulticlassAmulet:
    def __init__(self, skill_a, skill_b, uber, req_a, req_b, req_str, req_dex, req_int, add_str, add_dex, add_int):
        self.skill_a = skill_a
        self.skill_b = skill_b
        self.uber = uber
        self.req_a = req_a
        self.req_b = req_b
        self.req_str = req_str
        self.req_dex = req_dex
        self.req_int = req_int
        self.add_str = add_str
        self.add_dex = add_dex
        self.add_int = add_int

    def to_csv_line(self):
        return self.__dict__


def calc_multiclass_amulets():
    level_xp = load_level_xp()
    for a, b in MULTICLASSES:
        for u in range(10, 70, 10):
            xp = level_xp[u]
            skill_levels = get_level(int(xp/2), level_xp)
            stat_gains_a = get_stats_at_skill_level(a, u)
            stat_gains_b = get_stats_at_skill_level(b, u)
            stat_gains = {stat: (stat_gains_a[stat] + stat_gains_b[stat])/2 for stat in stat_gains_a}
            stat_reqs = {stat: 10+gains for stat, gains in stat_gains.items()}
            stat_gains_single_a = get_stats_at_skill_level(a, skill_levels)
            stat_gains_single_b = get_stats_at_skill_level(b, skill_levels)
            stat_gains_single = {stat: max(stat_gains_single_a[stat], stat_gains_single_b[stat]) for stat in stat_gains_a}
            stat_gaps = {stat: stat_gains_single[stat] - stat_gains[stat] for stat in stat_gains}
            stat_adds = {stat: stat_gaps[stat] if stat_gaps[stat] > 0 else None for stat in stat_gaps}
            print(f'{a}{b} u{u}: {xp} xp -> skill levels {skill_levels}')
            print(f'  stat reqs {stat_reqs}')
            print(f'  stat gaps {stat_gaps}')
            print(f'  stat adds {stat_adds}')

    return [
        MulticlassAmulet('m', 'n', 20, 15, 15, 17, None, 18, 2.3, None, 2.75),
        MulticlassAmulet('m', 'n', 50, 45, 45, 28, None, 30, 10.55, None, 12.35),
    ]


def make_amulets_csv(amulets: list[MulticlassAmulet]):
    keys = ['skill_a', 'skill_b', 'uber', 'req_a', 'req_b', 'req_str', 'req_dex', 'req_int', 'add_str', 'add_dex', 'add_int']
    headers = {x: x for x in keys}
    data = [a.to_csv_line() for a in amulets]
    return keys, headers, data


def multiclass_amulets():
    amulets = calc_multiclass_amulets()
    amulets_csv = make_amulets_csv(amulets)
    write_csv_dict('multiclass-amulets', *amulets_csv, sep=';', quote_cells=False)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Multiclass Amulets')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    multiclass_amulets()


if __name__ == '__main__':
    main(sys.argv[1:])
