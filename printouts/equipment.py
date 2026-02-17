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


def load_armors(bits: Bits) -> list[Template]:
    return list(bits.templates.get_leaf_templates('armor').values())


def process_armors(armor_templates: list[Template]):
    return [Armor(armor_template) for armor_template in armor_templates]


def make_armors_csv(armors: list[Armor]):
    keys = ['template', 'screen_name']
    headers = {'template': 'Template', 'screen_name': 'Screen Name'}
    data = [{'template': armor.template_name, 'screen_name': armor.screen_name} for armor in armors]
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
