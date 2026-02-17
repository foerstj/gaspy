import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.csv import write_csv_dict


class Armor:
    def __init__(self, template: Template):
        self._template = template
        self.template_name = template.name
        self.screen_name = template.compute_value('common', 'screen_name').strip('"')
        self.world_level, self.coverage, self.rarity = self.parse_template_name(self.template_name)

    @classmethod
    def parse_template_name(cls, template_name: str):
        name_parts = template_name.split('_')
        world_level = None
        if name_parts[0].lower() in ['2w', '3w']:
            world_level = name_parts.pop(0).lower()
        coverage = None
        if name_parts[0] in ['bd', 'he', 'bo', 'gl', 'sh']:
            coverage = name_parts.pop(0)
        rarity = None
        if name_parts[0] in ['ra', 'un']:
            rarity = name_parts.pop(0)
        return world_level, coverage, rarity


def load_armors(bits: Bits) -> list[Template]:
    return list(bits.templates.get_leaf_templates('armor').values())


def process_armors(armor_templates: list[Template]):
    return [Armor(armor_template) for armor_template in armor_templates if armor_template.name != 'gen_bd_un_bl_f_g_c_blood']


def make_armors_csv(armors: list[Armor]):
    keys = ['template', 'screen_name', 'world_level', 'coverage', 'rarity']
    headers = {'template': 'Template', 'screen_name': 'Screen Name', 'world_level': 'World Level', 'coverage': 'Coverage', 'rarity': 'Rarity'}
    data = []
    for armor in armors:
        row = {
            'template': armor.template_name,
            'screen_name': armor.screen_name,
            'world_level': {'2w': 'Veteran', '3w': 'Elite'}.get(armor.world_level),
            'coverage': {'bd': 'Body', 'he': 'Helmet', 'bo': 'Boots', 'gl': 'Gloves', 'sh': 'Shield'}.get(armor.coverage),
            'rarity': {'ra': 'rare', 'un': 'unique'}.get(armor.rarity)
        }
        data.append(row)
    return keys, headers, data


def printout_equipment(bits: Bits):
    armor_templates = load_armors(bits)
    armors = process_armors(armor_templates)
    armors_csv = make_armors_csv(armors)
    write_csv_dict('armors', *armors_csv)


def equipment(bits_path: str):
    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)
    printout_equipment(bits)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Equipment')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    equipment(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
