import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas import Section
from gas.gas_parser import GasParser
from printouts.common import parse_bool_value
from printouts.csv import write_csv_dict


GREENLIGHT_INACCESSIBLE = [
    'he_un_ca_pl_guard_archer',
    'he_un_op_pl_guard_captain',
    'he_un_op_pl_guard_fighter',
    'sh_u_g_c_k_l_avg',
    'sh_un_m_o_k_m_dermal',
    'he_threestorms',
]


ACCESSIBLE = ['hero', 'companion', 'placed', 'drop', 'drops', 'container', 'containers', 'convo', 'bonus']
# companion = worn by companion, hero = worn by hero, drop/s = dropped by enemy/enemies, placed = placed on map, container/s = placed in container/s,
# convo = given in conversation, bonus = chicken level / krug disco
# unused = unused, npc = worn by npc, enemy = worn by enemy (and not dropped)
ACCESSIBILITY = {
    # Accessible
    # vanilla
    'bd_ro_un_merik': 'companion',
    'bd_un_le_f_pad_avg': 'drop',  # altans leather
    'bd_un_ba_f_g_skeleton_captain': 'drop',
    'bo_bo_le_f_g_c_healthy': 'placed',
    'bo_bo_le_f_g_c_satin': 'companion',  # merik
    'bo_bo_le_light': 'hero',
    'he_fu_pl_knight_fin_03': 'container',  # in a container
    'he_fu_pl_smallwings_kavaren': 'convo',
    'sh_w_g_c_r_s_krohar': 'drop',
    # loa
    'he_ra_ca_le_avg_pimp': 'bonus',
    'he_op_pl_f_ofkhar_dsx': 'convo',
    '2w_he_op_pl_f_ofkhar_dsx': 'convo',
    '3w_he_op_pl_f_ofkhar_dsx': 'convo',
    'st_un_dsx_angk': 'drop',
    '2w_st_un_dsx_angk': 'drop',
    '3w_st_un_dsx_angk': 'drop',
    'sd_d_c_dsx_skl_1h_mag_player': 'drop',
    '2w_sd_d_c_dsx_skl_1h_mag_player': 'drop',
    '3w_sd_d_c_dsx_skl_1h_mag_player': 'drop',
    'sh_w_f_g_c_t_s_avg_deathknight_player': 'drop',
    '2w_sh_w_f_g_c_t_s_avg_deathknight_player': 'drop',
    '3w_sh_w_f_g_c_t_s_avg_deathknight_player': 'drop',

    # Inaccessible
    # vanilla
    'he_un_ca_pl_guard_archer': 'unused',
    'he_un_op_pl_guard_captain': 'unused',
    'he_un_op_pl_guard_fighter': 'unused',
    'he_threestorms': 'unused',
    'sh_u_g_c_k_l_avg': 'unused',
    'sh_un_m_o_k_m_dermal': 'unused',
    'tongs': 'npc',
    'blacksmith_hammer': 'npc',
    'torch_small': 'enemy',
    # loa
    'bd_pl_f_g_c_death_knight': 'enemy',
    'sh_w_f_g_c_t_s_avg_deathknight_monster': 'enemy',
    'sh_un_m_o_r_m_turtle_dsx': 'enemy',
    'sh_un_m_o_r_m_turtle_01_dsx': 'enemy',
    'sh_un_m_o_r_m_turtle_02_dsx': 'enemy',
    'sh_un_m_o_k_m_dermal_dsx': 'enemy',
    'dsx_minigun_gas_monster': 'enemy',
    'minigun_magic_missles': 'unused',
    'sd_g_c_dsx_kat_1h_shadowjumper_NIS_ONLY': 'nis',
    'st_g_c_dsx_pcane': 'unused',
    'st_un_dsx_angk_guardian': 'enemy',
    'sd_d_c_dsx_skl_1h_mag': 'enemy',
}


def parse_equip_requirements(value: str):
    reqs = dict()
    req_strs = value.split(',')
    for req_str in req_strs:
        stat, val_str = req_str.split(':')
        reqs[stat.strip()] = int(val_str)
    return reqs


def get_pcontent_variants(template: Template) -> list[Section]:
    var_secs = []
    while template is not None:
        pcontent_section = template.section.get_section('pcontent')
        if pcontent_section:
            var_secs.extend(pcontent_section.get_sections())
        template = template.parent_template
    return var_secs


