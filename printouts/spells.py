import argparse
import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.csv import write_csv


def csv_val(value: str):
    if value is None:
        return ''
    return value.strip('"')


class Spell:
    def __init__(
            self,
            template_name,
            spell_component,
            is_monster,
            is_scroll,
            magic_class,
            screen_name,
            gold_value,
            required_level,
            max_level,
            cast_range,
            is_one_shot,
            state_name,
            description,
            is_pcontent_allowed
    ):
        self.template_name = template_name
        self.spell_component: str = spell_component
        self.is_monster = is_monster
        self.is_scroll = is_scroll
        self.magic_class = magic_class
        self.screen_name = screen_name
        self.gold_value = gold_value
        self.required_level = required_level
        self.max_level = max_level
        self.cast_range = cast_range
        self.is_one_shot = is_one_shot
        self.state_name = state_name
        self.description = description
        self.is_pcontent_allowed = is_pcontent_allowed
        self.used_by_actors = list()

    @staticmethod
    def read_template(spell_template: Template) -> 'Spell':
        template_name = spell_template.name

        spell_component = None
        for template in [spell_template] + spell_template.base_templates():
            for section in template.section.get_sections():
                section_header = section.header.lower()
                if not section_header.startswith('spell_') and not section_header.startswith('dsx_spell_'):
                    continue
                spell_component = section.header

        is_monster = spell_template.is_descendant_of('base_spell_monster')

        one_use = spell_template.compute_value('magic', 'one_use')
        is_scroll = one_use and one_use.lower() == 'true'

        magic_class = spell_template.compute_value('magic', 'magic_class')
        assert magic_class in ['mc_nature_magic', 'mc_combat_magic']

        screen_name = spell_template.compute_value('common', 'screen_name')

        gold_value = spell_template.compute_value('aspect', 'gold_value')

        required_level = spell_template.compute_value('magic', 'required_level')

        max_level = spell_template.compute_value('magic', 'max_level')

        cast_range = spell_template.compute_value('magic', 'cast_range')

        is_one_shot = spell_template.compute_value('magic', 'is_one_shot')
        is_one_shot = False if is_one_shot is None else (is_one_shot.lower() == 'true')

        state_name = spell_template.compute_value('magic', 'state_name')

        description = spell_template.compute_value('common', 'description')

        is_pcontent_allowed = spell_template.compute_value('common', 'is_pcontent_allowed')
        is_pcontent_allowed = True if is_pcontent_allowed is None else (is_pcontent_allowed.lower() == 'true')

        return Spell(
            template_name,
            spell_component,
            is_monster,
            is_scroll,
            magic_class,
            screen_name,
            gold_value,
            required_level,
            max_level,
            cast_range,
            is_one_shot,
            state_name,
            description,
            is_pcontent_allowed
        )

    def write_csv_line(self):
        template_name = self.template_name
        spell_component = self.spell_component if self.spell_component is not None else ''
        pm = 'P' if not self.is_monster else 'M'
        spell_type = 'SCROLL' if self.is_scroll else ''
        nc = 'N' if self.magic_class == 'mc_nature_magic' else 'C'
        screen_name = csv_val(self.screen_name)
        gold_value = csv_val(self.gold_value)
        required_level = csv_val(self.required_level)
        max_level = csv_val(self.max_level)
        cast_range = csv_val(self.cast_range)
        is_one_shot = '1' if self.is_one_shot else ''
        state_name = csv_val(self.state_name)
        description = csv_val(self.description)
        pcontent = 'yes' if self.is_pcontent_allowed else ''
        actors = ', '.join([a.name for a in self.used_by_actors])
        return [template_name, spell_component, screen_name, spell_type, pm, nc, gold_value, required_level, max_level, cast_range, is_one_shot, pcontent, state_name, description, actors]


def filter_spell(spell: Spell, only_for=None, only_type=None, only_class=None) -> bool:
    if only_for == 'player' and spell.is_monster:
        return False
    elif only_for == 'monster' and not spell.is_monster:
        return False
    if only_type == 'spell' and spell.is_scroll:
        return False
    elif only_type == 'scroll' and not spell.is_scroll:
        return False
    if only_class == 'nature' and spell.magic_class != 'mc_nature_magic':
        return False
    elif only_class == 'combat' and spell.magic_class != 'mc_combat_magic':
        return False
    return True


def write_spells_csv(bits: Bits, only_for=None, only_type=None, only_class=None):
    spell_templates = bits.templates.get_leaf_templates('spell')
    spells = {spell_template.name: Spell.read_template(spell_template) for spell_template in spell_templates.values()}
    spells = {name: spell for name, spell in spells.items() if filter_spell(spell, only_for, only_type, only_class)}

    spell_attrs = ['il_active_primary_spell', 'il_active_secondary_spell', 'il_spell_1', 'il_spell_2', 'il_spell_3', 'il_spell_4', 'il_spell_5', 'il_spell_6', 'il_spell_7', 'il_spell_8', 'il_spell_9', 'il_spell_10', 'il_spell_11', 'il_spell_12']
    actors = bits.templates.get_actor_templates(False)
    for actor in actors.values():
        if actor.name.startswith('2W_') or actor.name.startswith('3W_'):
            continue
        for spell_attr_name in spell_attrs:
            for attr in actor.section.find_attrs_recursive(spell_attr_name):
                if attr.value in spells:
                    spell = spells[attr.value]
                    assert isinstance(spell, Spell)
                    spell.used_by_actors.append(actor)

    csv_header = ['Template', 'Component', 'Name', 'Scroll', 'P/M', 'N/C', 'gold', 'min lvl', 'max lvl', 'range', '1shot', 'pcontent', 'state', 'desc', 'used by']
    csv = [csv_header]
    csv.extend([spell.write_csv_line() for spell in spells.values()])

    print(f'CSV: {len(csv)-1} data rows')
    write_csv('Spells', csv)


# Own CLI for more options

def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printouts spells')
    parser.add_argument('--only-for', choices=['player', 'monster'])
    parser.add_argument('--only-type', choices=['spell', 'scroll'])
    parser.add_argument('--only-class', choices=['nature', 'combat'])
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    GasParser.get_instance().print_warnings = False
    bits = Bits(args.bits)
    write_spells_csv(bits, args.only_for, args.only_type, args.only_class)


if __name__ == '__main__':
    main(sys.argv[1:])
