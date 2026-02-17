import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.csv import write_csv_dict


class Armor:
    def __init__(self, template: Template, is_dsx: bool):
        self._template = template
        self.is_dsx = is_dsx
        self.template_name = template.name
        self.screen_name = template.compute_value('common', 'screen_name').strip('"')
        self.world_level, self.coverage, self.rarity, self.material = self.parse_template_name(self.template_name)
        variants = []
        if template.has_component('pcontent'):
            pcontent_section = template.section.get_section('pcontent')
            variants = [s.header for s in pcontent_section.get_sections()]
        self.variants = variants

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
        if name_parts[0] in ['ra', 'un']:  # wtf he_ra_un_fu_pl_skull
            rarity = name_parts.pop(0)

        # skip over subtypes of boots/gloves/helmets
        if coverage == 'bo':
            assert name_parts[0] in ['bo', 'gr', 'sh'], template_name
            name_parts.pop(0)
        if coverage == 'gl':
            assert name_parts[0] in ['ga', 'gl'], template_name
            name_parts.pop(0)
        if coverage == 'he':
            if name_parts[0] in ['ca', 'fu', 'op', 'vi', 'fl']:
                name_parts.pop(0)
            else:
                print(f'wtf helmet {template_name}')

        material = None
        if coverage != 'sh':
            if name_parts[0] in ['le', 'bl', 'sl', 'ro', 'ba', 'br', 'fp', 'pl', 'ch', 'sc', 'bp']:
                material = name_parts.pop(0)
            else:
                print(f'wtf material {template_name}')

        return world_level, coverage, rarity, material


def load_dsx_armor_template_names(bits: Bits) -> list[str]:
    templates = {}
    template_base_dir = bits.templates.gas_dir
    interactive_dir = template_base_dir.get_subdir(['regular', 'interactive'])
    for gas_file_name, gas_file in interactive_dir.get_gas_files().items():
        if gas_file_name.startswith('dsx_'):
            bits.templates.load_templates_file(interactive_dir.get_gas_file(gas_file_name), templates)
    # templates are unconnected but we only return the names anyway
    return list(templates.keys())


def load_armor_templates(bits: Bits) -> tuple[list[str], list[Template]]:
    dsx_armor_template_names = load_dsx_armor_template_names(bits)
    armor_templates = list(bits.templates.get_leaf_templates('armor').values())
    return dsx_armor_template_names, armor_templates


def process_armors(armor_templates: list[Template], dsx_armor_template_names: list[str]):
    return [Armor(armor_template, armor_template.name in dsx_armor_template_names) for armor_template in armor_templates if armor_template.name != 'gen_bd_un_bl_f_g_c_blood']


def make_armors_csv(armors: list[Armor]):
    keys = ['template', 'screen_name', 'is_dsx', 'world_level', 'coverage', 'rarity', 'material', 'variants']
    headers = {
        'template': 'Template', 'screen_name': 'Screen Name',
        'is_dsx': 'LoA', 'world_level': 'World Level',
        'coverage': 'Coverage', 'rarity': 'Rarity', 'material': 'Material', 'variants': 'Variants',
    }
    data = []
    for armor in armors:
        row = {
            'template': armor.template_name,
            'screen_name': armor.screen_name,
            'is_dsx': 'LoA' if armor.is_dsx else None,
            'world_level': {'2w': 'Veteran', '3w': 'Elite'}.get(armor.world_level),
            'coverage': {'bd': 'Body', 'he': 'Helmet', 'bo': 'Boots', 'gl': 'Gloves', 'sh': 'Shield'}.get(armor.coverage),
            'rarity': {'ra': 'rare', 'un': 'unique'}.get(armor.rarity),
            'material': armor.material,
            'variants': ', '.join(armor.variants)
        }
        data.append(row)
    return keys, headers, data


def printout_equipment(bits: Bits):
    dsx_armor_template_names, armor_templates = load_armor_templates(bits)
    armors = process_armors(armor_templates, dsx_armor_template_names)
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
