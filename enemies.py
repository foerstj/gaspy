import argparse
import sys

from bits.bits import Bits
from bits.templates import Template
from csv import write_csv
from gas.gas_parser import GasParser


class Enemy:
    def __init__(self, template):
        assert isinstance(template, Template)
        self.template = template
        self.template_name = template.name
        self.screen_name: str = template.compute_value('common', 'screen_name')
        self.xp = int(template.compute_value('aspect', 'experience_value') or 0)
        self.life = int(template.compute_value('aspect', 'max_life') or 0)
        self.defense = float(template.compute_value('defend', 'defense') or 0)
        self.h2h_min = int(template.compute_value('attack', 'damage_min') or 0)
        self.h2h_max = int(template.compute_value('attack', 'damage_max') or 0)
        self.melee_lvl = compute_skill_level(template, 'melee')
        self.ranged_lvl = compute_skill_level(template, 'ranged')
        self.magic_lvl = compute_skill_level(template, 'combat_magic')
        self.strength = compute_skill_level(template, 'strength')
        self.dexterity = compute_skill_level(template, 'dexterity')
        self.intelligence = compute_skill_level(template, 'intelligence')
        self.wpn_pref: str = template.compute_value('mind', 'actor_weapon_preference')
        icz_melee = template.compute_value('mind', 'on_enemy_entered_icz_switch_to_melee')
        self.icz_melee = {'true': True, 'false': False}[icz_melee.lower()] if icz_melee else False

    def get_stance(self):
        stance = self.wpn_pref[3:].capitalize()
        if self.icz_melee and stance != 'Melee':
            if self.template.compute_value('inventory', 'selected_active_location'):
                stance = 'Combo'
        return stance

    def has_melee_weapon(self):
        for base_template in self.template.base_templates([self.template]):
            for inventory in base_template.section.get_sections('inventory'):
                for _ in inventory.find_attrs_recursive('es_weapon_hand'):
                    return True
        return False


def load_enemies(bits):
    enemies = bits.templates.get_enemy_templates()
    enemies = [e for n, e in enemies.items() if not (n.startswith('2w_') or n.startswith('3w_'))]
    enemies = [e for e in enemies if 'base' not in e.name]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name]
    enemies = [e for e in enemies if e.screen_name is not None]  # dsx_drake
    enemies = [e for e in enemies if '_reveal' not in e.template_name and '_nis_' not in e.template_name and not e.template_name.startswith('test_')]
    return [Enemy(e) for e in enemies]


def compute_skill_level(template: Template, skill: str) -> int:
    skill_lvl = template.compute_value('actor', 'skills', skill)
    if skill_lvl is None:
        skill_lvl = 0
    else:
        skill_lvl = int(float(skill_lvl.split(',')[0].strip()))  # float e.g. dsx_armor_deadly strength
    return skill_lvl


def make_enemies_csv_line(enemy: Enemy, extended=False) -> list:
    name = enemy.screen_name.strip('"')
    xp = enemy.xp
    life = enemy.life
    defense = int(enemy.defense)
    template_name = enemy.template_name
    stance = enemy.get_stance()
    attacks = []
    if stance == 'Magic' or stance == 'Combo':
        magic_attack = f'(as spell) lvl {enemy.magic_lvl}'
        attacks.append(magic_attack)
    if stance == 'Melee' or stance == 'Combo':
        melee_attack_type = 'h2h' if not enemy.has_melee_weapon() else '(wpn) +'
        melee_attack = f'{melee_attack_type} {enemy.h2h_min}-{enemy.h2h_max} lvl {enemy.melee_lvl}'
        attacks.append(melee_attack)
    if stance == 'Ranged':
        ranged_attack = f'(wpn) + {enemy.h2h_min}-{enemy.h2h_max} lvl {enemy.ranged_lvl}'
        attacks.append(ranged_attack)
    attacks = '\n'.join(attacks)
    csv_line = [name, xp, life, defense, stance, attacks, template_name]
    if extended:
        csv_line.extend([enemy.wpn_pref, enemy.h2h_min, enemy.h2h_max, enemy.melee_lvl, enemy.ranged_lvl, enemy.magic_lvl, enemy.strength, enemy.dexterity, enemy.intelligence])
    return csv_line


# Sth similar to the List of Enemies in the Wiki
def write_enemies_csv(bits: Bits, extended=False):
    enemies = load_enemies(bits)
    if not extended:
        enemies = [e for e in enemies if e.xp]  # enemies with 0 xp aren't included in the wiki either

    enemies.sort(key=lambda e: e.screen_name)
    enemies.sort(key=lambda e: e.xp)

    print('Enemies: ' + str(len(enemies)))
    print([e.template_name for e in enemies])
    csv_header = ['Name', 'XP', 'Life', 'Defense', 'Stance', 'Attacks', 'Template']
    if extended:
        csv_header.extend(['WpnPref', 'h2h min', 'h2h max', 'melee lvl', 'ranged lvl', 'magic lvl', 'strength', 'dexterity', 'intelligence'])
    csv = [csv_header]
    for enemy in enemies:
        csv.append(make_enemies_csv_line(enemy, extended))
    write_csv('enemies-regular', csv)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Enemies')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--extended', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    GasParser.get_instance().print_warnings = False
    bits = Bits(args.bits)
    write_enemies_csv(bits, args.extended)


if __name__ == '__main__':
    main(sys.argv[1:])
