import os

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from bits.templates import Template


class Enemy:
    def __init__(self, template):
        assert isinstance(template, Template)
        self.template = template
        self.template_name = template.name.lower()
        self.screen_name: str = template.compute_value('common', 'screen_name')
        self.xp = int(template.compute_value('aspect', 'experience_value') or '0')
        self.life = int(float(template.compute_value('aspect', 'max_life') or '0'))
        self.defense = float(template.compute_value('defend', 'defense') or '0')


def load_enemies(bits: Bits, world_levels=False) -> list[Enemy]:
    enemies = bits.templates.get_enemy_templates()
    if not world_levels:
        enemies = [e for n, e in enemies.items() if not (n.startswith('2w_') or n.startswith('3w_'))]
    else:
        enemies = enemies.values()
    enemies = [e for e in enemies if 'base' not in e.name.split('_')]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name.split('_')]
    enemies = [e for e in enemies if 'nis' not in e.name.split('_')]  # e.g. shadowjumper
    enemies = [Enemy(e) for e in enemies]
    # print(repr([e.template_name for e in enemies]))
    return sorted(enemies, key=lambda x: x.template_name)


def load_level_xp():
    level_file_path = os.path.join('input', 'XP Chart.csv')
    with open(level_file_path) as level_file:
        level_xp = [int(line.split(',')[1]) for line in level_file]
    return level_xp


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


def get_level(xp, level_xp):
    level = 0
    while level + 1 < len(level_xp) and level_xp[level + 1] <= xp:
        level += 1
    return level


class RegionXP:
    def __init__(self, region: Region, weight: float = 1, world_level='regular'):
        self.region = region
        self.name = region.gas_dir.dir_name
        # print(self.name)
        self.xp = region.get_xp(world_level)
        self.weight = weight
        self.xp_pre = None
        self.xp_post = None
        self.pre_level = None
        self.post_level = None
        self.world_level = world_level

    def set_pre_xp(self, pre_xp, level_xp):
        self.xp_pre = pre_xp
        self.xp_post = pre_xp + self.xp*self.weight
        self.pre_level = get_level(pre_xp, level_xp)
        self.post_level = get_level(self.xp_post, level_xp)
        return self.xp_post

    @property
    def xp_weighted(self):
        return self.xp * self.weight


def load_regions_xp(m: Map, world_levels: bool = None, start_level=0) -> list[RegionXP]:
    if world_levels is None:
        world_levels = m.is_multi_world()
    world_levels = ['regular'] if not world_levels else ['regular', 'veteran', 'elite']
    ordered_regions = load_ordered_regions(m)
    level_xp = load_level_xp()
    regions_xp = [RegionXP(region_name, weight, world_level) for world_level in world_levels for region_name, weight in ordered_regions]
    xp = level_xp[start_level]
    for rx in regions_xp:
        if rx.world_level == 'veteran':
            xp = max(xp, level_xp[54])
        if rx.world_level == 'elite':
            xp = max(xp, level_xp[83])
        xp = rx.set_pre_xp(xp, level_xp)
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
