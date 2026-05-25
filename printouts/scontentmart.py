import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.csv import write_csv_dict
from printouts.equipment import Equipment, EQUIPMENT_USAGE, load_equipment_templates, PContentVariant

GREENLIGHT_INACCESSIBLE = [
    'he_un_ca_pl_guard_archer',
    'he_un_op_pl_guard_captain',
    'he_un_op_pl_guard_fighter',
    'sh_u_g_c_k_l_avg',
    'sh_un_m_o_k_m_dermal',
    'he_threestorms',
    'pickaxe',
    'scythe_g_1h_fun',
    'fire_poker',
    'st_un_ice_c_d_b_avg',
    'st_un_seck_gom',
    'cb_un_2h_troll',
    'cb_un_2h_troll_rock',
    'bw_un_seck_str',
    'ax_un_2h1b_darkblood',  # Bone Axe
    'bw_dsx_zau_2',
    'bw_dsx_zau_2_a',
    'bw_dsx_zau_2_b',
    'bw_dsx_zau_2_c',
    'bw_dsx_zau_2_d',
    'bw_dsx_zaurask_2_b',
    'bw_un_droog_avg_dsx',
    'bw_dsx_hassat_01',
    'bw_dsx_hassat_02',
    'bw_dsx_hassat_03',
    'bw_g_c_s_s_r_avg_dsx',
    'bw_dsx_rune_caster',
    'cb_un_1h_troll_dsx_scrub',
    'cb_un_2h_troll_dsx_forest',
    'cb_un_dsx_2h_troll',
    'dg_g_c_dsx_kaj_mag',
    'dg_g_c_dsx_sjumper_three',
    'dg_g_c_dsx_sjumper_five',
    'hm_g_c_dsx_goblin_blackguard',
    'hm_g_c_dsx_warmlt_avg',
    'ax_d_d_dsx_goblin_mutant',
    'st_g_c_bl_1h_fun_nossirom_dsx',
    'st_un_toreck_dsx',  # scrub howler
    'st_un_seck_mage_dsx',  # necron
    'sd_g_c_dsx_kat_1h_shadowjumper',
    'ss_g_c_bl_1h_fun_zaur_dsx',
    'ss_g_c_bl_1h_fun_noss_dsx',
    'ss_g_c_bl_1h_fun_dsx',
    'ss_g_c_bl_1h_fun_01_dsx',
    'ss_g_c_bl_1h_fun_02_dsx',
    'ss_g_c_bl_1h_fun_03_dsx',
    'ss_g_c_bl_1h_fun_04_dsx',
    'ss_g_c_bl_1h_fun_05_dsx',
    'sd_g_c_sd_1h_avg_dsx',
    'sd_g_c_dsx_goblin_guard',
    'ax_d_c_1h1b_avg_dsx',
    'ax_g_c_1h2b_low_dsx',
    'bw_dsx_cicatrix_skeleton',
    'bw_dsx_hassat',
]


class SCMItem:
    def __init__(self, equipment: Equipment, variant: PContentVariant):
        self.equipment = equipment
        self.variant = variant

        self.equip_requirements = variant.equip_requirements if variant.equip_requirements is not None else equipment.equip_requirements
        self.req_stat = Equipment.get_equip_requirement_stat(self.equip_requirements)
        assert self.decide_stance() == equipment.decide_stance(), f'{equipment.template_name}:{variant.name} "{equipment.screen_name}" - different stance for variant!'

        self.inventory_icon = variant.inventory_icon if variant.inventory_icon is not None else equipment.inventory_icon
        assert bool(self.inventory_icon) == bool(equipment.inventory_icon), 'variant has icon where template has not'

    def decide_stance(self):
        return self.equipment.decide_stance(self.req_stat)


def decide_scm_shop(item: SCMItem) -> str:
    equipment = item.equipment
    v = 'loa' if equipment.is_dsx else 'v'
    if item.inventory_icon is None or equipment.screen_name is None:
        return v + '_excluded'
    if not (equipment.is_accessible or equipment.template_name in GREENLIGHT_INACCESSIBLE):
        return v + '_excluded'
    if equipment.equipment_type is None or (equipment.equipment_type == 'weapon' and equipment.weapon_kind is None):
        return v + '_excluded'
    if not equipment.can_sell:
        return v + '_excluded'
    if equipment.tn_red_flag:
        return v + '_excluded'

    if equipment.item_set:
        sp = 'sp' if equipment.item_set in ['arhok', 'illicor', 'kajj', 'patents', 'demlock', 'clockwork'] else 'mp'
        return 'loa_any_sets_' + sp

    stance = equipment.decide_stance() or 'any'
    eq_type = equipment.equipment_type
    shop_type = equipment.armor_type if eq_type == 'armor' else equipment.weapon_type if eq_type == 'weapon' else None
    rarity = 's' if equipment.rarity or not equipment.is_pcontent_allowed else 'n'  # shops are only either normal or special

    # combine shops to reasonable sizes
    if not shop_type:
        stance = 'any'  # off to the general stores

    if eq_type == 'armor':
        if v == 'loa':
            rarity = None  # combined normal/special shops for loa armors
        if shop_type in ['he', 'gl', 'bo'] and not (v == 'v' and stance == 'f'):
            shop_type = 'hgb'  # separate he/gl/bo shops only for vanilla fighters, else combine
        if stance == 'r' and rarity == 's' and shop_type != 'sh':
            shop_type = 'amr'  # combine all special ranger armors

    if eq_type == 'weapon':
        if v == 'v' and stance == 'f' and shop_type in ['cb', 'dg', 'hm', 'st', 'scythe']:
            shop_type = 'cdhss'  # combine small weapon groups - clubs daggers hammers melee-staves scythes
            rarity = None
        if v == 'v' and shop_type == 'ss':
            rarity = None
        if equipment.weapon_kind == 'melee' and stance == 'f':
            if v == 'loa':
                if equipment.is_2h:
                    shop_type = '2h'
                    rarity = None
                else:
                    shop_type = '1h'
            else:
                if equipment.is_2h:
                    shop_type += '2h'
        if shop_type in ['cw', 'minigun']:
            shop_type = 'cm'
            rarity = None
        if v == 'loa' and stance in ['r', 'm']:
            rarity = None

    if stance == 'any':
        # general store: all-in-one
        rarity = None
        shop_type = None
    if equipment.usage == 'bonus':
        shop_type = 'bonus'
        rarity = None
        stance = None

    parts = [v, stance, shop_type, rarity]
    return '_'.join([p for p in parts if p is not None])


