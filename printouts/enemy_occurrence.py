# Print out which enemies occur in which regions
import argparse

import sys

from bits.bits import Bits
from bits.maps.map import Map
from gas.gas_parser import GasParser
from printouts.common import load_enemies, load_regions_xp, Enemy, RegionXP
from printouts.csv import write_csv_dict


def get_enemy_template_main_name(template_name: str) -> str:
    name_segs = template_name.split('_')
    redundant_segs = ['reveal', 'ar', 'act']
    for redundant_seg in redundant_segs:
        if redundant_seg in name_segs:
            index = name_segs.index(redundant_seg)
            name_segs = name_segs[:index]  # cut off everything behind redundant segment, looking at you skeleton_mercenary_reveal_02
    return '_'.join(name_segs)


def load_enemies_main(bits: Bits) -> dict[str, Enemy]:
    enemies = load_enemies(bits)
    enemies_by_tn: dict[str, Enemy] = {e.template_name: e for e in enemies}
    for etn in list(enemies_by_tn.keys()):
        etn_main = get_enemy_template_main_name(etn)
        if etn_main != etn:
            if etn_main not in enemies_by_tn:
                # how could they
                print(f'Note: not de-duplicating redundant template {etn} because main template does not exist')
                continue
            if enemies_by_tn[etn].xp != enemies_by_tn[etn_main].xp:
                # how could they
                print(f'Note: de-duplicating redundant template {etn} even tho XP differs')
            del enemies_by_tn[etn]
    print(f'Loaded {len(enemies_by_tn)} de-duplicated enemies')
    return enemies_by_tn


class EnemyOccurrence:
    def __init__(self, enemy: Enemy, regions_xp: list[RegionXP], count: int):
        self.enemy = enemy
        self.regions_xp = regions_xp
        self.count = count

    @property
    def occurs(self) -> bool:
        return len(self.regions_xp) > 0

    @property
    def min_pre_level(self):
        return min([rxp.pre_level for rxp in self.regions_xp]) if self.occurs else None

    @property
    def max_post_level(self):
        return max([rxp.post_level for rxp in self.regions_xp]) if self.occurs else None


def load_enemy_occurrence_region(rxp: RegionXP, enemies_by_tn: dict[str, Enemy]) -> dict[str, EnemyOccurrence]:
    region = rxp.region
    enemy_regions = {etn: list() for etn in enemies_by_tn}

    region_enemies = region.get_enemy_actors()
    region_gen_enemies = region.get_generated_enemies()
    region_enemy_template_names = {e.template_name for e in region_enemies}
    region_enemy_template_names.update(region_gen_enemies.keys())

    enemy_counts: dict[str, int] = {tn: 0 for tn in region_enemy_template_names}
    for enemy in region_enemies:
        enemy_counts[enemy.template_name] += 1
    for tn, gen_enemy in region_gen_enemies.items():
        enemy_counts[tn] += gen_enemy[0]

    for retn in list(region_enemy_template_names):
        retn_main = get_enemy_template_main_name(retn)
        if retn_main != retn and retn not in enemies_by_tn and retn_main in enemies_by_tn:
            region_enemy_template_names.discard(retn)
            region_enemy_template_names.add(retn_main)

            if retn_main not in enemy_counts:
                enemy_counts[retn_main] = 0
            enemy_counts[retn_main] += enemy_counts[retn]
            del enemy_counts[retn]
    region_enemy_template_names = {x for x in region_enemy_template_names if x in enemies_by_tn}  # filter out dsx_shadow_bigboss_nis_staff

    region_enemy_strs = [f'{tn} ({enemies_by_tn[tn].xp} XP)' for tn in region_enemy_template_names]
    region_enemies_str = ', '.join(region_enemy_strs)
    print(f'Region {region.get_name()} (lvl {rxp.pre_level} - {rxp.post_level}) contains {len(region_enemy_template_names)} enemy types: ' + region_enemies_str)
    for retn in region_enemy_template_names:
        enemy_regions[retn].append(rxp)

    occurrences = {tn: EnemyOccurrence(enemy, enemy_regions[tn], enemy_counts.get(tn) or 0) for tn, enemy in enemies_by_tn.items()}
    return occurrences


