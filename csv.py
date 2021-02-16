import os
import sys

from bits import Bits
from gas_parser import GasParser
from templates import Template


def write_map_csv(map):
    regions = map.get_regions()
    order_file_path = os.path.join('input', map.gas_dir.dir_name + '.txt')
    if os.path.isfile(order_file_path):
        with open(order_file_path) as order_file:
            ordered_regions = [regions[line.strip()] for line in order_file.readlines()]
    else:
        ordered_regions = regions.values()

    level_file_path = os.path.join('input', 'XP Chart.csv')
    with open(level_file_path) as level_file:
        level_xp = [int(line.split(',')[1]) for line in level_file]

    out_file_path = os.path.join('output', map.gas_dir.dir_name + '.csv')
    with open(out_file_path, 'w') as csv_file:
        csv = [['region', 'xp', 'sum', 'level pre', 'level post']]
        xp_sum = 0
        level = 0
        for region in ordered_regions:
            name = region.gas_dir.dir_name
            xp = region.get_xp()
            xp_sum += xp
            pre_level = level
            while level_xp[level + 1] <= xp_sum:
                level += 1
            csv.append([name, xp, xp_sum, pre_level, level])
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


def write_enemies_csv(bits: Bits):
    enemies = bits.templates.get_enemy_templates()
    enemies = [e for n, e in enemies.items() if not (n.startswith('2') or n.startswith('3'))]
    enemies = [Enemy(e) for e in enemies]
    enemies.sort(key=lambda e: e.xp)
    print('Enemies: ' + str(len(enemies)))
    print([e.template_name for e in enemies])
    with open(os.path.join('output', 'enemies-regular.csv'), 'w') as file:
        file.write('Name,XP,Life,Defense,Template\n')
        for enemy in enemies:
            file.write(','.join([enemy.screen_name, str(enemy.xp), str(enemy.life), str(enemy.defense), enemy.template_name]) + '\n')


def main(argv):
    path = argv[0] if len(argv) > 0 else None
    GasParser.get_instance().print_warnings = False
    bits = Bits(path)
    write_maps_csv(bits)
    # write_enemies_csv(bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
