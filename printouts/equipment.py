import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas import Section
from gas.gas_parser import GasParser
from printouts.common import parse_bool_value
from printouts.csv import write_csv_dict


ACCESSIBLE_USAGES = ['hero', 'companion', 'placed', 'drop', 'drops', 'container', 'containers', 'convo', 'bonus']
# companion = worn by companion, hero = worn by hero, drop/s = dropped by enemy/enemies, placed = placed on map, container/s = placed in container/s,
# convo = given in conversation, bonus = chicken level / krug disco
# unused = unused, npc = worn by npc, enemy = worn by enemy but not dropped, prop = placed on map but can't pick up
EQUIPMENT_USAGE = {
    # Armors
    # vanilla accessible
    'bd_ro_un_merik': 'companion',
    'bd_un_le_f_pad_avg': 'drop',  # altans leather
    'bd_un_ba_f_g_skeleton_captain': 'drop',
    'bo_bo_le_f_g_c_healthy': 'placed',
    'bo_bo_le_f_g_c_satin': 'companion',  # merik
    'bo_bo_le_light': 'hero',
    'he_fu_pl_knight_fin_03': 'container',  # in a container
    'he_fu_pl_smallwings_kavaren': 'convo',
    'sh_w_g_c_r_s_krohar': 'drop',
    # vanilla inaccessible
    'he_un_ca_pl_guard_archer': 'unused',
    'he_un_op_pl_guard_captain': 'unused',
    'he_un_op_pl_guard_fighter': 'unused',
    'he_threestorms': 'unused',
    'sh_u_g_c_k_l_avg': 'unused',
    'sh_un_m_o_k_m_dermal': 'unused',
    'tongs': 'npc',  # shield
    # loa accessible
    'he_ra_ca_le_avg_pimp': 'bonus',
    'he_op_pl_f_ofkhar_dsx': 'convo',
    '2w_he_op_pl_f_ofkhar_dsx': 'convo',
    '3w_he_op_pl_f_ofkhar_dsx': 'convo',
    'sh_w_f_g_c_t_s_avg_deathknight_player': 'drop',
    '2w_sh_w_f_g_c_t_s_avg_deathknight_player': 'drop',
    '3w_sh_w_f_g_c_t_s_avg_deathknight_player': 'drop',
    # loa inaccessible
    'bd_pl_f_g_c_death_knight': 'enemy',
    'sh_w_f_g_c_t_s_avg_deathknight_monster': 'enemy',
    'sh_un_m_o_r_m_turtle_dsx': 'enemy',
    'sh_un_m_o_r_m_turtle_01_dsx': 'enemy',
    'sh_un_m_o_r_m_turtle_02_dsx': 'enemy',
    'sh_un_m_o_k_m_dermal_dsx': 'enemy',

    # Weapons
    # vanilla accessible
    'ax_g_o_1h1b_low': 'placed',
    'bw_ra_g_c_s_s_c_stopper': 'drop',
    'bw_un_droog_avg': 'drops',
    'bw_un_ice_c_m_s_r_avg': 'drops',
    'bw_un_seck_avg': 'drops',
    'bw_un_seck_fin': 'drops',
    'cb_un_1h_swanny': 'drop',
    'cb_un_2h_cyclops': 'drops',
    'cb_un_2h_horrid': 'drops',
    'cb_un_2h_troll_forest': 'drops',
    'cb_un_2h_troll_swamp': 'drops',
    'dg_g_d_1h_fun': 'hero',
    'meat_bone': 'drops',
    'chicken_gun': 'bonus',
    'minigun_dragon': 'drops',
    'minigun_flamethrower': 'drops',
    'minigun_grenade_launcher': 'drops',
    'minigun_lightning': 'drops',
    'hoe': 'placed',
    'pitchfork': 'placed',
    'pitchfork_dull': 'placed',
    'rake': 'placed',
    'shovel': 'placed',
    'st_ra_g_o_r_puller': 'drop',
    'st_un_merik': 'placed',
    'st_un_seck_mage': 'drops',
    'st_un_toreck': 'drops',
    'sd_un_droog_1h_avg': 'drops',
    'sd_un_ice_avg': 'drops',
    'sd_un_seck_1h_avg': 'drops',
    'sd_un_seck_1h_fin': 'drops',
    'ss_un_gl_rusk': 'companion',
    # vanilla inaccessible
    'blacksmith_hammer': 'npc',
    'torch_small': 'enemy',
    'ax_un_2h1b_darkblood': 'unused',  # unused enemy
    'pickaxe': 'prop',
    'scythe_g_1h_fun': 'unused',
    'bw_un_seck_str': 'unused',
    'rock_krug': 'enemy',
    'cb_un_2h_troll': 'unused',  # unused enemy
    'cb_un_2h_troll_rock': 'unused',
    'temp_mc_g_c_f_1h_avg': 'unused',
    'fire_poker': 'enemy',
    'st_un_ice_c_d_b_avg': 'unused',
    'st_un_reaper': 'unused',
    'st_un_seck_gom': 'enemy',
    'test_rock_krug': 'unused',  # unused enemy
    # loa accessible
    'st_un_dsx_angk': 'drop',
    '2w_st_un_dsx_angk': 'drop',
    '3w_st_un_dsx_angk': 'drop',
    'sd_d_c_dsx_skl_1h_mag_player': 'drop',
    '2w_sd_d_c_dsx_skl_1h_mag_player': 'drop',
    '3w_sd_d_c_dsx_skl_1h_mag_player': 'drop',
    'ax_g_c_dsx_chp_avg_najj': 'companion',
    'bw_dsx_reynards_gift': 'convo',
    'dsx_minigun_dragon': 'drops',
    'dsx_minigun_flamethrower': 'drops',
    'dsx_minigun_flamethrower2': 'drops',
    'dsx_minigun_grenade_launcher': 'drops',
    'dsx_gobbot_grenade_launcher': 'drops',
    'dsx_minigun_lightning': 'drops',
    'minigun_napalm': 'drops',
    'minigun_gas': 'drops',
    'st_g_c_dsx_stars': 'drop',
    '2w_st_g_c_dsx_stars': 'drop',
    '3w_st_g_c_dsx_stars': 'drop',
    # loa inaccessible
    'dsx_minigun_gas_monster': 'enemy',
    'minigun_magic_missles': 'unused',
    'sd_g_c_dsx_kat_1h_shadowjumper_NIS_ONLY': 'nis',
    'st_g_c_dsx_pcane': 'unused',
    'st_un_dsx_angk_guardian': 'enemy',
    'sd_d_c_dsx_skl_1h_mag': 'enemy',
    'ax_g_c_1h2b_low_dsx': 'enemy',
    'ax_d_c_1h1b_avg_dsx': 'enemy',
    'mc_dsx_cicatrix_skeleton': 'enemy',
    'bw_dsx_cicatrix_skeleton': 'enemy',
    'dsx_rock_goblin': 'enemy',
    'bw_dsx_shadjump_2_avg': 'enemy',
    'bw_dsx_shadjump_4_avg': 'enemy',
    'bw_dsx_zau_2': 'unused',
    'bw_dsx_zau_2_a': 'enemy',
    'bw_dsx_zau_2_b': 'unused',
    'bw_dsx_zau_2_c': 'enemy',
    'bw_dsx_zau_2_d': 'enemy',
    'bw_dsx_zaurask_2_b': 'enemy',
    'bw_un_droog_avg_dsx': 'unused',
    'bw_dsx_hassat': 'unused',
    'bw_dsx_hassat_01': 'enemy',
    'bw_dsx_hassat_02': 'enemy',
    'bw_dsx_hassat_03': 'enemy',
    'bw_g_c_s_s_r_avg_dsx': 'enemy',
    'bw_dsx_rune_caster': 'unused',
    'cb_un_1h_troll_dsx_scrub': 'enemy',
    'cb_un_2h_troll_dsx_forest': 'enemy',
    'cb_un_dsx_2h_troll': 'enemy',
    'dg_g_c_dsx_kaj_mag': 'enemy',
    'dg_g_c_dsx_sjumper_three': 'enemy',
    'dg_g_c_dsx_sjumper_five': 'enemy',
    'hm_g_c_dsx_goblin_blackguard': 'enemy',
    'hm_g_c_dsx_warmlt_avg': 'unused',
    'ax_d_d_dsx_goblin_mutant': 'enemy',
    'st_g_c_bl_1h_fun_nossirom_dsx': 'enemy',
    'st_un_toreck_dsx': 'enemy',  # scrub howler
    'st_un_seck_mage_dsx': 'enemy',  # necron
    'sd_g_c_dsx_kat_1h_shadowjumper': 'enemy',
    'ss_g_c_bl_1h_fun_zaur_dsx': 'enemy',
    'ss_g_c_bl_1h_fun_noss_dsx': 'unused',
    'ss_g_c_bl_1h_fun_dsx': 'enemy',
    'ss_g_c_bl_1h_fun_01_dsx': 'enemy',
    'ss_g_c_bl_1h_fun_02_dsx': 'enemy',
    'ss_g_c_bl_1h_fun_03_dsx': 'enemy',
    'ss_g_c_bl_1h_fun_04_dsx': 'enemy',
    'ss_g_c_bl_1h_fun_05_dsx': 'enemy',
    'sd_g_c_sd_1h_avg_dsx': 'enemy',
    'sd_g_c_dsx_goblin_guard': 'enemy',
}


