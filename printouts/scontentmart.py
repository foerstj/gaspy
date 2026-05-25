import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.csv import write_csv_dict
from printouts.equipment import Equipment, EQUIPMENT_USAGE, load_equipment_templates

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


class SCMEquipment(Equipment):
    def decide_scm_shop(self):
        v = 'loa' if self.is_dsx else 'v'
        if self.inventory_icon is None or self.screen_name is None:
            return v + '_excluded'
        if not (self.is_accessible or self.template_name in GREENLIGHT_INACCESSIBLE):
            return v + '_excluded'
        if self.equipment_type is None or (self.equipment_type == 'weapon' and self.weapon_kind is None):
            return v + '_excluded'
        if not self.can_sell:
            return v + '_excluded'
        if self.tn_red_flag:
            return v + '_excluded'

        if self.item_set:
            sp = 'sp' if self.item_set in ['arhok', 'illicor', 'kajj', 'patents', 'demlock', 'clockwork'] else 'mp'
            return 'loa_any_sets_' + sp

        stance = self.decide_stance() or 'any'
        eq_type = self.equipment_type
        shop_type = self.armor_type if eq_type == 'armor' else self.weapon_type if eq_type == 'weapon' else None
        rarity = 's' if self.rarity or not self.is_pcontent_allowed else 'n'  # shops are only either normal or special

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
            if self.weapon_kind == 'melee' and stance == 'f':
                if v == 'loa':
                    if self.is_2h:
                        shop_type = '2h'
                        rarity = None
                    else:
                        shop_type = '1h'
                else:
                    if self.is_2h:
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
        if self.usage == 'bonus':
            shop_type = 'bonus'
            rarity = None
            stance = None

        parts = [v, stance, shop_type, rarity]
        return '_'.join([p for p in parts if p is not None])


def process_equipments(equipment_templates: list[Template], dsx_equipment_template_names: list[str], equipment_usages: dict[str, str]) -> list[SCMEquipment]:
    return [
        SCMEquipment(equipment_template, equipment_template.name.lower() in dsx_equipment_template_names, equipment_usages.get(equipment_template.name.lower()))
        for equipment_template in equipment_templates
        if not equipment_template.has_component('generator_multiple_mp')
    ]


def make_equipments_csv(equipments: list[SCMEquipment]):
    keys = ['template', 'screen_name', 'stance', 'scm_shop', 'is_dsx', 'eq_type', 'excluded', 'set', 'item_type', 'rarity', 'req_stat', 'variants']
    headers = {
        'template': 'Template', 'screen_name': 'Screen Name',
        'is_dsx': 'LoA', 'eq_type': 'Equipment Type', 'excluded': 'Excluded', 'set': 'Item Set',
        'item_type': 'Item Type', 'rarity': 'Rarity', 'req_stat': 'Req. Stat',
        'variants': 'Variants',
        'stance': 'Stance', 'scm_shop': 'SCM Shop',
    }
    data = []
    for item in equipments:
        row = {
            'template': item.template_name,
            'screen_name': item.screen_name,
            'is_dsx': 'LoA' if item.is_dsx else None,
            'eq_type': item.equipment_type,
            'excluded': 'excluded' if item.is_pcontent_allowed is False else None,
            'set': item.item_set,
            'item_type': item.armor_type if item.equipment_type == 'armor' else item.weapon_type if item.equipment_type == 'weapon' else None,
            'rarity': {'ra': 'rare', 'un': 'unique'}.get(item.rarity),
            'req_stat': item.req_stat,
            'variants': ', '.join([v.name for v in item.variants]),
            'stance': {'f': 'Fighter', 'r': 'Ranger', 'm': 'Mage'}.get(item.decide_stance()),
            'scm_shop': item.decide_scm_shop(),
        }
        data.append(row)
    return keys, headers, data


def printout_equipment_shops(equipments: list[SCMEquipment]):
    shops = dict()
    for item in equipments:
        shop_name = item.decide_scm_shop()
        if shop_name not in shops:
            shops[shop_name] = (0, 0)
        num_items, num_variants = shops[shop_name]
        num_items += 1
        num_variants += max(1, len(item.variants))
        shops[shop_name] = (num_items, num_variants)
    print()
    print(f'SCM shops:')
    for shop_name in sorted(shops.keys()):
        (num_items, num_variants) = shops[shop_name]
        print(f'{shop_name}: {num_items} / {num_variants}')
    print(f'SCM shops: {len(shops)}')


def printout_scontentmart(bits: Bits, output_dir='output'):
    dsx_equipment_template_names, equipment_templates = load_equipment_templates(bits)
    equipments = process_equipments(equipment_templates, dsx_equipment_template_names, EQUIPMENT_USAGE)
    printout_equipment_shops(equipments)
    equipments_csv = make_equipments_csv(equipments)
    write_csv_dict('equipments', *equipments_csv, sep=';', quote_cells=False, output_dir=output_dir)


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
