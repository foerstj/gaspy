import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from printouts.common import load_enemies, Enemy, load_regions_xp, load_level_xp, get_level
from printouts.csv import write_csv
from gas.gas import Section
from gas.gas_parser import GasParser
from bits.templates import Template
from gas.molecules import PContentSelector
from printouts.enemy_occurrence import print_enemy_occurrence
from printouts.level_enemies import write_level_enemies_csv
from printouts.map_levels import write_map_levels_csv
from printouts.world_level_shrines import print_world_level_shrines


class EnemyEncounter:
    def __init__(self, enemy: Enemy, xp_at_first_encounter: int, region: Region, level: int):
        self.enemy = enemy
        self.xp_at_first_encounter = xp_at_first_encounter
        self.region = region
        self.level = level


def calc_xp_gradient(bits: Bits, m: Map, world_levels=False) -> dict[str, EnemyEncounter]:
    enemies = load_enemies(bits, True)
    enemies_by_tn: dict[str, Enemy] = {e.template_name: e for e in enemies}
    level_xp = load_level_xp()

    region_xp = load_regions_xp(m, world_levels)
    enemy_encounters = dict()  # dict enemy template name -> encounter data
    for rxp in region_xp:
        region = rxp.region
        region_enemy_gos = region.get_enemy_actors(rxp.world_level)
        region_enemy_template_names_list = [e.template_name.lower() for e in region_enemy_gos]
        region_enemy_template_names = set(region_enemy_template_names_list)
        region_enemy_template_counts = {template_name: 0 for template_name in region_enemy_template_names}
        for template_name in region_enemy_template_names_list:
            region_enemy_template_counts[template_name] += 1
        # let's assume the player does all the least-powerful enemies of the region first, then the next-powerful ones etc.
        region_enemies: list[Enemy] = [enemies_by_tn[template_name] for template_name in region_enemy_template_names]
        region_enemies = sorted(region_enemies, key=lambda x: x.xp)
        region_xp = 0
        for region_enemy in region_enemies:
            if region_enemy.template_name not in enemy_encounters:
                xp_at_first_encounter = int(rxp.xp_pre + region_xp)
                level = get_level(xp_at_first_encounter, level_xp)
                enemy_encounters[region_enemy.template_name] = EnemyEncounter(region_enemy, xp_at_first_encounter, region, level)
            count = region_enemy_template_counts[region_enemy.template_name]
            region_xp += count * region_enemy.xp
        # assert region_xp == rxp.xp, f'{rxp.name}: {region_xp} != {rxp.xp}'  # numbers don't add up because I'm omitting generators for now
    return enemy_encounters


def write_xp_gradient_csv(bits: Bits, m: Map, world_levels=False):
    enemy_encounters = calc_xp_gradient(bits, m, world_levels)

    for template_name, encounter in enemy_encounters.items():
        print(f'Enemy {template_name} ({encounter.enemy.xp} XP)'
              f' is first encountered in region {encounter.region.get_name()}'
              f' with estimated {encounter.xp_at_first_encounter} player XP (level {encounter.level})')

    csv_header = ['Enemy', 'Enemy XP', 'Region', 'Player XP', 'Player level']
    csv = [csv_header]
    for template_name, encounter in enemy_encounters.items():
        csv.append([template_name, encounter.enemy.xp, encounter.region.get_name(), encounter.xp_at_first_encounter, encounter.level])
    write_csv(f'xp gradient {m.get_name()}', csv)


def wl_actor_skill(template: Template, skill_name: str):
    skill_value = template.compute_value('actor', 'skills', skill_name)
    if skill_value is None:
        return None
    return skill_value.split(',')[0]


def wl_actor_dict(template: Template):
    return {
        'experience_value': template.compute_value('aspect', 'experience_value'),
        'defense': template.compute_value('defend', 'defense'),
        'damage_min': template.compute_value('attack', 'damage_min'),
        'damage_max': template.compute_value('attack', 'damage_max'),
        'life': template.compute_value('aspect', 'life'),
        'max_life': template.compute_value('aspect', 'max_life'),
        'mana': template.compute_value('aspect', 'mana'),
        'max_mana': template.compute_value('aspect', 'max_mana'),
        'strength': wl_actor_skill(template, 'strength'),
        'dexterity': wl_actor_skill(template, 'dexterity'),
        'intelligence': wl_actor_skill(template, 'intelligence'),
        'melee': wl_actor_skill(template, 'melee'),
        'ranged': wl_actor_skill(template, 'ranged'),
        'combat_magic': wl_actor_skill(template, 'combat_magic'),
        'nature_magic': wl_actor_skill(template, 'nature_magic'),
    }


