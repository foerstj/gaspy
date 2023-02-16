import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from printouts.common import load_enemies, Enemy, load_regions_xp, load_level_xp, get_level
from printouts.csv import write_csv
from gas.gas_parser import GasParser
from printouts.enemy_occurrence import print_enemy_occurrence
from printouts.level_enemies import write_level_enemies_csv
from printouts.map_levels import write_map_levels_csv
from printouts.world_level_gold import write_world_level_gold_csv
from printouts.world_level_pcontent import write_world_level_pcontent_csv
from printouts.world_level_shrines import print_world_level_shrines
from printouts.world_level_stats import write_world_level_stats_csv


class EnemyEncounter:
    def __init__(self, enemy: Enemy, xp_at_first_encounter: int, region: Region, level: int):
        self.enemy = enemy
        self.xp_at_first_encounter = xp_at_first_encounter
        self.region = region
        self.level = level


def calc_xp_gradient(bits: Bits, m: Map, world_levels=False) -> dict[str, EnemyEncounter]:
    enemies = load_enemies(bits, True)
    enemies_by_tn: dict[str, Enemy] = {e.template_name: e for e in enemies}
    level_xp = load_level_xp()

    region_xp = load_regions_xp(m, world_levels)
    enemy_encounters = dict()  # dict enemy template name -> encounter data
    for rxp in region_xp:
        region = rxp.region
        region_enemy_gos = region.get_enemy_actors(rxp.world_level)
        region_enemy_template_names_list = [e.template_name.lower() for e in region_enemy_gos]
        region_enemy_template_names = set(region_enemy_template_names_list)
        region_enemy_template_counts = {template_name: 0 for template_name in region_enemy_template_names}
        for template_name in region_enemy_template_names_list:
            region_enemy_template_counts[template_name] += 1
        # let's assume the player does all the least-powerful enemies of the region first, then the next-powerful ones etc.
        region_enemies: list[Enemy] = [enemies_by_tn[template_name] for template_name in region_enemy_template_names]
        region_enemies = sorted(region_enemies, key=lambda x: x.xp)
        region_xp = 0
        for region_enemy in region_enemies:
            if region_enemy.template_name not in enemy_encounters:
                xp_at_first_encounter = int(rxp.xp_pre + region_xp)
                level = get_level(xp_at_first_encounter, level_xp)
                enemy_encounters[region_enemy.template_name] = EnemyEncounter(region_enemy, xp_at_first_encounter, region, level)
            count = region_enemy_template_counts[region_enemy.template_name]
            region_xp += count * region_enemy.xp
        # assert region_xp == rxp.xp, f'{rxp.name}: {region_xp} != {rxp.xp}'  # numbers don't add up because I'm omitting generators for now
    return enemy_encounters


def write_xp_gradient_csv(bits: Bits, m: Map, world_levels=False):
    enemy_encounters = calc_xp_gradient(bits, m, world_levels)

    for template_name, encounter in enemy_encounters.items():
        print(f'Enemy {template_name} ({encounter.enemy.xp} XP)'
              f' is first encountered in region {encounter.region.get_name()}'
              f' with estimated {encounter.xp_at_first_encounter} player XP (level {encounter.level})')

    csv_header = ['Enemy', 'Enemy XP', 'Region', 'Player XP', 'Player level']
    csv = [csv_header]
    for template_name, encounter in enemy_encounters.items():
        csv.append([template_name, encounter.enemy.xp, encounter.region.get_name(), encounter.xp_at_first_encounter, encounter.level])
    write_csv(f'xp gradient {m.get_name()}', csv)


def get_map(bits: Bits, map_name: str) -> Map:
    assert map_name, 'No map name given'
    assert map_name in bits.maps, f'Map {map_name} does not exist'
    return bits.maps[map_name]


def init_arg_parser():
    which_choices = ['level-enemies', 'enemy-occurrence', 'enemies', 'map-levels', 'world-level-shrines', 'world-level-stats', 'world-level-gold', 'world-level-pcontent', 'xp-gradient']
    parser = argparse.ArgumentParser(description='GasPy statistics')
    parser.add_argument('which', choices=which_choices)
    parser.add_argument('--bits', default=None)
    parser.add_argument('--map-name', nargs='?')
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
        # this should basically give a rough overview of the steepness of the difficulty of a map.
        # using player xp/level as player power, and enemy xp as enemy power.
        write_xp_gradient_csv(bits, get_map(bits, args.map_name))
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
