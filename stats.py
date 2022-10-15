import argparse
import os
import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from csv import write_csv
from gas.gas import Section
from gas.gas_parser import GasParser
from bits.templates import Template
from gas.molecules import PContentSelector


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
                line = line.strip()
                if not line or line.startswith('#'):
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
    while level_xp[level + 1] <= xp:
        level += 1
    return level


class RegionXP:
    def __init__(self, region: Region, weight=1, world_level='regular'):
        self.region = region
        self.name = region.gas_dir.dir_name
        print(self.name)
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


def load_regions_xp(m: Map, world_levels: bool = None) -> list[RegionXP]:
    if world_levels is None:
        world_levels = m.is_multi_world()
    world_levels = ['regular'] if not world_levels else ['regular', 'veteran', 'elite']
    ordered_regions = load_ordered_regions(m)
    level_xp = load_level_xp()
    regions_xp = [RegionXP(*r, world_level=wl) for wl in world_levels for r in ordered_regions]
    xp = 0
    for rx in regions_xp:
        xp = rx.set_pre_xp(xp, level_xp)
    return regions_xp


# Ordered regions -> how much XP, and what lvl the player will be at
def write_map_levels_csv(m: Map):
    regions_xp = load_regions_xp(m, False)
    data = [['world level', 'region', 'xp', 'weight', 'xp', 'sum', 'level pre', 'level post']]
    for r in regions_xp:
        data.append([r.world_level, r.name, r.xp, r.weight, r.xp*r.weight, r.xp_post, r.pre_level, r.post_level])
    write_csv(m.gas_dir.dir_name, data)


class Enemy:
    def __init__(self, template):
        assert isinstance(template, Template)
        self.template = template
        self.template_name = template.name.lower()
        self.screen_name: str = template.compute_value('common', 'screen_name')
        self.xp = int(template.compute_value('aspect', 'experience_value') or '0')
        self.life = int(float(template.compute_value('aspect', 'max_life') or '0'))
        self.defense = float(template.compute_value('defend', 'defense') or '0')


def load_enemies(bits: Bits, world_levels=False):
    enemies = bits.templates.get_enemy_templates()
    if not world_levels:
        enemies = [e for n, e in enemies.items() if not (n.startswith('2w_') or n.startswith('3w_'))]
    else:
        enemies = enemies.values()
    enemies = [e for e in enemies if 'base' not in e.name]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name]
    enemies = [Enemy(e) for e in enemies]
    # print(repr([e.template_name for e in enemies]))
    return sorted(enemies, key=lambda x: x.template_name)


# Print out which enemies occur in which regions
def print_enemy_occurrence(bits: Bits):
    maps = ['map_world', 'multiplayer_world', 'map_expansion']
    maps = {n: bits.maps[n] for n in maps}
    enemies = load_enemies(bits)
    enemy_regions = {e.template_name: list() for e in enemies}
    enemies_by_tn = {e.template_name: e for e in enemies}
    for map_name, m in maps.items():
        print('Map ' + map_name)
        region_xp = load_regions_xp(m, False)
        for rxp in region_xp:
            region = rxp.region
            region_enemies = region.get_enemy_actors()
            region_enemy_template_names = {e.template_name for e in region_enemies}
            region_enemy_strs = [tn + ' ('+str(enemies_by_tn[tn].xp)+' XP)' for tn in region_enemy_template_names]
            region_enemies_str = str(len(region_enemy_template_names)) + ' enemy types: ' + ', '.join(region_enemy_strs)
            print('Region ' + region.get_name() + ' (XP '+str(rxp.xp_pre)+' - '+str(rxp.xp_post)+') contains ' + region_enemies_str)
            for retn in region_enemy_template_names:
                enemy_regions[retn].append(rxp)
    for enemy in enemies:
        rxps = enemy_regions[enemy.template_name]
        region_strs = [rxp.name + ' (XP '+str(rxp.xp_pre)+' - '+str(rxp.xp_post)+')' for rxp in rxps]
        regions_str = str(len(rxps)) + ' regions: ' + ', '.join(region_strs)
        print('Enemy type ' + enemy.template_name + ' (' + str(enemy.xp) + ' XP) occurs in ' + regions_str)


