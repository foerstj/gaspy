import os

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from bits.templates import Template
from printouts.level_xp import get_level, load_level_xp


def parse_bool_value(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return {'true': True, 'false': False}[value.lower()]
    assert False, value


def parse_value(value, default=None):
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    try:
        return int(value.split()[0])  # dsx_zaurask_commander (missing semicolon)
    except ValueError:
        pass

    assert False, value


# It's not just krug_scavenger's defense - it's also all the 2W and 3W templates
def parse_int_value(value, default=None):
    value = parse_value(value, default)
    return int(value) if value is not None else None


def is_shield(tn: str):
    return tn.startswith('sh_') or tn.startswith('#shield')


def compute_skill_level(template: Template, skill: str) -> int:
    skill_lvl = template.compute_value('actor', 'skills', skill)
    if skill_lvl is None:
        skill_lvl = 0
    else:
        assert '#' not in skill_lvl
        skill_lvl = int(float(skill_lvl.split(',')[0].strip()))  # float e.g. dsx_armor_deadly strength
    return skill_lvl


class Enemy:
    def __init__(self, template):
        assert isinstance(template, Template)
        self.template = template
        self.template_name = template.name.lower()
        screen_name: str = template.compute_value('common', 'screen_name')
        self.screen_name = screen_name.strip('"') if screen_name is not None else None
        self.xp = parse_value(template.compute_value('aspect', 'experience_value'), 0)
        self.life = parse_int_value(template.compute_value('aspect', 'max_life'), 0)
        self.mana = parse_int_value(template.compute_value('aspect', 'max_mana'), 0)
        self.defense = parse_int_value(template.compute_value('defend', 'defense'), 0)
        self.melee_lvl = compute_skill_level(template, 'melee')
        self.ranged_lvl = compute_skill_level(template, 'ranged')
        self.combat_magic_lvl = compute_skill_level(template, 'combat_magic')
        self.nature_magic_lvl = compute_skill_level(template, 'nature_magic')
        self.strength = compute_skill_level(template, 'strength')
        self.dexterity = compute_skill_level(template, 'dexterity')
        self.intelligence = compute_skill_level(template, 'intelligence')
        self.icz_melee = parse_bool_value(template.compute_value('mind', 'on_enemy_entered_icz_switch_to_melee'))
        self.selected_active_location = (template.compute_value('inventory', 'selected_active_location') or 'il_active_melee_weapon').lower()
        self.switches2melee = parse_bool_value(template.compute_value('mind', 'actor_auto_switches_to_melee'), True)
        self.switches2ranged = parse_bool_value(template.compute_value('mind', 'actor_auto_switches_to_ranged'))
        self.switches2magic = parse_bool_value(template.compute_value('mind', 'actor_auto_switches_to_magic'))

    def is_melee(self):
        if self.template_name == 'xp_salamander_red':  # sigh
            return True
        return self.selected_active_location == 'il_active_melee_weapon' or self.icz_melee

    def is_ranged(self):
        if self.template_name == 'xp_salamander_red':  # sigh
            return False
        return self.selected_active_location in ['il_active_ranged_weapon', 'il_hand_1', 'il_hand_2'] or self.switches2ranged

    def is_magic(self):
        return self.selected_active_location in ['il_active_primary_spell', 'il_active_secondary_spell', 'il_spell_1', 'il_spell_2']


def load_enemies(bits: Bits, world_levels=False) -> list[Enemy]:
    enemies = bits.templates.get_enemy_templates()
    enemies = list(enemies.values())
    if not world_levels:
        enemies = [e for e in enemies if not e.wl_prefix]
    enemies = [e for e in enemies if 'base' not in e.name.split('_')]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name.split('_')]
    enemies = [e for e in enemies if '_reveal' not in e.name and not e.name.endswith('_ar') and not e.name.endswith('_act')]
    enemies = [e for e in enemies if '_nis_' not in e.name and not e.name.startswith('test_')]
    enemies = [Enemy(e) for e in enemies]
    enemies = [e for e in enemies if e.screen_name is not None]  # dsx_drake
    # print(repr([e.template_name for e in enemies]))
    return sorted(enemies, key=lambda x: x.template_name)


def load_ordered_regions(m: Map) -> list[tuple[Region, float]]:
    regions = m.get_regions()
    order_file_path = os.path.join('input', m.get_name() + '.txt')
    if os.path.isfile(order_file_path):
        ordered_regions = []
        with open(order_file_path) as order_file:
            for line in order_file.readlines():
                line = line.split('#')[0].strip()
                if not line:
                    continue
                line = line.split(',')
                region_name = line[0]
                region_weight = float(line[1]) if len(line) > 1 else 1.0
                ordered_regions.append((regions[region_name], region_weight))
    else:
        ordered_regions = [(r, 1.0) for r in regions.values()]
    return ordered_regions


class RegionXP:
    def __init__(self, region: Region, weight: float = 1, world_level='regular', level_xp: list[int] = None):
        self.region = region
        self.level_xp = level_xp
        self.weight = weight
        self.world_level = world_level
        self.xp_pre = None
        self.add_xp = 0

        self.name = region.gas_dir.dir_name
        self.xp = region.get_xp(world_level)

    @property
    def xp_weighted(self):
        return (self.xp + self.add_xp) * self.weight

    @property
    def xp_post(self):
        return self.xp_pre + self.xp_weighted

    @property
    def pre_level(self):
        return get_level(self.xp_pre, self.level_xp)

    @property
    def post_level(self):
        return get_level(self.xp_post, self.level_xp)


def load_regions_xp(m: Map, world_levels: bool = None, start_level=0, add_region_xp: dict[str, int] = None) -> list[RegionXP]:
    if add_region_xp is None:
        add_region_xp = dict()

    if world_levels is None:
        world_levels = m.is_multi_world()
    world_levels = ['regular'] if not world_levels else ['regular', 'veteran', 'elite']
    ordered_regions = load_ordered_regions(m)
    level_xp = load_level_xp()

    regions_xp = [RegionXP(region, weight, world_level, level_xp) for world_level in world_levels for region, weight in ordered_regions]
    regions_xp_dict = {rx.region.get_name(): rx for rx in regions_xp}
    for region_name, add_xp in add_region_xp.items():
        regions_xp_dict[region_name].add_xp = add_xp

    # iterate through regions, passing xp from one to the next
    xp = level_xp[start_level]
    for rx in regions_xp:
        if rx.world_level == 'veteran':
            xp = max(xp, level_xp[54])
        if rx.world_level == 'elite':
            xp = max(xp, level_xp[83])
        rx.xp_pre = xp
        xp = rx.xp_post
    return regions_xp


def get_wl_templates(templates: dict[str, Template]) -> dict[str, dict[str, Template]]:  # dict[name.lower: template] -> dict[name.lower: dict[WL: template]]
    wls = {'veteran': '2W', 'elite': '3W'}
    wls_templates: dict[str, dict[str, Template]] = dict()
    for name, template in templates.items():
        if name.startswith('2w_') or name.startswith('3w_'):
            continue
        wl_templates = {'regular': template, 'veteran': None, 'elite': None}
        for wl, wl_prefix in wls.items():
            wl_name = f'{wl_prefix.lower()}_{name}'
            # if name == 'molten_golem_summon_gom':
            #     wl_name = '2_molten_golem_summon_gom'  # how could they
            wl_template = templates.get(wl_name)
            if wl_template is None:
                continue
            wl_templates[wl] = wl_template
            wls_templates[name] = wl_templates
    return wls_templates


def none_empty(values: list):
    return [v if v is not None else '' for v in values]
