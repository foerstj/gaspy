import os
import sys

from gas_dir import GasDir
from gas_dir_handler import GasDirHandler
from map import Map
from templates import Templates, Template


class Bits(GasDirHandler):
    def __init__(self, path=None):
        if path is None:
            path = os.path.join(os.path.expanduser("~"), 'Documents', 'Dungeon Siege LoA', 'Bits')
        assert os.path.isdir(path)
        super().__init__(GasDir(path))
        self.templates = self.init_templates()
        self.maps = self.init_maps()

    def init_maps(self):
        maps_dir = self.gas_dir.get_subdir(['world', 'maps'])
        map_dirs = maps_dir.get_subdirs() if maps_dir is not None else {}
        return {name: Map(map_dir, self) for name, map_dir in map_dirs.items()}

    def init_templates(self):
        templates_dir = self.gas_dir.get_subdir(['world', 'contentdb', 'templates'])
        return Templates(templates_dir)


def print_maps(bits: Bits):
    maps = bits.maps
    print('Maps: ' + str(len(maps)))
    for map in maps.values():
        # map.print('xp')
        map.write_csv()


def print_templates(bits: Bits):
    templates = bits.templates.get_templates()
    print('Templates: ' + str(len(templates)))
    for template in templates.values():
        template.print('children')


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
    with open(os.path.join('output', 'enemies-regular.csv'), 'w') as file:
        file.write('Name,XP,Life,Defense,Template\n')
        for enemy in enemies:
            file.write(','.join([enemy.screen_name, str(enemy.xp), str(enemy.life), str(enemy.defense), enemy.template_name]) + '\n')


def main(argv):
    path = argv[0] if len(argv) > 0 else None
    bits = Bits(path)
    # print_maps(bits)
    # print_templates(bits)
    write_enemies_csv(bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