def process_equipment_scm(equipment: Equipment) -> list[SCMItem]:
    variants = equipment.variants if len(equipment.variants) > 0 else [PContentVariant(None)]
    return [SCMItem(equipment, variant) for variant in variants]


def process_equipments(equipment_templates: list[Template], dsx_equipment_template_names: list[str], equipment_usages: dict[str, str]) -> list[Equipment]:
    return [
        Equipment(equipment_template, equipment_template.name.lower() in dsx_equipment_template_names, equipment_usages.get(equipment_template.name.lower()))
        for equipment_template in equipment_templates
        if not equipment_template.has_component('generator_multiple_mp')
    ]


def process_equipments_scm(equipments: list[Equipment]) -> list[SCMItem]:
    items: list[SCMItem] = list()
    for equipment in equipments:
        items.extend(process_equipment_scm(equipment))
    return items


def make_equipments_csv(items: list[SCMItem]):
    keys = ['template', 'variant', 'scm_shop', 'rarity', 'excluded', 'screen_name', 'stance', 'is_dsx', 'eq_type', 'set', 'item_type', 'req_stat', 'modifier_min', 'modifier_max']
    headers = {
        'template': 'Template', 'screen_name': 'Screen Name',
        'is_dsx': 'LoA', 'eq_type': 'Equipment Type', 'excluded': 'Excluded', 'set': 'Item Set',
        'item_type': 'Item Type', 'rarity': 'Rarity', 'req_stat': 'Req. Stat',
        'variant': 'Variant',
        'stance': 'Stance', 'scm_shop': 'SCM Shop',
        'modifier_min': 'ModMin', 'modifier_max': 'ModMax',
    }
    data = []
    for item in items:
        equipment = item.equipment
        row = {
            'template': equipment.template_name,
            'variant': item.variant.name,
            'scm_shop': decide_scm_shop(item),
            'rarity': {'ra': 'rare', 'un': 'unique'}.get(equipment.rarity),
            'excluded': 'excluded' if equipment.is_pcontent_allowed is False else None,
            'modifier_min': item.variant.modifier_min,
            'modifier_max': item.variant.modifier_max,
            'screen_name': equipment.screen_name,
            'is_dsx': 'LoA' if equipment.is_dsx else None,
            'eq_type': equipment.equipment_type,
            'set': equipment.item_set,
            'item_type': equipment.armor_type if equipment.equipment_type == 'armor' else equipment.weapon_type if equipment.equipment_type == 'weapon' else None,
            'req_stat': item.req_stat,
            'stance': {'f': 'Fighter', 'r': 'Ranger', 'm': 'Mage'}.get(item.decide_stance()),
        }
        data.append(row)
    return keys, headers, data


def printout_equipment_shops(items: list[SCMItem]):
    shops: dict[str, list] = dict()
    for item in items:
        shop_name = decide_scm_shop(item)
        if shop_name not in shops:
            shops[shop_name] = list()
        shops[shop_name].append(item)
    print()
    print(f'SCM shops:')
    for shop_name in sorted(shops.keys()):
        shop_content = shops[shop_name]
        template_names = set([item.equipment.template_name for item in shop_content])
        print(f'{shop_name}: {len(template_names)} / {len(shop_content)}')
    print(f'SCM shops: {len(shops)}')


def printout_scontentmart(bits: Bits, output_dir='output'):
    dsx_equipment_template_names, equipment_templates = load_equipment_templates(bits)
    equipments = process_equipments(equipment_templates, dsx_equipment_template_names, EQUIPMENT_USAGE)
    items = process_equipments_scm(equipments)
    printout_equipment_shops(items)
    scontentmart_csv = make_equipments_csv(items)
    write_csv_dict('equipments', *scontentmart_csv, sep=';', quote_cells=False, output_dir=output_dir)


def scontentmart(bits_path: str, output_dir='output'):
    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)
    printout_scontentmart(bits, output_dir)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout SContentMart data')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--out', default='output')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    scontentmart(args.bits, args.out)


if __name__ == '__main__':
    main(sys.argv[1:])
