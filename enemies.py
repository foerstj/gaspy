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
        self.xp = int(template.compute_value('aspect', 'experience_value') or '0')
        self.life = int(template.compute_value('aspect', 'max_life') or '0')
        self.defense = float(template.compute_value('defend', 'defense') or '0')


def load_enemies(bits):
    enemies = bits.templates.get_enemy_templates()
    enemies = [e for n, e in enemies.items() if not (n.startswith('2w_') or n.startswith('3w_'))]
    enemies = [e for e in enemies if 'base' not in e.name]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name]
    enemies = [Enemy(e) for e in enemies]
    return enemies


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
    wpn_pref: str = enemy.template.compute_value('mind', 'actor_weapon_preference')
    icz_melee = enemy.template.compute_value('mind', 'on_enemy_entered_icz_switch_to_melee')
    icz_melee = {'true': True, 'false': False}[icz_melee.lower()] if icz_melee else False
    stance = wpn_pref[3:].capitalize()
    if icz_melee and stance != 'Melee':
        if enemy.template.compute_value('inventory', 'selected_active_location'):
            stance = 'Combo'
    attacks = []
    h2h_min = enemy.template.compute_value('attack', 'damage_min') or 0
    h2h_max = enemy.template.compute_value('attack', 'damage_max') or 0
    melee_lvl = compute_skill_level(enemy.template, 'melee')
    ranged_lvl = compute_skill_level(enemy.template, 'ranged')
    magic_lvl = compute_skill_level(enemy.template, 'combat_magic')
    if stance == 'Magic' or stance == 'Combo':
        magic_attack = f'(as spell) lvl {magic_lvl}'
        attacks.append(magic_attack)
    if stance == 'Melee' or stance == 'Combo':
        melee_attack_type = 'h2h'
        for base_template in enemy.template.base_templates([enemy.template]):
            for inventory in base_template.section.get_sections('inventory'):
                for _ in inventory.find_attrs_recursive('es_weapon_hand'):
                    melee_attack_type = '(wpn) +'
        melee_attack = f'{melee_attack_type} {h2h_min}-{h2h_max} lvl {melee_lvl}'
        attacks.append(melee_attack)
    if stance == 'Ranged':
        ranged_attack = f'(wpn) + {h2h_min}-{h2h_max} lvl {ranged_lvl}'
        attacks.append(ranged_attack)
    attacks = '\n'.join(attacks)
    csv_line = [name, xp, life, defense, stance, attacks, template_name]
    if extended:
        strength = compute_skill_level(enemy.template, 'strength')
        dexterity = compute_skill_level(enemy.template, 'dexterity')
        intelligence = compute_skill_level(enemy.template, 'intelligence')
        csv_line.extend([wpn_pref, h2h_min, h2h_max, melee_lvl, ranged_lvl, magic_lvl, strength, dexterity, intelligence])
    return csv_line


# Sth similar to the List of Enemies in the Wiki
def write_enemies_csv(bits: Bits, extended=False):
    enemies = load_enemies(bits)

    enemies = [e for e in enemies if e.screen_name is not None]  # dsx_drake
    enemies = [e for e in enemies if '_reveal' not in e.template_name and '_nis_' not in e.template_name and not e.template_name.startswith('test_')]
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
