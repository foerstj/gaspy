import argparse
import os
import sys

from bits.bits import Bits
from gas.gas_parser import GasParser
from bits.templates import Template


def load_level_xp():
    level_file_path = os.path.join('input', 'XP Chart.csv')
    with open(level_file_path) as level_file:
        level_xp = [int(line.split(',')[1]) for line in level_file]
    return level_xp


def load_ordered_regions(m):
    regions = m.get_regions()
    order_file_path = os.path.join('input', m.gas_dir.dir_name + '.txt')
    if os.path.isfile(order_file_path):
        ordered_regions = []
        with open(order_file_path) as order_file:
            for line in order_file.readlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                line = line.split(',')
                region_name = line[0]
                region_weight = float(line[1]) if len(line) > 1 else 1
                ordered_regions.append((regions[region_name], region_weight))
    else:
        ordered_regions = [(r, 1) for r in regions.values()]
    return ordered_regions


def get_level(xp, level_xp):
    level = 0
    while level_xp[level + 1] <= xp:
        level += 1
    return level


class RegionXP:
    def __init__(self, region, weight=1):
        self.region = region
        self.name = region.gas_dir.dir_name
        print(self.name)
        self.xp = region.get_xp()
        self.weight = weight
        self.xp_pre = None
        self.xp_post = None
        self.pre_level = None
        self.post_level = None

    def set_pre_xp(self, pre_xp, level_xp):
        self.xp_pre = pre_xp
        self.xp_post = pre_xp + self.xp*self.weight
        self.pre_level = get_level(pre_xp, level_xp)
        self.post_level = get_level(self.xp_post, level_xp)
        return self.xp_post


def load_region_xp(m):
    ordered_regions = load_ordered_regions(m)
    level_xp = load_level_xp()
    regions_xp = [RegionXP(*r) for r in ordered_regions]
    xp = 0
    for rx in regions_xp:
        xp = rx.set_pre_xp(xp, level_xp)
    return regions_xp


def write_csv(name: str, data: list[list], sep=','):
    out_file_path = os.path.join('output', f'{name}.csv')
    with open(out_file_path, 'w') as csv_file:
        csv_file.writelines([sep.join([str(x) for x in y]) + '\n' for y in data])
    print(f'wrote {out_file_path}')


# Ordered regions -> how much XP, and what lvl the player will be at
def write_map_levels_csv(m):
    regions_xp = load_region_xp(m)
    data = [['region', 'xp', 'weight', 'xp', 'sum', 'level pre', 'level post']]
    for r in regions_xp:
        data.append([r.name, r.xp, r.weight, r.xp*r.weight, r.xp_post, r.pre_level, r.post_level])
    write_csv(m.gas_dir.dir_name, data)


class Enemy:
    def __init__(self, template):
        assert isinstance(template, Template)
        self.template = template
        self.template_name = template.name
        self.screen_name: str = template.compute_value('common', 'screen_name')
        self.xp = int(template.compute_value('aspect', 'experience_value') or '0')
        self.life = int(template.compute_value('aspect', 'max_life') or '0')
        self.defense = float(template.compute_value('defend', 'defense') or '0')


def load_enemies(bits):
    enemies = bits.templates.get_enemy_templates()
    enemies = [e for n, e in enemies.items() if not (n.startswith('2w_') or n.startswith('3w_'))]
    enemies = [e for e in enemies if 'base' not in e.name]  # unused/forgotten base templates e.g. dsx_base_goblin, dsx_elemental_fire_base
    enemies = [e for e in enemies if 'summon' not in e.name]
    enemies = [Enemy(e) for e in enemies]
    return enemies


def make_enemies_csv_line(enemy: Enemy) -> list:
    name = enemy.screen_name.strip('"')
    xp = enemy.xp
    life = enemy.life
    defense = int(enemy.defense)
    template_name = enemy.template_name
    wp_pref: str = enemy.template.compute_value('mind', 'actor_weapon_preference')
    icz_melee = enemy.template.compute_value('mind', 'on_enemy_entered_icz_switch_to_melee')
    icz_melee = {'true': True, 'false': False}[icz_melee.lower()] if icz_melee else False
    stance = wp_pref[3:].capitalize()
    if icz_melee and stance != 'Melee':
        if enemy.template.compute_value('inventory', 'selected_active_location'):
            stance = 'Combo'
    attacks = []
    if stance == 'Melee' or stance == 'Combo':
        h2h_min = enemy.template.compute_value('attack', 'damage_min') or 0
        h2h_max = enemy.template.compute_value('attack', 'damage_max') or 0
        h2h_lvl = enemy.template.compute_value('actor', 'skills', 'melee')
        if h2h_lvl is None:
            h2h_lvl = 0
        else:
            h2h_lvl = h2h_lvl.split(',')[0].strip()
        h2h = f'h2h {h2h_min}-{h2h_max} lvl {h2h_lvl}'
        attacks.append(h2h)
    attacks = '\n'.join(attacks)
    return [name, xp, life, defense, stance, attacks, template_name]


# Sth similar to the List of Enemies in the Wiki
def write_enemies_csv(bits: Bits):
    enemies = load_enemies(bits)

    enemies = [e for e in enemies if e.screen_name is not None]  # dsx_drake
    enemies = [e for e in enemies if '_reveal' not in e.template_name and '_nis_' not in e.template_name and not e.template_name.startswith('test_')]
    # enemies = [e for e in enemies if e.xp]  # enemies with 0 xp aren't included in the wiki either

    enemies.sort(key=lambda e: e.screen_name)
    enemies.sort(key=lambda e: e.xp)

    print('Enemies: ' + str(len(enemies)))
    print([e.template_name for e in enemies])
    data = [['Name', 'XP', 'Life', 'Defense', 'Stance', 'Attacks', 'Template']]
    for enemy in enemies:
        data.append(make_enemies_csv_line(enemy))
    write_csv('enemies-regular', data)


# Print out which enemies occur in which regions
def print_enemy_occurrence(bits: Bits):
    maps = ['map_world', 'multiplayer_world', 'map_expansion']
    maps = {n: bits.maps[n] for n in maps}
    enemies = load_enemies(bits)
    enemy_regions = {e.template_name: list() for e in enemies}
    enemies_by_tn = {e.template_name: e for e in enemies}
    for map_name, m in maps.items():
        print('Map ' + map_name)
        region_xp = load_region_xp(m)
        for rxp in region_xp:
            region = rxp.region
            region_enemies = region.get_enemies()
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
        region_xp = load_region_xp(m)
        all_region_xp.extend(region_xp)
        for rxp in region_xp:
            region = rxp.region
            region_enemies = region.get_enemies()
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
            for enemy in rxp.region.get_enemies():
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


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy CSV')
    parser.add_argument('which', choices=['level-enemies', 'enemy-occurrence', 'enemies', 'map-levels'])
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
    elif which == 'enemies':
        write_enemies_csv(bits)
    elif which == 'map-levels':
        map_name = args.map_name
        assert map_name
        assert map_name in bits.maps
        write_map_levels_csv(bits.maps[map_name])
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
