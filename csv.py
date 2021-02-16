import os
import sys

from bits import Bits
from gas_parser import GasParser
from templates import Template


def load_level_xp():
    level_file_path = os.path.join('input', 'XP Chart.csv')
    with open(level_file_path) as level_file:
        level_xp = [int(line.split(',')[1]) for line in level_file]
    return level_xp


def load_ordered_regions(map):
    regions = map.get_regions()
    order_file_path = os.path.join('input', map.gas_dir.dir_name + '.txt')
    if os.path.isfile(order_file_path):
        with open(order_file_path) as order_file:
            ordered_regions = [regions[line.strip()] for line in order_file.readlines()]
    else:
        ordered_regions = regions.values()
    return ordered_regions


def get_level(xp, level_xp):
    level = 0
    while level_xp[level + 1] <= xp:
        level += 1
    return level


class RegionXP:
    def __init__(self, region):
        self.region = region
        self.name = region.gas_dir.dir_name
        self.xp = region.get_xp()
        self.xp_pre = None
        self.xp_post = None
        self.pre_level = None
        self.post_level = None

    def set_pre_xp(self, pre_xp, level_xp):
        self.xp_pre = pre_xp
        self.xp_post = pre_xp + self.xp
        self.pre_level = get_level(pre_xp, level_xp)
        self.post_level = get_level(self.xp_post, level_xp)
        return self.xp_post


def load_region_xp(map):
    ordered_regions = load_ordered_regions(map)
    level_xp = load_level_xp()
    regions_xp = [RegionXP(r) for r in ordered_regions]
    xp = 0
    for rx in regions_xp:
        xp = rx.set_pre_xp(xp, level_xp)
    return regions_xp


def write_map_csv(map):
    regions_xp = load_region_xp(map)
    out_file_path = os.path.join('output', map.gas_dir.dir_name + '.csv')
    with open(out_file_path, 'w') as csv_file:
        csv = [['region', 'xp', 'sum', 'level pre', 'level post']]
        for r in regions_xp:
            csv.append([r.name, r.xp, r.xp_post, r.pre_level, r.post_level])
        csv_file.writelines([','.join([str(x) for x in y]) + '\n' for y in csv])


def write_maps_csv(bits: Bits):
    maps = bits.maps
    print('Maps: ' + str(len(maps)))
    for map in maps.values():
        print(map.get_screen_name())
        write_map_csv(map)


class Enemy:
    def __init__(self, template):
        assert isinstance(template, Template)
        self.template = template
        self.template_name = template.name
        self.screen_name = template.compute_value('common', 'screen_name') or ''
        self.xp = int(template.compute_value('aspect', 'experience_value') or '0')
        self.life = int(template.compute_value('aspect', 'max_life') or '0')
        self.defense = float(template.compute_value('defend', 'defense') or '0')


def load_enemies(bits):
    enemies = bits.templates.get_enemy_templates()
    enemies = [e for n, e in enemies.items() if not (n.startswith('2') or n.startswith('3'))]
    enemies = [Enemy(e) for e in enemies]
    return enemies


def write_enemies_csv(bits: Bits):
    enemies = load_enemies(bits)
    enemies.sort(key=lambda e: e.xp)
    print('Enemies: ' + str(len(enemies)))
    print([e.template_name for e in enemies])
    with open(os.path.join('output', 'enemies-regular.csv'), 'w') as file:
        file.write('Name,XP,Life,Defense,Template\n')
        for enemy in enemies:
            file.write(','.join([enemy.screen_name, str(enemy.xp), str(enemy.life), str(enemy.defense), enemy.template_name]) + '\n')


def enemy_occurrence(bits: Bits):
    maps = ['map_world', 'multiplayer_world', 'map_expansion']
    maps = {n: bits.maps[n] for n in maps}
    enemies = load_enemies(bits)
    enemy_regions = {e.template_name: list() for e in enemies}
    enemies_by_tn = {e.template_name: e for e in enemies}
    for map_name, map in maps.items():
        print('Map ' + map_name)
        region_xp = load_region_xp(map)
        for rxp in region_xp:
            region = rxp.region
            region_enemies = region.get_enemies()
            region_enemy_template_names = {e.template_name for e in region_enemies}
            region_enemy_strs = [tn + ' ('+str(enemies_by_tn[tn].xp)+' XP)' for tn in region_enemy_template_names]
            region_enemies_str = str(len(region_enemy_template_names)) + ' enemy types: ' + ', '.join(region_enemy_strs)
            print('Region ' + region.get_name() + ' (XP '+str(rxp.xp_pre)+' - '+str(rxp.xp_post)+') contains ' + region_enemies_str)
            for retn in region_enemy_template_names:
                enemy_regions[retn].append(rxp)
    for enemy in enemies:
        rxps = enemy_regions[enemy.template_name]
        region_strs = [rxp.name + ' (XP '+str(rxp.xp_pre)+' - '+str(rxp.xp_post)+')' for rxp in rxps]
        regions_str = str(len(rxps)) + ' regions: ' + ', '.join(region_strs)
        print('Enemy type ' + enemy.template_name + ' (' + str(enemy.xp) + ' XP) occurs in ' + regions_str)


def main(argv):
    path = argv[0] if len(argv) > 0 else None
    GasParser.get_instance().print_warnings = False
    bits = Bits(path)
    enemy_occurrence(bits)
    # write_maps_csv(bits)
    # write_enemies_csv(bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
