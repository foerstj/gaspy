# Print out which enemies occur in which regions
from bits.bits import Bits
from printouts.common import load_enemies, load_regions_xp


def print_enemy_occurrence(bits: Bits):
    maps = ['map_world', 'multiplayer_world', 'yesterhaven', 'map_expansion', 'dsx_xp']
    maps = {n: bits.maps[n] for n in maps}
    enemies = load_enemies(bits)
    enemy_regions = {e.template_name: list() for e in enemies}
    enemies_by_tn = {e.template_name: e for e in enemies}
    for map_name, m in maps.items():
        print('Map ' + map_name)
        region_xp = load_regions_xp(m, False)
        for rxp in region_xp:
            region = rxp.region
            region_enemies = region.get_enemy_actors()
            region_gen_enemies = region.get_generated_enemies()
            region_enemy_template_names = {e.template_name for e in region_enemies}
            region_enemy_template_names.update(region_gen_enemies.keys())
            region_enemy_strs = [f'{tn} ({enemies_by_tn[tn].xp} XP)' for tn in region_enemy_template_names]
            region_enemies_str = ', '.join(region_enemy_strs)
            print(f'Region {region.get_name()} (lvl {rxp.pre_level} - {rxp.post_level}) contains {len(region_enemy_template_names)} enemy types: ' + region_enemies_str)
            for retn in region_enemy_template_names:
                enemy_regions[retn].append(rxp)
    for enemy in enemies:
        rxps = enemy_regions[enemy.template_name]
        regions_lvls_str = ''
        if len(rxps):
            pre_level = min([rxp.pre_level for rxp in rxps])
            post_level = max([rxp.post_level for rxp in rxps])
            regions_lvls_str = f' lvl {pre_level} - {post_level}'
        region_strs = [f'{rxp.name} (lvl {rxp.pre_level} - {rxp.post_level})' for rxp in rxps]
        regions_str = ', '.join(region_strs)
        print(f'Enemy type {enemy.template_name} ({enemy.xp} XP) occurs in {len(rxps)} regions{regions_lvls_str}: ' + regions_str)