def none_empty(values: list):
    return [v if v is not None else '' for v in values]


def get_wl_templates(templates: dict[str, Template]) -> dict[str, dict[str, Template]]:  # dict[name.lower: template] -> dict[name.lower: dict[WL: template]]
    wls = {'veteran': '2W', 'elite': '3W'}
    wls_templates: dict[str, dict[str, Template]] = dict()
    for name, template in templates.items():
        if name.startswith('2w_') or name.startswith('3w_'):
            continue
        wl_templates = {'regular': template, 'veteran': None, 'elite': None}
        for wl, wl_prefix in wls.items():
            wl_template = templates.get(f'{wl_prefix.lower()}_{name}')
            if wl_template is None:
                continue
            wl_templates[wl] = wl_template
            wls_templates[name] = wl_templates
    return wls_templates


def write_world_level_stats_csv(bits: Bits):
    actors = bits.templates.get_actor_templates()
    wls_actors = get_wl_templates(actors)

    wls = ['regular', 'veteran', 'elite']
    skill_stats = ['strength', 'dexterity', 'intelligence', 'melee', 'ranged', 'combat_magic', 'nature_magic']
    other_stats = ['defense', 'damage_min', 'damage_max', 'life', 'max_life', 'mana', 'max_mana']
    stats = ['experience_value'] + other_stats + skill_stats
    csv = [['actor'] + [f'{wl} {stat}' for stat in stats for wl in wls]]
    for name, wl_actors in wls_actors.items():
        actors = [wl_actor_dict(wl_actors[wl]) for wl in wls]
        csv_line = [name]
        for stat in stats:
            wl_stats = [a[stat] for a in actors]
            wl_stats = [s.split()[0] if s is not None else None for s in wl_stats]  # dsx_zaurask_commander damage_max garbage after missing semicolon
            csv_line += none_empty(wl_stats)
        csv.append(csv_line)
    write_csv('World-Level Stats', csv)


def write_world_level_gold_csv(bits: Bits):
    templates = bits.templates.get_actor_templates(False)
    templates.update(bits.templates.get_container_templates(False))
    wls_templates = get_wl_templates(templates)
    wls = ['regular', 'veteran', 'elite']
    stats = ['min', 'max']
    csv = [['template'] + [f'{wl} {stat}' for stat in stats for wl in wls]]
    for name, wl_templates in wls_templates.items():
        wls_gold_sections = {wl: template.section.find_sections_recursive('gold*') for wl, template in wl_templates.items()}
        counts = [len(sections) for sections in wls_gold_sections.values()]
        if len(set(counts)) != 1:
            print('Warning: differing numbers of gold sections in ' + name)
            continue
        for i in range(counts[0]):
            wl_gold_sections = [wls_gold_sections[wl][i] for wl in wls]
            csv_line = [name]
            for stat in stats:
                wl_stats = [gs.get_attr_value(stat) for gs in wl_gold_sections]
                csv_line += none_empty(wl_stats)
            csv.append(csv_line)
    write_csv('World-Level Gold', csv)


PCONTENT_CATEGORIES = {
    'spell': ['spell', 'cmagic', 'nmagic', 'combat_magic', 'nature_magic'],
    'armor': ['armor', 'body', 'gloves', 'boots', 'shield', 'helm'],
    'jewelry': ['amulet', 'ring'],
    'weapon': ['weapon', 'melee', 'ranged', 'axe', 'club', 'dagger', 'hammer', 'mace', 'staff', 'sword', 'bow', 'minigun'],
    '*': ['*'],
}


def get_pcontent_category(pcontent_type):
    for cat, types in PCONTENT_CATEGORIES.items():
        if pcontent_type in types:
            return cat
    if pcontent_type in ['spellbook']:
        return 'other'
    print(f'Warning: missing pcontent categorization for {pcontent_type}')
    return None