def parse_equip_requirements(value: str) -> dict[str, int]:
    reqs = dict()
    req_strs = value.split(',')
    for req_str in req_strs:
        stat, val_str = req_str.split(':')
        reqs[stat.strip()] = int(val_str)
    return reqs


class PContentVariant:
    KNOWN_ATTRS = [
        'modifier_min', 'modifier_max', 'equip_requirements', 'inventory_icon', 'pcontent_special_type',
        'armor_style', 'armor_type', 'inventory_height', 'inventory_width', 'model', 'texture', 'active_icon',
        'defense', 'damage_min', 'damage_max',
    ]

    def __init__(self, name: str, modifier_min: float = None, modifier_max: float = None, equip_requirements: dict[str, int] = None, inventory_icon: str = None, pcontent_special_type: str = None):
        self.name = name
        self.modifier_min = modifier_min
        self.modifier_max = modifier_max
        self.equip_requirements = equip_requirements
        self.inventory_icon = inventory_icon
        self.pcontent_special_type = pcontent_special_type

    @classmethod
    def parse(cls, section: Section) -> 'PContentVariant':
        attr_names = [a.name for a in section.get_attrs()]
        for attr_name in attr_names:
            assert attr_name in cls.KNOWN_ATTRS, attr_name

        name = section.header
        modifier_min = section.get_attr_value('modifier_min')
        modifier_max = section.get_attr_value('modifier_max')
        equip_requirements_value = section.get_attr_value('equip_requirements')
        equip_requirements = None if equip_requirements_value is None else parse_equip_requirements(equip_requirements_value)
        inventory_icon = section.get_attr_value('inventory_icon')
        pcontent_special_type = section.get_attr_value('pcontent_special_type')
        return PContentVariant(name, modifier_min, modifier_max, equip_requirements, inventory_icon, pcontent_special_type)


