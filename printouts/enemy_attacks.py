from bits.bits import Bits
from bits.templates import Template
from gas.gas import Attribute
from printouts.common import load_enemies, Enemy, is_shield, parse_int_value, SPELL_ATTR_NAMES
from printouts.csv import write_csv_dict
from printouts.spells import Spell


class EnemyAttack:
    def __init__(self, enemy: Enemy, bits: Bits, stance: str, selected_spell: Template = None):
        self.enemy = enemy
        self.bits = bits
        self.stance = stance
        self.selected_spell = selected_spell
        self.base_dmg_min = None if stance != 'Melee' else parse_int_value(enemy.template.compute_value('attack', 'damage_min'))
        self.base_dmg_max = None if stance != 'Melee' else parse_int_value(enemy.template.compute_value('attack', 'damage_max'))
        self.weapon = selected_spell.name if selected_spell else self.get_wpn()
        self.wpn_dmg_min, self.wpn_dmg_max = self.get_wpn_dmg()
        if selected_spell:
            dyn_dmg_min = selected_spell.compute_value('magic', 'attack_damage_modifier_min')
            self.wpn_dmg_min = parse_int_value(selected_spell.compute_value('attack', 'damage_min')) if not dyn_dmg_min else '?'
            dyn_dmg_max = selected_spell.compute_value('magic', 'attack_damage_modifier_max')
            self.wpn_dmg_max = parse_int_value(selected_spell.compute_value('attack', 'damage_max')) if not dyn_dmg_max else '?'
        self.spell_component = None
        if selected_spell:
            spell_info = Spell.read_template(selected_spell)
            self.spell_component = spell_info.spell_component
        # TODO: spell's effect name, damage type, hit type (via class Spell)
        # TODO: same for miniguns
        # TODO: melee hit_multiple
        # TODO: suicide attacks (Proxo)
        # TODO: attack duration, multi-hit anims

    def get_wpn_dmg(self):
        if self.stance == 'Melee':
            return self.get_melee_wpn_dmg()
        if self.stance == 'Ranged':
            return self.get_ranged_wpn_dmg()
        return [None, None]

    def get_wpn(self):
        if self.stance == 'Melee':
            return self.get_melee_wpn()
        if self.stance == 'Ranged':
            return self.get_ranged_wpn()
        return None

    @classmethod
    def get_generic_wpn(cls, weapon_values):
        if len(weapon_values) > 1:
            return '?'
        if len(weapon_values) == 0:
            return None
        weapon_value = weapon_values[0]
        if weapon_value.startswith('#'):
            return '?'
        return weapon_value

    def get_melee_wpn(self):
        weapon_values = get_equipment('es_weapon_hand', self.enemy.template)
        return self.get_generic_wpn(weapon_values)

    def get_ranged_wpn(self):
        weapon_values = get_equipment('es_shield_hand', self.enemy.template)
        weapon_values = [v for v in weapon_values if not is_shield(v)]
        return self.get_generic_wpn(weapon_values)

    def get_generic_wpn_dmg(self, weapon_name):
        if weapon_name is None:
            return [None, None]
        if weapon_name == '?':
            return ['?', '?']
        weapon: Template = self.bits.templates.templates[weapon_name]
        dmg_min = parse_int_value(weapon.compute_value('attack', 'damage_min'))
        dmg_max = parse_int_value(weapon.compute_value('attack', 'damage_max'))
        return [dmg_min, dmg_max]

    def get_melee_wpn_dmg(self):
        weapon_name = self.get_melee_wpn()
        return self.get_generic_wpn_dmg(weapon_name)

    def get_ranged_wpn_dmg(self):
        weapon_name = self.get_ranged_wpn()
        return self.get_generic_wpn_dmg(weapon_name)


def get_equipment(es, template: Template) -> list[str]:
    es_attrs: list[Attribute] = list()
    template.section.find_attrs_recursive(es, es_attrs)
    if len(es_attrs) > 0:
        return [a.value for a in es_attrs]
    if template.parent_template:
        return get_equipment(es, template.parent_template)
    return list()


def get_attack_spells(enemy: Enemy, bits: Bits):
    spell_names = [e for an in SPELL_ATTR_NAMES for e in get_equipment(an, enemy.template)]
    spell_templates = [bits.templates.templates[n] for n in spell_names]
    return spell_templates


def make_csv_line(attack: EnemyAttack) -> dict:
    return {
        'template': attack.enemy.template_name,
        'screen_name': attack.enemy.screen_name,
        'stance': attack.stance,
        'base dmg min': attack.base_dmg_min,
        'base dmg max': attack.base_dmg_max,
        'wpn': attack.weapon,
        'wpn dmg min': attack.wpn_dmg_min,
        'wpn dmg max': attack.wpn_dmg_max,
        'spl comp': attack.spell_component,
    }


def write_enemy_attacks_csv(bits: Bits):
    enemies = load_enemies(bits)
    attacks: list[EnemyAttack] = list()
    for enemy in enemies:
        if enemy.is_melee():
            attacks.append(EnemyAttack(enemy, bits, 'Melee'))
        if enemy.is_ranged():
            attacks.append(EnemyAttack(enemy, bits, 'Ranged'))
        if enemy.is_magic():
            for spell in get_attack_spells(enemy, bits):
                a = EnemyAttack(enemy, bits, 'Magic', spell)
                if a.wpn_dmg_min or a.wpn_dmg_max:
                    attacks.append(a)

    keys = ['template', 'screen_name', 'stance', 'base dmg min', 'base dmg max', 'wpn', 'wpn dmg min', 'wpn dmg max', 'spl comp']
    header_dict = {
        'template': 'Template',
        'screen_name': 'Screen Name',
        'stance': 'Stance',
        'base dmg min': 'Base Dmg Min',
        'base dmg max': 'Base Dmg Max',
        'wpn': 'Weapon',
        'wpn dmg min': 'Wpn Dmg Min',
        'wpn dmg max': 'Wpn Dmg Max',
        'spl comp': 'Spell Component'
    }
    data_dicts = [make_csv_line(a) for a in attacks]

    write_csv_dict('Enemy Attacks', keys, header_dict, data_dicts, ';')
