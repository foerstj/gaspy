import argparse

import sys

from bits.bits import Bits
from gas.gas_parser import GasParser
from printouts.common import parse_bool_value


def frags(bits_path: str):
    bits = Bits(bits_path)
    GasParser.get_instance().print_warnings = False
    bits.templates.get_templates()

    enemies = bits.templates.get_enemy_templates()
    for enemy in enemies.values():
        if enemy.wl_prefix is not None:
            continue
        gib_gore_good = parse_bool_value(enemy.compute_value('physics', 'gib_gore_good'))
        ewk_str = enemy.compute_value('physics', 'explode_when_killed')
        explode_when_killed = False if ewk_str is None else parse_bool_value(ewk_str.split()[0])
        if not gib_gore_good and not explode_when_killed:
            continue
        break_particulate = enemy.resolve_section('physics', 'break_particulate')
        if break_particulate is None:
            continue
        frag_names = [a.name for a in break_particulate.get_attrs()]
        frag_names_str = ', '.join(frag_names)
        print(f'{enemy.name}: {gib_gore_good} {explode_when_killed}; {frag_names_str}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Frags')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    frags(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