def get_pcontent_variants(template: Template) -> list[PContentVariant]:
    var_secs = []
    while template is not None:
        pcontent_section = template.section.get_section('pcontent')
        if pcontent_section:
            var_secs.extend(pcontent_section.get_sections())
        template = template.parent_template
    return [PContentVariant.parse(s) for s in var_secs]


class Equipment:
    def __init__(self, template: Template, is_dsx: bool, usage: str):
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

        self.variants = get_pcontent_variants(template)

        reqs_str = template.compute_value('gui', 'equip_requirements')
        self.equip_requirements = parse_equip_requirements(reqs_str) if reqs_str is not None else dict()
        self.req_stat = self.get_equip_requirement_stat(self.equip_requirements)
        if self.req_stat == 'int':
            if not (self.tn_stance == 'm' or self.tn_stance is None):
                print(f'wtf tn-stance {template.name}')
        if self.req_stat == 'dex':
            if not (self.tn_stance == 'r' or self.tn_stance is None):
                print(f'wtf tn-stance {template.name}')

        if not self.decide_stance():
            print(f'undecided stance {template.name}')

        self.is_pcontent_allowed = parse_bool_value(template.compute_value('common', 'is_pcontent_allowed'), True)

        self.usage = 'pcontent' if self.is_pcontent_allowed else usage
        self.is_accessible = True if self.is_pcontent_allowed else self.usage in ACCESSIBLE_USAGES

        self.item_set = template.compute_value('set_item', 'set_compare_name')

        self.inventory_icon = template.compute_value('gui', 'inventory_icon')

        is_2h_val = template.compute_value('attack', 'is_two_handed')
        self.is_2h = parse_bool_value(is_2h_val) if is_2h_val != '2' else None  # wtf Guiseppi's Bow

        self.can_sell = parse_bool_value(template.compute_value('gui', 'can_sell'), True)

        tn_segs = self.template_name.split('_')
        self.tn_red_flag = 'temp' in tn_segs or 'NIS' in tn_segs

    def decide_stance(self, req_stat: str = None):
        if req_stat is None:
            req_stat = self.req_stat
        # if sth requires dex or int, it's for rangers / mages
        if req_stat == 'dex':
            return 'r'
        if req_stat == 'int':
            return 'm'
        # with str reqs we can't be so sure
        if self.weapon_kind == 'ranged':
            return 'r'
        if self.weapon_type == 'st' and req_stat != 'str':
            return 'm'  # staves are for mages by default
        if self.weapon_kind == 'melee':
            return 'f'
        if self.material == 'ro' and req_stat == 'str':  # wtf molten boots
            return 'f'
        # let's check what the template name says
        if self.tn_stance:
            return self.tn_stance
        if req_stat == 'str':
            return 'f'
        # if material is robe, it's for mages
        if self.material == 'ro':
            return 'm'
        # shield without any requirements - fighter
        if self.armor_type == 'sh':
            return 'f'
        # no idea - hopefully all that's left now is bo_bo_le_light
        return None

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
    def get_equip_requirement_stat(cls, reqs: dict[str, int]):
        req_stats = list(reqs.keys())

        is_str = 'strength' in req_stats
        is_dex = 'dexterity' in req_stats
        is_int = 'intelligence' in req_stats
        if is_str + is_dex + is_int > 1:
            return 'multi'
        return 'str' if is_str else 'dex' if is_dex else 'int' if is_int else None