class Armor:
    def __init__(self, template: Template, is_dsx: bool):
        self._template = template
        self.is_dsx = is_dsx

        self.template_name = template.name
        screen_name = template.compute_value('common', 'screen_name')
        self.screen_name = screen_name.strip('"') if screen_name is not None else None

        self.equipment_type = 'armor' if template.is_descendant_of('armor') else 'weapon' if template.is_descendant_of('weapon') else None
        self.weapon_kind = 'melee' if template.is_descendant_of('weapon_melee') else 'ranged' if template.is_descendant_of('weapon_ranged') else None

        self.world_level, self.armor_type, self.weapon_type, self.rarity, self.material, self.tn_stance = self.parse_template_name(self.template_name)
        if self.template_name == 'dsx_gobbot_grenade_launcher':
            self.weapon_type = 'minigun'  # sigh

        variant_sections = get_pcontent_variants(template)
        self.variants = [s.header for s in variant_sections]

        self.req_stat = self.get_equip_requirement_stat(template)
        if self.req_stat == 'int':
            if not (self.tn_stance == 'm' or self.tn_stance is None):
                print(f'wtf tn-stance {template.name}')
        if self.req_stat == 'dex':
            if not (self.tn_stance == 'r' or self.tn_stance is None):
                print(f'wtf tn-stance {template.name}')

        if not self.decide_stance():
            print(f'undecided stance {template.name}')

        self.is_pcontent_allowed = parse_bool_value(template.compute_value('common', 'is_pcontent_allowed'), True)

        accessibility = ACCESSIBILITY.get(template.name)
        accessibility = None if accessibility is None else accessibility in ACCESSIBLE
        self.is_ok = self.is_pcontent_allowed or accessibility is not False or template.name in GREENLIGHT_INACCESSIBLE

        self.item_set = template.compute_value('set_item', 'set_compare_name')

        self.inventory_icon = template.compute_value('gui', 'inventory_icon')

        is_2h_val = template.compute_value('attack', 'is_two_handed')
        self.is_2h = parse_bool_value(is_2h_val) if is_2h_val != '2' else None  # wtf Guiseppi's Bow

        self.can_sell = parse_bool_value(template.compute_value('gui', 'can_sell'), True)

        tn_segs = self.template_name.split('_')
        self.tn_red_flag = 'temp' in tn_segs or 'NIS' in tn_segs

    def decide_stance(self):
        # if sth requires dex or int, it's for rangers / mages
        if self.req_stat == 'dex':
            return 'r'
        if self.req_stat == 'int':
            return 'm'
        # with str reqs we can't be so sure
        if self.weapon_kind == 'ranged':
            return 'r'
        if self.weapon_type == 'st' and self.req_stat != 'str':
            return 'm'  # staves are for mages by default
        if self.weapon_kind == 'melee':
            return 'f'
        if self.material == 'ro' and self.req_stat == 'str':  # wtf molten boots
            return 'f'
        # let's check what the template name says
        if self.tn_stance:
            return self.tn_stance
        if self.req_stat == 'str':
            return 'f'
        # if material is robe, it's for mages
        if self.material == 'ro':
            return 'm'
        # shield without any requirements - fighter
        if self.armor_type == 'sh':
            return 'f'
        # no idea - hopefully all that's left now is bo_bo_le_light
        return None

    def decide_scm_shop(self):
        if self.inventory_icon is None or self.screen_name is None:
            return 'x_excluded'
        if self.is_ok is False:
            return 'x_excluded'
        if self.equipment_type is None or (self.equipment_type == 'weapon' and self.weapon_kind is None):
            return 'x_excluded'
        if not self.can_sell:
            return 'x_excluded'
        if self.tn_red_flag:
            return 'x_excluded'

        if self.item_set:
            return 'loa_any_sets'

        v = 'loa' if self.is_dsx else 'v'
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
            v = 'x'  # even vanilla & loa
            rarity = None
            shop_type = None

        parts = [v, stance, shop_type, rarity]
        return '_'.join([p for p in parts if p is not None])

    @classmethod
    def parse_template_name(cls, template_name: str):
        name_parts = template_name.split('_')

        world_level = None
        if name_parts[0].lower() in ['2w', '3w']:
            world_level = name_parts.pop(0).lower()

        if name_parts[0] == 'dsx':
            name_parts.pop(0)

        armor_type = None
        if name_parts[0] in ['bd', 'he', 'bo', 'gl', 'sh']:
            armor_type = name_parts.pop(0)
        weapon_type = None
        if name_parts[0] in ['ax', 'cb', 'dg', 'hm', 'mc', 'st', 'sd', 'ss', 'scythe'] or name_parts[0] in ['bw', 'cw', 'minigun']:
            weapon_type = name_parts.pop(0)

        rarity = None
        if name_parts[0] in ['ra', 'un']:
            rarity = name_parts.pop(0)
        if name_parts[0] in ['ra', 'un']:  # wtf he_ra_un_fu_pl_skull
            rarity = name_parts.pop(0)

        # skip over subtypes of boots/gloves/helmets
        if armor_type == 'bo':
            assert name_parts[0] in ['bo', 'gr', 'sh'], template_name
            name_parts.pop(0)
        if armor_type == 'gl':
            assert name_parts[0] in ['ga', 'gl'], template_name
            name_parts.pop(0)
        if armor_type == 'he':
            if name_parts[0] in ['ca', 'fu', 'op', 'vi', 'fl']:
                name_parts.pop(0)
            else:
                print(f'wtf helmet {template_name}')

        material = None
        if armor_type is not None and armor_type != 'sh':
            if name_parts[0] in ['le', 'bl', 'sl', 'ro', 'ba', 'br', 'fp', 'pl', 'ch', 'sc', 'bp']:
                material = name_parts.pop(0)
            else:
                print(f'wtf material {template_name}')

        stance = None
        if armor_type is not None and armor_type != 'sh':
            is_fighter = 'f' in name_parts
            is_ranger = 'r' in name_parts
            is_mage = 'm' in name_parts
            if is_fighter + is_ranger + is_mage == 1:
                stance = 'f' if is_fighter else 'r' if is_ranger else 'm' if is_mage else None

        return world_level, armor_type, weapon_type, rarity, material, stance

    @classmethod
    def get_equip_requirement_stat(cls, template: Template):
        reqs_str = template.compute_value('gui', 'equip_requirements')
        reqs = parse_equip_requirements(reqs_str) if reqs_str is not None else dict()
        req_stats = list(reqs.keys())

        is_str = 'strength' in req_stats
        is_dex = 'dexterity' in req_stats
        is_int = 'intelligence' in req_stats
        if is_str + is_dex + is_int > 1:
            return 'multi'
        return 'str' if is_str else 'dex' if is_dex else 'int' if is_int else None


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
    armor_templates = list()
    armor_templates.extend(bits.templates.get_leaf_templates('armor').values())
    armor_templates.extend(bits.templates.get_leaf_templates('weapon').values())
    return dsx_armor_template_names, armor_templates


