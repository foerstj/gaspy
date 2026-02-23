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
            print(f'{a}{b} u{u}: {xp} xp -> skill levels {skill_levels}')

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