def load_dsx_equipment_template_names(bits: Bits) -> list[str]:
    templates = {}
    template_base_dir = bits.templates.gas_dir
    interactive_dir = template_base_dir.get_subdir(['regular', 'interactive'])
    for gas_file_name, gas_file in interactive_dir.get_gas_files().items():
        if gas_file_name.startswith('dsx_'):
            bits.templates.load_templates_file(interactive_dir.get_gas_file(gas_file_name), templates)
    # templates are unconnected but we only return the names anyway
    return list(templates.keys())


def load_equipment_templates(bits: Bits) -> tuple[list[str], list[Template]]:
    dsx_equipment_template_names = load_dsx_equipment_template_names(bits)
    equipment_templates = list()
    equipment_templates.extend(bits.templates.get_leaf_templates('armor').values())
    equipment_templates.extend(bits.templates.get_leaf_templates('weapon').values())
    return dsx_equipment_template_names, equipment_templates


def process_equipments(equipment_templates: list[Template], dsx_equipment_template_names: list[str], equipment_usages: dict[str, str]) -> list[Equipment]:
    return [
        Equipment(equipment_template, equipment_template.name.lower() in dsx_equipment_template_names, equipment_usages.get(equipment_template.name.lower()))
        for equipment_template in equipment_templates
        if not equipment_template.has_component('generator_multiple_mp')
    ]


def make_equipments_csv(equipments: list[Equipment]):
    keys = ['template', 'screen_name', 'stance', 'is_dsx', 'eq_type', 'world_level', 'excluded', 'set', 'item_type', 'rarity', 'material', 'tn_stance', 'req_stat', 'icon', 'variants']
    headers = {
        'template': 'Template', 'screen_name': 'Screen Name',
        'is_dsx': 'LoA', 'eq_type': 'Equipment Type', 'world_level': 'World Level', 'excluded': 'Excluded', 'set': 'Item Set',
        'item_type': 'Item Type', 'rarity': 'Rarity', 'material': 'Material', 'tn_stance': 'TN Stance', 'req_stat': 'Req. Stat', 'icon': 'Icon',
        'variants': 'Variants',
        'stance': 'Stance',
    }
    data = []
    for item in equipments:
        row = {
            'template': item.template_name,
            'screen_name': item.screen_name,
            'is_dsx': 'LoA' if item.is_dsx else None,
            'eq_type': item.equipment_type,
            'world_level': {'2w': 'Veteran', '3w': 'Elite'}.get(item.world_level),
            'excluded': 'excluded' if item.is_pcontent_allowed is False else None,
            'set': item.item_set,
            'item_type': item.armor_type if item.equipment_type == 'armor' else item.weapon_type if item.equipment_type == 'weapon' else None,
            'rarity': {'ra': 'rare', 'un': 'unique'}.get(item.rarity),
            'material': item.material,
            'tn_stance': item.tn_stance,
            'req_stat': item.req_stat,
            'icon': item.inventory_icon,
            'variants': ', '.join([v.name for v in item.variants]),
            'stance': {'f': 'Fighter', 'r': 'Ranger', 'm': 'Mage'}.get(item.decide_stance()),
        }
        data.append(row)
    return keys, headers, data


def printout_equipment(bits: Bits, output_dir='output'):
    dsx_equipment_template_names, equipment_templates = load_equipment_templates(bits)
    equipments = process_equipments(equipment_templates, dsx_equipment_template_names, EQUIPMENT_USAGE)
    equipments_csv = make_equipments_csv(equipments)
    write_csv_dict('equipments', *equipments_csv, sep=';', quote_cells=False, output_dir=output_dir)


def equipment(bits_path: str, output_dir='output'):
    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)
    printout_equipment(bits, output_dir)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Equipment')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--out', default='output')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    equipment(args.bits, args.out)


if __name__ == '__main__':
    main(sys.argv[1:])