def process_armors(armor_templates: list[Template], dsx_armor_template_names: list[str]):
    return [Armor(armor_template, armor_template.name.lower() in dsx_armor_template_names) for armor_template in armor_templates if not armor_template.has_component('generator_multiple_mp')]


def make_armors_csv(armors: list[Armor]):
    keys = ['template', 'screen_name', 'stance', 'scm_shop', 'is_dsx', 'eq_type', 'world_level', 'excluded', 'set', 'item_type', 'rarity', 'material', 'tn_stance', 'req_stat', 'icon', 'variants']
    headers = {
        'template': 'Template', 'screen_name': 'Screen Name',
        'is_dsx': 'LoA', 'eq_type': 'Equipment Type', 'world_level': 'World Level', 'excluded': 'Excluded', 'set': 'Item Set',
        'item_type': 'Item Type', 'rarity': 'Rarity', 'material': 'Material', 'tn_stance': 'TN Stance', 'req_stat': 'Req. Stat', 'icon': 'Icon',
        'variants': 'Variants',
        'stance': 'Stance', 'scm_shop': 'SCM Shop',
    }
    data = []
    for armor in armors:
        row = {
            'template': armor.template_name,
            'screen_name': armor.screen_name,
            'is_dsx': 'LoA' if armor.is_dsx else None,
            'eq_type': armor.equipment_type,
            'world_level': {'2w': 'Veteran', '3w': 'Elite'}.get(armor.world_level),
            'excluded': 'excluded' if armor.is_pcontent_allowed is False else None,
            'set': armor.item_set,
            'item_type': armor.armor_type if armor.equipment_type == 'armor' else armor.weapon_type if armor.equipment_type == 'weapon' else None,
            'rarity': {'ra': 'rare', 'un': 'unique'}.get(armor.rarity),
            'material': armor.material,
            'tn_stance': armor.tn_stance,
            'req_stat': armor.req_stat,
            'icon': armor.inventory_icon,
            'variants': ', '.join(armor.variants),
            'stance': {'f': 'Fighter', 'r': 'Ranger', 'm': 'Mage'}.get(armor.decide_stance()),
            'scm_shop': armor.decide_scm_shop(),
        }
        data.append(row)
    return keys, headers, data


def printout_armor_shops(armors: list[Armor]):
    shops = dict()
    for armor in armors:
        shop_name = armor.decide_scm_shop()
        if shop_name not in shops:
            shops[shop_name] = (0, 0)
        num_items, num_variants = shops[shop_name]
        num_items += 1
        num_variants += max(1, len(armor.variants))
        shops[shop_name] = (num_items, num_variants)
    print()
    print(f'SCM shops:')
    for shop_name in sorted(shops.keys()):
        (num_items, num_variants) = shops[shop_name]
        print(f'{shop_name}: {num_items} / {num_variants}')
    print(f'SCM shops: {len(shops)}')


def printout_equipment(bits: Bits):
    dsx_armor_template_names, armor_templates = load_armor_templates(bits)
    armors = process_armors(armor_templates, dsx_armor_template_names)
    printout_armor_shops(armors)
    armors_csv = make_armors_csv(armors)
    write_csv_dict('armors', *armors_csv, sep=';', quote_cells=False)


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