def write_world_level_pcontent_csv(bits: Bits):
    templates = bits.templates.get_actor_templates(False)
    templates.update(bits.templates.get_container_templates(False))
    wls_templates = get_wl_templates(templates)
    wls = ['regular', 'veteran', 'elite']
    csv = [['template'] + [f'{wl} {pc_cat}' for pc_cat in PCONTENT_CATEGORIES for wl in wls]]
    for name, wl_templates in wls_templates.items():
        print(name)
        wls_pcontent_sections = {wl: template.section.find_sections_recursive('pcontent') + template.section.find_sections_recursive('store_pcontent') for wl, template in wl_templates.items()}
        section_counts = [len(sections) for sections in wls_pcontent_sections.values()]
        if len(set(section_counts)) != 1:
            print('Warning: differing numbers of pcontent sections in ' + name)
            continue
        for i in range(section_counts[0]):
            wl_pcontent_sections: list[Section] = [wls_pcontent_sections[wl][i] for wl in wls]
            wls_il_main_attrs = [s.find_attrs_recursive('il_main') for s in wl_pcontent_sections]
            attr_counts = [len(attrs) for attrs in wls_il_main_attrs]
            if len(set(attr_counts)) != 1:
                print('Warning: differing numbers of pcontent il_main attrs in ' + name)
                continue
            for j in range(attr_counts[0]):
                wl_il_main_attrs = [attrs[j] for attrs in wls_il_main_attrs]
                if any([not a.value.startswith('#') for a in wl_il_main_attrs]):
                    continue
                wl_selector_strs = [attr.value.split()[0] for attr in wl_il_main_attrs]  # remove garbage behind missing semicolon
                wl_selectors = [PContentSelector.parse(pcs_str) for pcs_str in wl_selector_strs]
                wl_item_types = [pcs.item_type for pcs in wl_selectors]
                if len(set(wl_item_types)) != 1:
                    print(f'Warning: different pcontent types in {name}: {wl_item_types}')
                    continue
                pc_cat = get_pcontent_category(wl_item_types[0])
                if pc_cat not in PCONTENT_CATEGORIES:
                    continue  # unhandled pcontent category
                wl_powers = [pcs.power for pcs in wl_selectors]
                wl_range_segs = [list(p) if isinstance(p, tuple) else [p] for p in wl_powers]
                if len(set([len(segs) for segs in wl_range_segs])) != 1:
                    print(f'Warning: different pcontent range defs in {name}')
                    continue
                for k in range(len(wl_range_segs[0])):
                    wl_pcontent_powers = [r[k] for r in wl_range_segs]
                    csv_line = [name]
                    for iter_pc_cat in PCONTENT_CATEGORIES:
                        if iter_pc_cat == pc_cat:
                            csv_line.extend(wl_pcontent_powers)
                        else:
                            csv_line.extend([None for _ in wls])
                    csv.append(none_empty(csv_line))
    write_csv('World-Level PContent', csv)


def get_map(bits: Bits, map_name: str) -> Map:
    assert map_name, 'No map name given'
    assert map_name in bits.maps, f'Map {map_name} does not exist'
    return bits.maps[map_name]


def init_arg_parser():
    which_choices = ['level-enemies', 'enemy-occurrence', 'enemies', 'map-levels', 'world-level-shrines', 'world-level-stats', 'world-level-gold', 'world-level-pcontent', 'xp-gradient']
    parser = argparse.ArgumentParser(description='GasPy statistics')
    parser.add_argument('which', choices=which_choices)
    parser.add_argument('--bits', default=None)
    parser.add_argument('--map-name', nargs='?')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    GasParser.get_instance().print_warnings = False
    bits = Bits(args.bits)
    which = args.which
    if which == 'level-enemies':
        write_level_enemies_csv(bits)
    elif which == 'enemy-occurrence':
        print_enemy_occurrence(bits)
    elif which == 'map-levels':
        write_map_levels_csv(get_map(bits, args.map_name))
    elif which == 'world-level-shrines':
        print_world_level_shrines(get_map(bits, args.map_name))
    elif which == 'world-level-stats':
        write_world_level_stats_csv(bits)
    elif which == 'world-level-gold':
        write_world_level_gold_csv(bits)
    elif which == 'world-level-pcontent':
        write_world_level_pcontent_csv(bits)
    elif which == 'xp-gradient':
        # this should basically give a rough overview of the steepness of the difficulty of a map.
        # using player xp/level as player power, and enemy xp as enemy power.
        write_xp_gradient_csv(bits, get_map(bits, args.map_name))
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
