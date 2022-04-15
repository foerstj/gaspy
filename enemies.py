# Sth similar to the List of Enemies in the Wiki
import argparse
import os
import sys

from bits.bits import Bits
from bits.templates import Template
from csv import write_csv
from gas.gas_parser import GasParser


def parse_value(value, default=0):
    if value is None:
        return default

    # DS2:
    if '#' in value:
        return 'arithmetic'

    try:
        return int(value)
    except:
        pass

    try:
        return float(value)
    except:
        pass

    try:
        return int(value.split()[0])  # dsx_zaurask_commander (missing semicolon)
    except:
        pass

    assert False, value


class Enemy:
    def __init__(self, template: Template):
        self.template = template
        self.template_name = template.name
        screen_name: str = template.compute_value('common', 'screen_name')
        self.screen_name = screen_name.strip('"') if screen_name is not None else None
        self.xp = parse_value(template.compute_value('aspect', 'experience_value'))
        self.life = parse_value(template.compute_value('aspect', 'max_life'))
        self.defense = parse_value(template.compute_value('defend', 'defense'))
        self.h2h_min = parse_value(template.compute_value('attack', 'damage_min'))
        self.h2h_max = parse_value(template.compute_value('attack', 'damage_max'))
        self.melee_lvl = compute_skill_level(template, 'melee')
        self.ranged_lvl = compute_skill_level(template, 'ranged')
        self.magic_lvl = compute_skill_level(template, 'combat_magic')
        self.strength = compute_skill_level(template, 'strength')
        self.dexterity = compute_skill_level(template, 'dexterity')
        self.intelligence = compute_skill_level(template, 'intelligence')
        icz_melee = template.compute_value('mind', 'on_enemy_entered_icz_switch_to_melee')
        self.icz_melee = {'true': True, 'false': False}[icz_melee.lower()] if icz_melee else False
        self.selected_active_location = (template.compute_value('inventory', 'selected_active_location') or 'il_active_melee_weapon').lower()

    def get_stance(self):
        [is_melee, is_ranged, is_magic] = [self.is_melee(), self.is_ranged(), self.is_magic()]
        num_attacks = len([a for a in [is_melee, is_ranged, is_magic] if a])
        assert num_attacks > 0, self.template_name
        if num_attacks > 1:
            return 'Combo'
        elif is_melee:
            return 'Melee'
        elif is_ranged:
            return 'Ranged'
        elif is_magic:
            return 'Magic'

    def has_melee_weapon(self):
        for base_template in self.template.base_templates([self.template]):
            for inventory in base_template.section.get_sections('inventory'):
                for _ in inventory.find_attrs_recursive('es_weapon_hand'):
                    return True
        return False

    def is_melee(self):
        return self.selected_active_location == 'il_active_melee_weapon' or self.icz_melee

    def is_ranged(self):
        return self.selected_active_location == 'il_active_ranged_weapon'

    def is_magic(self):
        return self.selected_active_location == 'il_active_primary_spell' or self.selected_active_location == 'il_active_secondary_spell'


def load_enemies(bits) -> list[Enemy]:
    enemies = bits.templates.get_enemy_templates()
    enemies = [e for n, e in enemies.items() if not (n.startswith('2w_') or n.startswith('3w_'))]
    enemies = [e for e in enemies if 'base' not in e.name]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name]
    enemies = [e for e in enemies if '_reveal' not in e.name and not e.name.endswith('_ar') and not e.name.endswith('_act')]
    enemies = [e for e in enemies if '_nis_' not in e.name and not e.name.startswith('test_')]
    enemies = [Enemy(e) for e in enemies]
    enemies = [e for e in enemies if e.screen_name is not None]  # dsx_drake
    return enemies


def compute_skill_level(template: Template, skill: str) -> int:
    skill_lvl = template.compute_value('actor', 'skills', skill)
    if skill_lvl is None:
        skill_lvl = 0
    else:
        skill_lvl = int(float(skill_lvl.split(',')[0].strip()))  # float e.g. dsx_armor_deadly strength
    return skill_lvl


def get_enemies(bits: Bits, extended=False):
    enemies = load_enemies(bits)
    if not extended:
        enemies = [e for e in enemies if e.xp]  # enemies with 0 xp aren't included in the wiki either

    enemies.sort(key=lambda e: e.xp if e.xp != 'arithmetic' else -1)
    enemies.sort(key=lambda e: e.screen_name.lower())

    print('Enemies: ' + str(len(enemies)))
    print([e.template_name for e in enemies])
    return enemies


