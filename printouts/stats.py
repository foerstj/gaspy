import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from gas.gas_parser import GasParser
from printouts.enemy_attacks import write_enemy_attacks_csv
from printouts.enemy_occurrence import print_enemy_occurrence
from printouts.level_enemies import write_level_enemies_csv
from printouts.map_levels import write_map_levels_csv
from printouts.spells import write_spells_csv
from printouts.world_level_gold import write_world_level_gold_csv
from printouts.world_level_pcontent import write_world_level_pcontent_csv
from printouts.world_level_shrines import print_world_level_shrines
from printouts.world_level_stats import write_world_level_stats_csv
from printouts.xp_gradient import write_xp_gradient_csv


def get_map(bits: Bits, map_name: str) -> Map:
    assert map_name, 'No map name given'
    assert map_name in bits.maps, f'Map {map_name} does not exist'
    return bits.maps[map_name]


def init_arg_parser():
    which_choices = [
        'level-enemies',
        'enemy-occurrence',
        'map-levels',
        'world-level-shrines',
        'world-level-stats',
        'world-level-gold',
        'world-level-pcontent',
        'xp-gradient',
        'spells',
        'enemy-attacks',
    ]
    parser = argparse.ArgumentParser(description='GasPy statistics')
    parser.add_argument('which', choices=which_choices)
    parser.add_argument('--bits', default=None)
    parser.add_argument('--map-name', nargs='?')  # for map-specific printouts
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    GasParser.get_instance().print_warnings = False
    bits = Bits(args.bits)
    which = args.which
    if which == 'level-enemies':
        write_level_enemies_csv(bits)
    elif which == 'enemy-occurrence':
        print_enemy_occurrence(bits)
    elif which == 'map-levels':
        write_map_levels_csv(get_map(bits, args.map_name))
    elif which == 'world-level-shrines':
        print_world_level_shrines(get_map(bits, args.map_name))
    elif which == 'world-level-stats':
        write_world_level_stats_csv(bits)
    elif which == 'world-level-gold':
        write_world_level_gold_csv(bits)
    elif which == 'world-level-pcontent':
        write_world_level_pcontent_csv(bits)
    elif which == 'xp-gradient':
        write_xp_gradient_csv(bits, get_map(bits, args.map_name))
    elif which == 'spells':
        write_spells_csv(bits)
    elif which == 'enemy-attacks':
        write_enemy_attacks_csv(bits)
    else:
        assert False, f'unexpected argument: {which}'
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