def categorize_enemy(enemy_template_name):
    enemy_parts: list = enemy_template_name.split('_')
    nonsense = [
        ['01', '02', '03', '04', '05', 'one', 'two', 'three', 'four', 'five', '2'],  # numbering
        ['dsx'],  # loa dsx
        ['reveal', 'act', 'temp', 'poking', 'eating', 'r', 'q', 'summon', 'mp', 'lhaoc'],  # reveal effect
        [  # theming
            'white', 'snow', 'farm', 'frost', 'gray', 'green', 'desert', 'red', 'lava', 'dungeon', 'molten',
            'black', 'water', 'forest', 'sea', 'slime', 'yellow', 'jungle', 'rock', 'cave', 'dark',
            'death', 'island', 'blue', 'marble', 'purple', 'shadow', 'thunder', 'hell', 'scrub', 'swamp',
            'bronze', 'grave', 'mountain', 'clockwork', 'air', 'earth', 'fire'
        ],
        [  # sub-types
            'grouse', 'apprentice', 'piercer', 'scavenger', 'scout', 'dog', 'ranged', 'fly', 'shaman', 'guard',
            'grunt', 'mage', 'archer', 'ripper', 'basher', 'elite', 'high', 'magic', 'melee', 'terror',
            'predator', 'raider', 'lesser', 'mercenary', 'throw', 'killer', 'grenade', 'minigun',
            'flamethrower', 'range', 'stalagnid', 'emerald', 'vile', 'twisted', 'adolescent', 'tortured',
            'walking', 'spitter', 'claw', 'commander', 'bowman', 'panther', 'rusted', 'weathered', 'slasher',
            'frostnid', 'headless', 'demonic', 'rotting', 'pudgy', 'warrior', 'teal', 'spine', 'baby', 'fang',
            'adept', 'knight', 'caster', 'dweller', 'maw', 'master', 'guardian', 'ranger', 'fighter', 'whacker',
            'chieftain', 'blackguard', 'mutant', 'hurler', 'masher', 'lightning', 'general'
        ],
        ['boss', 'monstrous'],  # bosses
        ['giant', 'super', 'large', 'small', 'med', 'sm', 'lg', 'greater'],  # size
        ['tail'],  # lost queen
        ['possessed']  # misc
    ]
    for ns in nonsense:
        for n in ns:
            if n in enemy_parts and len(enemy_parts) > 1:
                enemy_parts.remove(n)
    enemy_type = ' '.join(enemy_parts)
    synonyms = {
        'skeletal': 'skeleton',
        'krug skeleton': 'skeleton',  # krug dog skeleton
        'rector': 'skull',
        'corpse': 'zombie',
        'chomper': 'onetooth',
        'mhulliq': 'boar',
        'snapper': 'mangler',
        'angler': 'mangler',
        'slinger': 'lunger',
        'bubber': 'lizard',
        'lostqueen': 'mucosa',
        'lord hovart': 'skeleton',
        'beast': 'stone beast',
        'quadscale': 'picker',
        'deathknight': 'skeleton',  # cicatrix
        'acolyte': 'wraith',
        'hunter': 'robot',
        'goo walker': 'zombie',
        'scorpiot': 'robot',
        'copter': 'robot',
        'caster': 'lunger',
        'creature': 'swamp creature',
        'crawler': 'zombie',
        'swarmling': 'phrak',
        'golem cobbleman': 'stone beast',
        'proxo': 'robot',
        'stinger': 'phrak',  # swamp stinger
        'flying gritch': 'soul stinger',
        'slithermage': 'kell',
        'noctiss': 'ghost',
        'impaler': 'scorpion',
        'ztrool': 'onetooth',
        'skatwyrm': 'picker',
        'blaster': 'robot',
        'automaton flying': 'robot',
        'colonel norick': 'chicken',
        'bookas': 'pygmy',
        'octodrak': 'unguis',
        'automaton': 'robot',
        'bog beast': 'swamp creature',
        'cicatrix minion': 'skeleton',
        'elemental minion': 'elemental',
        'googore grub': 'grub',
        'heater': 'robot',
        'imp': 'lava imp',
        'jumper minion': 'shadowjumper minion',
        'kill bot': 'robot',
        'knight': 'skeleton',
        'leetch': 'slarg',
        'mummy': 'zombie',
        'nosirrom': 'zaurask',
        'perforator': 'robot',
        'punisher': 'skull',
        'sandskreech': 'picker',
        'spirit': 'lava spirit',
        'syrrus': 'hydrack',
        'undead body': 'zombie',
        'warlock': 'wraith'
    }
    if enemy_type in synonyms:
        return synonyms[enemy_type]
    return enemy_type


enemy_types = [
    # main enemies
    'bandit', 'braak', 'droc', 'droog', 'goblin', 'hassat', 'ice', 'krug', 'maljin', 'seck', 'trog', 'troll', 'zaurask',
    # undead
    'ghost', 'skeleton', 'skull', 'ursae', 'wraith', 'zombie',
    # robots
    'gobbot', 'robot',
    # further enemies
    'armor deadly', 'cyclops', 'darkling', 'doppelganger', 'elemental', 'giant', 'golem', 'horrid', 'howler', 'kell',
    'lava imp', 'lunger', 'mucosa', 'necron ghastly', 'pygmy', 'rune', 'sand', 'shadowjumper minion', 'toreck', 'witch',
    # animals?
    'barkrunner', 'eyes whelnar', 'fleshrender', 'furok', 'gargoyle', 'larch', 'lava spirit', 'shard', 'stone beast',
    'swamp creature', 'zepheryl',
    # animals
    'bear', 'boar', 'chitterskrag', 'drake', 'fury', 'googore', 'gorack', 'gremal', 'grub', 'hydrack', 'kikclaw',
    'klaw', 'krakbone', 'lectar', 'lizard', 'mangler', 'mantrap', 'midge swirling', 'mine worm', 'moth', 'onetooth',
    'phrak', 'picker', 'rat', 'scorpion', 'shrack', 'skick', 'skrubb', 'slarg', 'soul stinger', 'spider', 'spiked',
    'synged', 'tretch', 'unguis', 'vines', 'wasped', 'wolf',
    # misc
    'chicken', 'coil gob', 'mad jailer',
]


