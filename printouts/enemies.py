# Sth similar to the List of Enemies in the Wiki
import argparse
import os
import sys

from arithmetics import eval_expression
from bits.bits import Bits
from bits.templates import Template
from printouts.csv import write_csv
from gas.gas_parser import GasParser


def parse_value(value, default=None, variables: dict = None):
    if value is None:
        return default

    # DS2:
    if '#' in value:
        return eval_expression(value, variables)

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    try:
        return int(value.split()[0])  # dsx_zaurask_commander (missing semicolon)
    except ValueError:
        pass

    assert False, value


# It's not just krug_scavenger's defense - it's also all the 2W and 3W templates
def parse_int_value(value, default=None, variables: dict = None):
    value = parse_value(value, default, variables)
    return int(value) if value is not None else None


def parse_bool_value(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return {'true': True, 'false': False}[value.lower()]
    assert False, value


class Enemy:
    def __init__(self, template: Template, world_level: str):
        self.template = template
        self.world_level = world_level
        is_normal = world_level == 'regular'
        is_veteran = world_level == 'veteran'
        is_elite = world_level == 'elite'
        wl_vars = {'#is_normal': is_normal, '#is_veteran': is_veteran, '#is_elite': is_elite}
        wl_vars = {x: 1 if y else 0 for x, y in wl_vars.items()}
        self.template_name = template.name
        screen_name: str = template.compute_value('common', 'screen_name')
        self.screen_name = screen_name.strip('"') if screen_name is not None else None
        self.monster_level = parse_value(template.compute_value('actor', 'skills', 'monster_level'), 0, wl_vars)  # all this nonsense just for the DS2 arithmetic formulas
        ml_vars = {'#monster_level': self.monster_level}
        ml_vars.update(wl_vars)
        self.xp = parse_value(template.compute_value('aspect', 'experience_value'), 0, ml_vars)
        self.life = parse_int_value(template.compute_value('aspect', 'max_life'), 0, ml_vars)
        self.mana = parse_int_value(template.compute_value('aspect', 'max_mana'), 0, ml_vars)
        self.defense = parse_int_value(template.compute_value('defend', 'defense'), 0, ml_vars)
        self.h2h_min = parse_int_value(template.compute_value('attack', 'damage_min'), 1, ml_vars)
        self.h2h_max = parse_int_value(template.compute_value('attack', 'damage_max'), 1, ml_vars)
        self.cmb_min = parse_int_value(template.compute_value('attack', 'damage_bonus_min_cmagic'), 0)
        self.cmb_max = parse_int_value(template.compute_value('attack', 'damage_bonus_max_cmagic'), 0)
        self.melee_lvl = compute_skill_level(template, 'melee')
        self.ranged_lvl = compute_skill_level(template, 'ranged')
        self.combat_magic_lvl = compute_skill_level(template, 'combat_magic')
        self.nature_magic_lvl = compute_skill_level(template, 'nature_magic')
        self.strength = compute_skill_level(template, 'strength')
        self.dexterity = compute_skill_level(template, 'dexterity')
        self.intelligence = compute_skill_level(template, 'intelligence')
        self.icz_melee = parse_bool_value(template.compute_value('mind', 'on_enemy_entered_icz_switch_to_melee'))
        self.selected_active_location = (template.compute_value('inventory', 'selected_active_location') or 'il_active_melee_weapon').lower()
        self.switches2melee = parse_bool_value(template.compute_value('mind', 'actor_auto_switches_to_melee'))
        self.switches2ranged = parse_bool_value(template.compute_value('mind', 'actor_auto_switches_to_ranged'))
        self.switches2magic = parse_bool_value(template.compute_value('mind', 'actor_auto_switches_to_magic'))
        self.min_speed = parse_value(template.compute_value('body', 'min_move_velocity'), 1)
        self.avg_speed = parse_value(template.compute_value('body', 'avg_move_velocity'), 1)
        self.max_speed = parse_value(template.compute_value('body', 'max_move_velocity'), 1)
        self.speed = self.max_speed or self.avg_speed or self.min_speed
        template_prefix = self.template_name.split('_', 1)[0].lower()
        template_prefixes = ['dsx', 'gpg', 'xp']
        self.template_prefix = template_prefix if template_prefix in template_prefixes else None

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
        return self.selected_active_location in ['il_active_ranged_weapon', 'il_hand_1', 'il_hand_2'] or self.switches2ranged

    def is_magic(self):
        return self.selected_active_location in ['il_active_primary_spell', 'il_active_secondary_spell', 'il_spell_1', 'il_spell_2']

    def cat_speed(self):
        if self.speed < 3:
            return 'slow'
        elif self.speed > 5:
            return 'fast'
        return 'normal'


def load_enemies(bits: Bits, world_level='regular', ds2_wls=False) -> list[Enemy]:
    enemies = bits.templates.get_enemy_templates()
    enemies = list(enemies.values())
    if not ds2_wls:
        wl_prefix = {'regular': None, 'veteran': '2W', 'elite': '3W'}[world_level]
        enemies = [e for e in enemies if e.wl_prefix == wl_prefix]
        # in DS2 mode, templates aren't prefixed; instead, world level is considered when calculating arithmetic formulas for stats
    enemies = [e for e in enemies if 'base' not in e.name]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name]
    enemies = [e for e in enemies if '_reveal' not in e.name and not e.name.endswith('_ar') and not e.name.endswith('_act')]
    enemies = [e for e in enemies if '_nis_' not in e.name and not e.name.startswith('test_')]
    enemies = [Enemy(e, world_level if ds2_wls else None) for e in enemies]
    enemies = [e for e in enemies if e.screen_name is not None]  # dsx_drake
    return enemies


