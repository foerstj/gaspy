# For each level: regions and enemy categories
from bits.bits import Bits
from bits.maps.region import Region
from printouts.common import load_enemies, load_regions_xp, load_level_xp
from printouts.csv import write_csv

enemy_type_groups = [
    # main enemies
    ['bandit', 'braak', 'droc', 'droog', 'goblin', 'hassat', 'ice', 'krug', 'maljin', 'seck', 'trog', 'troll', 'zaurask'],
    # undead
    ['ghost', 'skeleton', 'skull', 'ursae', 'wraith', 'zombie'],
    # robots
    ['gobbot', 'robot'],
    # further enemies
    ['armor deadly', 'cyclops', 'darkling', 'doppelganger', 'elemental', 'giant', 'golem', 'horrid', 'howler', 'kell',
     'lava imp', 'lunger', 'mucosa', 'necron ghastly', 'pygmy', 'rune', 'sand', 'shadowjumper minion', 'toreck', 'witch',
     'werewolf'],
    # animals?
    ['barkrunner', 'eyes whelnar', 'fleshrender', 'furok', 'gargoyle', 'larch', 'lava spirit', 'shard', 'stone beast',
     'swamp creature', 'zepheryl'],
    # animals
    ['bear', 'boar', 'chitterskrag', 'drake', 'fury', 'googore', 'gorack', 'gremal', 'grub', 'hydrack', 'kikclaw',
     'klaw', 'krakbone', 'lectar', 'lizard', 'mangler', 'mantrap', 'midge swirling', 'mine worm', 'moth', 'onetooth',
     'phrak', 'picker', 'rat', 'scorpion', 'shrack', 'skick', 'skrubb', 'slarg', 'soul stinger', 'spider', 'spiked',
     'synged', 'tretch', 'unguis', 'vines', 'wasped', 'wolf'],
    # misc
    ['chicken', 'coil gob', 'misc boss'],
]


def categorize_enemy(enemy_template_name: str):
    enemy_template_name = (enemy_template_name
                           .replace('shadow_jumper', 'shadowjumper')
                           .replace('shadow_bigboss', 'shadowjumper')
                           .replace('queen_snow', 'snow queen')
                           .replace('king_lich', 'lich king')
                           .replace('king_fire', 'fire king'))
    enemy_parts: list = enemy_template_name.split('_')
    nonsense = [
        ['01', '02', '03', '04', '05', 'one', 'two', 'three', 'four', 'five', '2'],  # numbering
        ['gpg', 'dsx', 'xp'],  # yesterhaven, loa, r2a
        ['reveal', 'act', 'temp', 'poking', 'eating', 'r', 'q', 'summon', 'mp', 'lhaoc', 'ar'],  # reveal effect
        [  # theming
            'white', 'snow', 'farm', 'frost', 'gray', 'green', 'desert', 'red', 'lava', 'dungeon', 'molten',
            'black', 'water', 'forest', 'sea', 'slime', 'yellow', 'jungle', 'rock', 'cave', 'dark',
            'death', 'island', 'blue', 'marble', 'purple', 'shadow', 'thunder', 'hell', 'scrub', 'swamp',
            'bronze', 'grave', 'mountain', 'clockwork', 'air', 'earth', 'fire', 'grey'
        ],
        [  # sub-types
            'grouse', 'apprentice', 'piercer', 'scavenger', 'scout', 'dog', 'ranged', 'fly', 'shaman', 'guard',
            'grunt', 'mage', 'archer', 'ripper', 'basher', 'elite', 'high', 'magic', 'melee', 'terror',
            'predator', 'raider', 'lesser', 'mercenary', 'throw', 'killer', 'grenade', 'minigun',
            'flamethrower', 'range', 'stalagnid', 'emerald', 'vile', 'twisted', 'adolescent', 'tortured',
            'walking', 'spitter', 'claw', 'commander', 'bowman', 'panther', 'rusted', 'weathered', 'slasher',
            'frostnid', 'headless', 'demonic', 'rotting', 'pudgy', 'warrior', 'teal', 'spine', 'baby', 'fang',
            'adept', 'knight', 'caster', 'dweller', 'maw', 'master', 'guardian', 'ranger', 'fighter', 'whacker',
            'chieftain', 'blackguard', 'mutant', 'hurler', 'masher', 'lightning', 'general', 'sword', 'karate',
            'punk-ass'
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
        'warlock': 'wraith',
        'mad jailer': 'misc boss',
        'snow queen': 'misc boss',
        'lich king': 'misc boss',
        'fire king': 'misc boss',
        'salamander': 'zaurask',
        'raks': 'misc boss',
    }
    if enemy_type in synonyms:
        return synonyms[enemy_type]
    return enemy_type


def check_cells(columns, row_values, yes='x', no=''):
    for row_value in row_values:
        if row_value not in columns:
            print(f'Note: no column for row value {row_value}')
    return [yes if col in row_values else no for col in columns]


def get_region_enemy_template_names(region: Region) -> set[str]:
    region_enemies = region.get_enemy_actors()
    template_names = {e.template_name for e in region_enemies}
    gen_enemies = region.get_generated_enemies()
    template_names.update(gen_enemies.keys())
    return {t for t in template_names if '_nis_' not in t}


def write_level_enemies_csv(bits: Bits):
    maps = ['map_world', 'multiplayer_world', 'yesterhaven', 'map_expansion', 'dsx_xp']
    maps = {n: bits.maps[n] for n in maps}
    enemies = load_enemies(bits)
    enemy_regions = {e.template_name: list() for e in enemies}
    all_region_xp = []
    for map_name, m in maps.items():
        print('Map ' + map_name)
        region_xp = load_regions_xp(m, None, 0 if map_name != 'dsx_xp' else 10)
        all_region_xp.extend(region_xp)
        for rxp in region_xp:
            region_enemy_template_names = get_region_enemy_template_names(rxp.region)
            for retn in region_enemy_template_names:
                enemy_regions[retn].append(rxp)
    level_xp = load_level_xp()
    all_enemy_types = set()
    enemy_type_cols = []
    for enemy_type_group in enemy_type_groups:
        enemy_type_cols += [' '] + enemy_type_group
    enemy_type_cols = enemy_type_cols[1:]
    data = [['Level', 'XP', 'Regions', ' '] + enemy_type_cols]
    for level in range(150):
        level_regions = [rxp for rxp in all_region_xp if rxp.pre_level <= level <= rxp.post_level]
        level_enemies = set()
        for rxp in level_regions:
            level_enemies.update(get_region_enemy_template_names(rxp.region))
        level_enemy_types = set()
        for level_enemy in level_enemies:
            level_enemy_types.add(categorize_enemy(level_enemy))
        enemy_row = check_cells(enemy_type_cols, level_enemy_types)
        regions_str = ' '.join([r.name for r in level_regions])
        data.append([level, level_xp[level], regions_str, ' '] + enemy_row)
        all_enemy_types.update(level_enemy_types)
        enemies_str = ', '.join(sorted(level_enemy_types))
        print(str(level) + ': ' + str(level_xp[level]) + ' - enemies: ' + enemies_str)
    # print(sorted(all_enemy_types))
    write_csv('Enemies Level Chart', data)