def load_enemy_occurrence_map(m: Map, enemies_by_tn: dict[str, Enemy]) -> dict[str, EnemyOccurrence]:
    print()
    print('Map ' + m.get_name())
    region_xp = load_regions_xp(m, False, 0 if m.get_name() != 'dsx_xp' else 10)

    occurrences: dict[str, EnemyOccurrence] = dict()
    for rxp in region_xp:
        region_occurrences = load_enemy_occurrence_region(rxp, enemies_by_tn)

        for tn, region_occurrence in region_occurrences.items():
            if tn not in occurrences:
                occurrences[tn] = region_occurrence
            else:
                occurrences[tn].regions_xp.extend(region_occurrence.regions_xp)
                occurrences[tn].count += region_occurrence.count

    return occurrences


def load_enemy_occurrence(bits: Bits) -> dict[str, EnemyOccurrence]:
    maps = ['map_world', 'multiplayer_world', 'yesterhaven', 'map_expansion', 'dsx_xp']
    maps = {n: bits.maps[n] for n in maps}

    enemies_by_tn = load_enemies_main(bits)

    occurrences: dict[str, EnemyOccurrence] = dict()
    for map_name, m in maps.items():
        map_occurrences = load_enemy_occurrence_map(m, enemies_by_tn)
        for tn, map_occurrence in map_occurrences.items():
            if tn not in occurrences:
                occurrences[tn] = map_occurrence
            else:
                occurrences[tn].regions_xp.extend(map_occurrence.regions_xp)
                occurrences[tn].count += map_occurrence.count

    return occurrences


def do_print_enemy_occurrence(occurrences: dict[str, EnemyOccurrence]):
    with open('output/Enemy Occurrence.txt', 'w') as output_file:
        for template_name, occurrence in occurrences.items():
            rxps = occurrence.regions_xp
            regions_lvls_str = f' lvl {occurrence.min_pre_level} - {occurrence.max_post_level}' if occurrence.occurs else ''
            region_strs = [f'{rxp.name} (lvl {rxp.pre_level} - {rxp.post_level})' for rxp in rxps]
            regions_str = ', '.join(region_strs)
            line = f'Enemy type {template_name} ({occurrence.enemy.xp} XP) occurs in {len(rxps)} regions{regions_lvls_str}: ' + regions_str
            print(line)
            output_file.write(line + '\n')


def print_enemy_occurrence(bits: Bits):
    occurrences = load_enemy_occurrence(bits)
    print()
    do_print_enemy_occurrence(occurrences)


def make_occurrence_csv_line(occurrence: EnemyOccurrence) -> dict:
    return {
        'template': occurrence.enemy.template_name,
        'xp': occurrence.enemy.xp,
        'count': occurrence.count,
        'num regions': len(occurrence.regions_xp),
        'start lvl': occurrence.min_pre_level,
        'end lvl': occurrence.max_post_level,
        'life': occurrence.enemy.life,
        'mana': occurrence.enemy.mana,
        'defense': occurrence.enemy.defense,
        'melee': occurrence.enemy.melee_lvl,
        'ranged': occurrence.enemy.ranged_lvl,
        'cmagic': occurrence.enemy.combat_magic_lvl,
        'nmagic': occurrence.enemy.nature_magic_lvl,
        'str': occurrence.enemy.strength,
        'dex': occurrence.enemy.dexterity,
        'int': occurrence.enemy.intelligence,
    }


def do_write_enemy_occurrence_csv(occurrences: dict[str, EnemyOccurrence]):
    keys = ['template', 'xp', 'count', 'num regions', 'start lvl', 'end lvl', 'life', 'mana', 'defense', 'melee', 'ranged', 'cmagic', 'nmagic', 'str', 'dex', 'int']
    header_dict = {x: x for x in keys}  # pff
    data_dicts = [make_occurrence_csv_line(occurrence) for occurrence in occurrences.values()]
    write_csv_dict('Enemy Occurrence', keys, header_dict, data_dicts)


def write_enemy_occurrence_csv(bits: Bits):
    occurrences = load_enemy_occurrence(bits)
    print()
    do_write_enemy_occurrence_csv(occurrences)


def enemy_occurrence(bits_path, output):
    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)
    if output == 'txt':
        print_enemy_occurrence(bits)
    elif output == 'csv':
        write_enemy_occurrence_csv(bits)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy enemy_occurrence')
    parser.add_argument('--output', choices=['txt', 'csv'], default='txt')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    enemy_occurrence(args.bits, args.output)


if __name__ == '__main__':
    main(sys.argv[1:])