def make_enemies_csv_line(enemy: Enemy, extended=False) -> list:
    name = enemy.screen_name
    xp = enemy.xp
    life = enemy.life
    defense = int(enemy.defense)
    template_name = enemy.template_name
    stance = enemy.get_stance()
    attacks = []
    if enemy.is_magic():
        magic_attack = f'(as spell) lvl {enemy.magic_lvl}'
        attacks.append(magic_attack)
    if enemy.is_melee():
        melee_attack_type = 'h2h' if not enemy.has_melee_weapon() else '(wpn) +'
        melee_attack = f'{melee_attack_type} {enemy.h2h_min}-{enemy.h2h_max} lvl {enemy.melee_lvl}'
        attacks.append(melee_attack)
    if enemy.is_ranged():
        ranged_attack = f'(wpn) + {enemy.h2h_min}-{enemy.h2h_max} lvl {enemy.ranged_lvl}'
        attacks.append(ranged_attack)
    attacks = '\n'.join(attacks)
    csv_line = [name, xp, life, defense, stance, attacks, template_name]
    if extended:
        csv_line.extend([enemy.h2h_min, enemy.h2h_max, enemy.melee_lvl, enemy.ranged_lvl, enemy.magic_lvl, enemy.strength, enemy.dexterity, enemy.intelligence, enemy.selected_active_location])
    return csv_line


def name_file(bits_arg: str, extended=False, world_level='regular'):
    if bits_arg in ['DSLOA', 'DS1', 'DS2']:
        bits_seg = f'{bits_arg.lower()}-'
    elif not bits_arg:
        bits_seg = 'dsloa-'
    else:
        bits_seg = ''
    extended_seg = '-x' if extended else ''
    return f'enemies-{bits_seg}{world_level}{extended_seg}'


def write_enemies_csv(file_name: str, bits: Bits, extended=False):
    enemies = get_enemies(bits, extended)
    csv_header = ['Name', 'XP', 'Life', 'Armor', 'Stance', 'Attack(s)', 'Template Name']
    if extended:
        csv_header.extend(['h2h min', 'h2h max', 'melee lvl', 'ranged lvl', 'magic lvl', 'strength', 'dexterity', 'intelligence', 'active wpn'])
    csv = [csv_header]
    for enemy in enemies:
        csv.append(make_enemies_csv_line(enemy, extended))
    write_csv(file_name, csv)


def strval(x):
    x = str(x)
    x = x.replace('\n', '<br/>')
    return x


def write_wiki_table(name: str, header: list, data: list[list]):
    out_file_path = os.path.join('output', f'{name}.wiki.txt')
    lines = [
        '{|class="wikitable sortable highlight" style="width: 100%; text-align: center"'
    ]
    for h in header:
        lines.append(f'! {h}')
    for d in data:
        lines.append('|-')
        lines.append('| ' + ' || '.join([strval(x) for x in d]))
    lines.append('|}')
    with open(out_file_path, 'w') as wiki_file:
        wiki_file.writelines([line + '\n' for line in lines])
    print(f'wrote {out_file_path}')


def format_wiki_number(value):
    return f'{value:,}' if value != 'arithmetic' else "''arithmetic''"


def make_enemies_wiki_line(enemy: Enemy, extended=False) -> list:
    name = f'[[{enemy.screen_name}]]'
    xp = format_wiki_number(enemy.xp)
    life = format_wiki_number(enemy.life)
    defense = format_wiki_number(enemy.defense)
    template_name = f'<span style="font-size:67%;">\'\'{enemy.template_name}\'\'</span>'
    stance = enemy.get_stance()
    attacks = []
    if enemy.is_magic():
        magic_attack = f'\'\'(as spell)\'\' lvl {enemy.magic_lvl}'
        attacks.append(magic_attack)
    if enemy.is_melee():
        melee_attack_type = 'h2h' if not enemy.has_melee_weapon() else '\'\'(wpn)\'\' +'
        melee_attack = f'{melee_attack_type} {enemy.h2h_min}-{enemy.h2h_max} lvl {enemy.melee_lvl}'
        attacks.append(melee_attack)
    if enemy.is_ranged():
        ranged_attack = f'\'\'(wpn)\'\' + {enemy.h2h_min}-{enemy.h2h_max} lvl {enemy.ranged_lvl}'
        attacks.append(ranged_attack)
    attacks = '\n'.join(attacks)
    csv_line = [name, xp, life, defense, stance, attacks, template_name]
    if extended:
        csv_line.extend([enemy.h2h_min, enemy.h2h_max, enemy.melee_lvl, enemy.ranged_lvl, enemy.magic_lvl, enemy.strength, enemy.dexterity, enemy.intelligence, enemy.selected_active_location])
    return csv_line


def write_enemies_wiki(file_name: str, bits: Bits, extended=False):
    enemies = get_enemies(bits, extended)
    header = ['Name', 'XP', 'Life', 'Armor', 'Stance', 'Attack(s)', 'Template Name']
    if extended:
        header.extend(['h2h min', 'h2h max', 'melee lvl', 'ranged lvl', 'magic lvl', 'strength', 'dexterity', 'intelligence', 'active wpn'])
    data = []
    for enemy in enemies:
        data.append(make_enemies_wiki_line(enemy, extended))
    write_wiki_table(file_name, header, data)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Enemies')
    parser.add_argument('output', choices=['csv', 'wiki'])
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
    file_name = name_file(args.bits, args.extended)
    if args.output == 'csv':
        write_enemies_csv(file_name, bits, args.extended)
    elif args.output == 'wiki':
        write_enemies_wiki(file_name, bits, args.extended)


if __name__ == '__main__':
    main(sys.argv[1:])
