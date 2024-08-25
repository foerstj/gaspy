from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from printouts.common import Enemy, load_enemies, load_regions_xp
from printouts.csv import write_csv
from printouts.level_xp import load_level_xp, get_level


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

    region_xp = load_regions_xp(m, world_levels, 0 if m.get_name() != 'dsx_xp' else 10)
    enemy_encounters = dict()  # dict enemy template name -> encounter data
    for rxp in region_xp:
        region = rxp.region
        region_enemy_gos = region.get_enemy_actors(rxp.world_level)
        region_enemy_template_names_list = [e.template_name.lower() for e in region_enemy_gos]
        region_enemy_template_names = {n for n in region_enemy_template_names_list if 'nis' not in n.split('_')}
        region_enemy_template_counts = {template_name: 0 for template_name in region_enemy_template_names}
        for template_name in region_enemy_template_names:
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


# this should basically give a rough overview of the steepness of the difficulty of a map.
# using player xp/level as player power, and enemy xp as enemy power.
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