def check_cells(columns, row_values, yes='x', no=''):
    return [yes if col in row_values else no for col in columns]


# For each level: regions and enemy categories
def write_level_enemies_csv(bits: Bits):
    maps = ['map_world', 'multiplayer_world', 'map_expansion']
    maps = {n: bits.maps[n] for n in maps}
    enemies = load_enemies(bits)
    enemy_regions = {e.template_name: list() for e in enemies}
    all_region_xp = []
    for map_name, m in maps.items():
        print('Map ' + map_name)
        region_xp = load_regions_xp(m)
        all_region_xp.extend(region_xp)
        for rxp in region_xp:
            region = rxp.region
            region_enemies = region.get_enemy_actors()
            region_enemy_template_names = {e.template_name for e in region_enemies}
            for retn in region_enemy_template_names:
                enemy_regions[retn].append(rxp)
    level_xp = load_level_xp()
    all_enemy_types = set()
    data = [['Level', 'XP', 'Regions', ' '] + enemy_types]
    for level in range(150):
        level_regions = [rxp for rxp in all_region_xp if rxp.pre_level <= level <= rxp.post_level]
        if len(level_regions) == 0:
            break
        level_enemies = set()
        for rxp in level_regions:
            for enemy in rxp.region.get_enemy_actors():
                level_enemies.add(enemy.template_name)
        level_enemy_types = set()
        for level_enemy in level_enemies:
            if '_nis_' in level_enemy:
                continue
            level_enemy_types.add(categorize_enemy(level_enemy))
        enemy_row = check_cells(enemy_types, level_enemy_types)
        regions_str = ' '.join([r.name for r in level_regions])
        data.append([level, level_xp[level], regions_str, ' '] + enemy_row)
        all_enemy_types.update(level_enemy_types)
        enemies_str = ', '.join(level_enemy_types)
        print(str(level) + ': ' + str(level_xp[level]) + ' - enemies: ' + enemies_str)
    # print(sorted(all_enemy_types))
    write_csv('Enemies Level Chart', data)


class Shrine:
    def __init__(self, scid: str, region_name: str, data: dict):
        self.scid = scid
        self.region_name = region_name
        self.data = data


def print_world_level_shrines(_map: Map):
    shrines: dict[str, Shrine] = {}
    for region in _map.get_regions().values():
        objs_dir = region.gas_dir.get_subdir('objects')
        for wl in ['regular', 'veteran', 'elite']:
            wl_dir = objs_dir.get_subdir(wl)
            gas_file = wl_dir.get_gas_file('special')
            for go in gas_file.get_gas().get_sections():
                t, n = go.get_t_n_header()
                if t != 'life_shrine':  # life_shrine / mana_shrine
                    continue
                if n not in shrines:
                    shrines[n] = Shrine(n, region.get_name(), {'regular': None, 'veteran': None, 'elite': None})
                f = go.get_section('fountain')
                shrines[n].data[wl] = {'heal_amount': f.get_attr_value('heal_amount'), 'health_left': f.get_attr_value('health_left'), 'health_regen': f.get_attr_value('health_regen')}
    shrines_list: list[Shrine] = sorted(shrines.values(), key=lambda x: x.data['regular']['heal_amount'])
    csv = [
        [
            'SCID',
            'Region',
            'heal_amount regular',
            'heal_amount veteran',
            'heal_amount elite',
            'health_left regular',
            'health_left veteran',
            'health_left elite',
            'health_regen regular',
            'health_regen veteran',
            'health_regen elite'
        ]
    ]
    for shrine in shrines_list:
        r, v, e = shrine.data['regular'], shrine.data['veteran'], shrine.data['elite']
        ar, lr, rr = r['heal_amount'], r['health_left'], r['health_regen']
        av, lv, rv = v['heal_amount'], v['health_left'], v['health_regen']
        ae, le, re = e['heal_amount'], e['health_left'], e['health_regen']
        print(f'{shrine.scid}: heal_amount {ar}/{av}/{ae}, health_left {lr}/{lv}/{le}, health_regen {rr}/{rv}/{re}  ({shrine.region_name})')
        csv.append([shrine.scid, shrine.region_name, ar, av, ae, lr, lv, le, rr, rv, re])
    write_csv('World-Level Shrines', csv)


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
    assert False, f'Missing pcontent categorization for {pcontent_type}'


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
    parser = argparse.ArgumentParser(description='GasPy statistics')
    parser.add_argument('which', choices=['level-enemies', 'enemy-occurrence', 'enemies', 'map-levels', 'world-level-shrines', 'world-level-stats', 'world-level-gold', 'world-level-pcontent', 'xp-gradient'])
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