def compute_skill_level(template: Template, skill: str) -> int:
    skill_lvl = template.compute_value('actor', 'skills', skill)
    if skill_lvl is None:
        skill_lvl = 0
    else:
        assert '#' not in skill_lvl
        skill_lvl = int(float(skill_lvl.split(',')[0].strip()))  # float e.g. dsx_armor_deadly strength
    return skill_lvl


def get_enemies(bits: Bits, zero_xp=False, exclude: list[str] = None, world_level='regular', ds2_wls=False):
    enemies = load_enemies(bits, world_level, ds2_wls)
    if not zero_xp:
        enemies = [e for e in enemies if e.xp]  # enemies with 0 xp aren't included in the wiki either
    if exclude:
        enemies = [e for e in enemies if e.template.regular_name not in exclude]

    enemies.sort(key=lambda e: e.template_name)
    enemies.sort(key=lambda e: e.defense if e.defense != 'arithmetic' else -1)
    enemies.sort(key=lambda e: e.life if e.life != 'arithmetic' else -1)
    enemies.sort(key=lambda e: e.xp if e.xp != 'arithmetic' else -1)
    enemies.sort(key=lambda e: e.screen_name.lower())

    print('Enemies: ' + str(len(enemies)))
    print([e.template_name for e in enemies])
    return enemies


def name_file(bits_arg: str, extend=None, world_level='regular'):
    if bits_arg in ['DSLOA', 'DS1', 'DS2', 'DS2BW']:
        bits_seg = f'{bits_arg.lower()}-'
    elif not bits_arg:
        bits_seg = 'dsloa-'
    else:
        bits_seg = ''
    is_extended = extend is not None and len(extend) > 0
    extended_seg = '-x' if is_extended else ''
    return f'enemies-{bits_seg}{world_level}{extended_seg}'


def make_header(extend=None):
    header = ['Name', 'XP', 'Life', 'Armor', 'Stance', 'Attack(s)', 'Template Name']
    if extend is not None:
        if 'h2h' in extend:
            header.extend(['h2h min', 'h2h max'])
        if 'lvl' in extend:
            header.extend(['melee lvl', 'ranged lvl', 'cmagic lvl', 'nmagic lvl'])
        if 'stats' in extend:
            header.extend(['strength', 'dexterity', 'intelligence'])
        if 'mana' in extend:
            header.extend(['mana'])
        if 'wpn' in extend:
            header.extend(['active wpn'])
        if 'speed' in extend:
            header.extend(['min speed', 'avg speed', 'max speed', 'speed', 'speed cat'])
        if 'monster_level' in extend:  # DS2 property
            header.extend(['monster level'])
        if 'src' in extend:
            header.extend(['src'])
    return header


def make_enemies_csv_line(enemy: Enemy, extend=None) -> list:
    name = enemy.screen_name
    xp = enemy.xp
    life = enemy.life
    defense = enemy.defense
    template_name = enemy.template_name
    stance = enemy.get_stance()
    attacks = []
    if enemy.is_magic():
        magic_attack = f'(as spell) lvl {enemy.combat_magic_lvl}'
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
    if extend is not None:
        if 'h2h' in extend:
            csv_line.extend([enemy.h2h_min, enemy.h2h_max])
        if 'lvl' in extend:
            csv_line.extend([enemy.melee_lvl, enemy.ranged_lvl, enemy.combat_magic_lvl, enemy.nature_magic_lvl])
        if 'stats' in extend:
            csv_line.extend([enemy.strength, enemy.dexterity, enemy.intelligence])
        if 'mana' in extend:
            csv_line.extend([enemy.mana])
        if 'wpn' in extend:
            csv_line.extend([enemy.selected_active_location])
        if 'speed' in extend:
            csv_line.extend([enemy.min_speed or None, enemy.avg_speed or None, enemy.max_speed or None, enemy.speed or None, enemy.cat_speed()])
        if 'monster_level' in extend:
            csv_line.extend([enemy.monster_level])
        if 'src' in extend:
            csv_line.extend([enemy.template_prefix])
    return csv_line


