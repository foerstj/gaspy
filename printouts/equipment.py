import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.csv import write_csv_dict


def load_armors(bits: Bits) -> list[tuple[str, Template]]:
    return [(template_name, template) for template_name, template in bits.templates.get_leaf_templates('armor').items()]


def make_armors_csv(armors: list[tuple[str, Template]]):
    keys = ['template', 'screen_name']
    headers = {'template': 'Template', 'screen_name': 'Screen Name'}
    data = [{'template': template_name, 'screen_name': template.compute_value('common', 'screen_name').strip('"')} for template_name, template in armors]
    return keys, headers, data


def printout_equipment(bits: Bits):
    armors = load_armors(bits)
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
