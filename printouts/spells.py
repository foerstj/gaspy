import argparse
import sys

from bits.bits import Bits
from gas.gas_parser import GasParser
from printouts.csv import write_csv


def csv_val(value: str):
    if value is None:
        return ''
    return value.strip('"')


def write_spells_csv(bits: Bits, only_for=None, only_type=None, only_class=None):
    spell_templates = bits.templates.get_leaf_templates('spell')

    csv_header = ['Template', 'Name', 'Scroll', 'P/M', 'N/C', 'gold', 'min lvl', 'max lvl', 'range', '1shot', 'state', 'desc']
    csv = [csv_header]

    for spell_template in spell_templates.values():
        template_name = spell_template.name

        is_monster = spell_template.is_descendant_of('base_spell_monster')
        if only_for == 'player' and is_monster:
            continue
        elif only_for == 'monster' and not is_monster:
            continue
        pm = 'P' if not is_monster else 'M'

        one_use = spell_template.compute_value('magic', 'one_use')
        is_scroll = one_use and one_use.lower() == 'true'
        if only_type == 'spell' and is_scroll:
            continue
        elif only_type == 'scroll' and not is_scroll:
            continue
        spell_type = 'SCROLL' if is_scroll else ''

        magic_class = spell_template.compute_value('magic', 'magic_class')
        assert magic_class in ['mc_nature_magic', 'mc_combat_magic']
        nc = 'N' if magic_class == 'mc_nature_magic' else 'C'
        if only_class == 'nature' and nc != 'N':
            continue
        elif only_class == 'combat' and nc != 'C':
            continue

        screen_name = csv_val(spell_template.compute_value('common', 'screen_name'))

        gold_value = csv_val(spell_template.compute_value('aspect', 'gold_value'))
        required_level = csv_val(spell_template.compute_value('magic', 'required_level'))
        max_level = csv_val(spell_template.compute_value('magic', 'max_level'))
        cast_range = csv_val(spell_template.compute_value('magic', 'cast_range'))
        is_one_shot = spell_template.compute_value('magic', 'is_one_shot')
        is_one_shot = False if is_one_shot is None else (is_one_shot.lower() == 'true')
        is_one_shot = '1' if is_one_shot else ''
        state_name = csv_val(spell_template.compute_value('magic', 'state_name'))
        description = csv_val(spell_template.compute_value('common', 'description'))

        csv.append([template_name, screen_name, spell_type, pm, nc, gold_value, required_level, max_level, cast_range, is_one_shot, state_name, description])

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