def write_enemies_csv(enemies: list[Enemy], file_name: str, extend=None):
    csv_header = make_header(extend)
    csv = [csv_header]
    for enemy in enemies:
        csv.append(make_enemies_csv_line(enemy, extend))
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
    return f'{value:,g}'


def make_enemies_wiki_line(enemy: Enemy, extend=None) -> list:
    name = f'[[{enemy.screen_name}]]'
    xp = format_wiki_number(enemy.xp)
    life = format_wiki_number(enemy.life)
    defense = format_wiki_number(enemy.defense)
    template_name = f'<span style="font-size:67%;">\'\'{enemy.template_name}\'\'</span>'
    stance = enemy.get_stance()
    attacks = []
    if enemy.is_magic():
        magic_damage_bonus = f' + {enemy.cmb_min}-{enemy.cmb_max}' if enemy.cmb_min or enemy.cmb_max else ''
        magic_attack = f'\'\'(as spell)\'\'{magic_damage_bonus} lvl {enemy.combat_magic_lvl}'
        attacks.append(magic_attack)
    if enemy.is_melee():
        melee_attack_type = 'h2h' if not enemy.has_melee_weapon() else '\'\'(wpn)\'\' +'
        melee_damage = f'{enemy.h2h_min}-{enemy.h2h_max}' if enemy.h2h_min or enemy.h2h_max else ''
        melee_attack = f'{melee_attack_type} {melee_damage} lvl {enemy.melee_lvl}'
        attacks.append(melee_attack)
    if enemy.is_ranged():
        ranged_attack = f'\'\'(wpn)\'\' + {enemy.h2h_min}-{enemy.h2h_max} lvl {enemy.ranged_lvl}'
        attacks.append(ranged_attack)
    attacks = '\n'.join(attacks)
    wiki_line = [name, xp, life, defense, stance, attacks, template_name]
    if extend is not None:
        if 'h2h' in extend:
            wiki_line.extend([enemy.h2h_min, enemy.h2h_max])
        if 'lvl' in extend:
            wiki_line.extend([enemy.melee_lvl, enemy.ranged_lvl, enemy.combat_magic_lvl, enemy.nature_magic_lvl])
        if 'stats' in extend:
            wiki_line.extend([enemy.strength, enemy.dexterity, enemy.intelligence])
        if 'mana' in extend:
            wiki_line.extend([format_wiki_number(enemy.mana)])
        if 'wpn' in extend:
            wiki_line.extend([enemy.selected_active_location])
        if 'speed' in extend:
            wiki_line.extend([enemy.min_speed or '', enemy.avg_speed or '', enemy.max_speed or '', enemy.speed or '', enemy.cat_speed()])
        if 'monster_level' in extend:
            wiki_line.extend([f'{enemy.monster_level:g}'])
        if 'src' in extend:
            wiki_line.extend([enemy.template_prefix or ''])
    return wiki_line


def write_enemies_wiki(enemies: list[Enemy], file_name: str, extend=None):
    header = make_header(extend)
    data = []
    for enemy in enemies:
        data.append(make_enemies_wiki_line(enemy, extend))
    write_wiki_table(file_name, header, data)


def write_enemies(bits_path: str, zero_xp=False, exclude=None, world_level='regular', extend=None, output='', ds2_wls=False):
    all_world_levels = ['regular', 'veteran', 'elite']
    if world_level == 'all':
        world_levels = all_world_levels
    else:
        assert world_level in all_world_levels
        world_levels = [world_level]

    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)

    for world_level in world_levels:
        file_name = name_file(bits_path, extend, world_level)
        enemies = get_enemies(bits, zero_xp, exclude, world_level, ds2_wls)
        if output == 'csv':
            write_enemies_csv(enemies, file_name, extend)
        elif output == 'wiki':
            write_enemies_wiki(enemies, file_name, extend)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Enemies')
    parser.add_argument('output', choices=['csv', 'wiki'])
    parser.add_argument('--extend', choices=['h2h', 'lvl', 'stats', 'mana', 'wpn', 'speed', 'monster_level', 'src'], nargs='+')
    parser.add_argument('--zero-xp', action='store_true', help='Include enemies with 0 xp')
    parser.add_argument('--exclude', nargs='+', help='Exclude enemies by (regular) template name')
    parser.add_argument('--world-level', choices=['regular', 'veteran', 'elite', 'all'], default='regular')
    parser.add_argument('--ds2-world-levels', action='store_true', help='DS2 mode for calculating/selecting enemies of the given world-level')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    write_enemies(args.bits, args.zero_xp, args.exclude, args.world_level, args.extend, args.output, args.ds2_world_levels)


if __name__ == '__main__':
    main(sys.argv[1:])
