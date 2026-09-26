import argparse
import sys


DIST = {
    'm': {'s': 0.64, 'd': 0.27, 'i': 0.09},
    'r': {'s': 0.25, 'd': 0.62, 'i': 0.13},
    'n': {'s': 0.09, 'd': 0.18, 'i': 0.73},
    'c': {'s': 0.13, 'd': 0.17, 'i': 0.70},
}


WL_EQUIVS = {
    'regular': (1, 0),
    'veteran': ((150-54)/150, 54),
    'elite': ((150-83)/150, 83),
}


class Char:
    def __init__(self):
        self.uber = 0
        self.melee = 0
        self.ranged = 0
        self.nmagic = 0
        self.cmagic = 0
        self.strength = 0
        self.dexterity = 0
        self.intelligence = 0

    def __str__(self):
        skills_str = f'm{round(self.melee, 2)} r{round(self.ranged, 2)} n{round(self.nmagic, 2)} c{round(self.cmagic, 2)}'
        stats_str = f's{round(self.strength, 2)}+10 d{round(self.dexterity, 2)}+10 i{round(self.intelligence, 2)}+10'
        return f'u{round(self.uber, 2)} [{skills_str}] [{stats_str}]'


def char_at(skill: str, level: float) -> Char:
    char = Char()
    char.uber = level
    char.melee = level if skill == 'melee' else 0
    char.ranged = level if skill == 'ranged' else 0
    char.nmagic = level if skill == 'nmagic' else 0
    char.cmagic = level if skill == 'cmagic' else 0
    char.strength = level * DIST[skill[0]]['s']
    char.dexterity = level * DIST[skill[0]]['d']
    char.intelligence = level * DIST[skill[0]]['i']
    return char


def skill_progression_wl_equiv(levels: list[list[int]], wl='regular'):
    m, c = WL_EQUIVS[wl]
    for skill in ['melee', 'ranged', 'nmagic', 'cmagic']:
        for levels_def in levels:
            for regular_level in range(levels_def[0], levels_def[1]+1, levels_def[2] if len(levels_def) > 2 else 1):
                equiv_level = m * regular_level + c
                char = char_at(skill, equiv_level)
                level_str = f'{equiv_level}' if wl == 'regular' else f'{wl} {round(equiv_level, 2)} (eq. regular {regular_level})'
                print(f'{skill} level {level_str}: {char}')


def parse_levels_str(levels_str: str):
    level_parts = [int(s) for s in levels_str.split(':')]
    assert 2 <= len(level_parts) <= 3
    return level_parts


def skill_progression(levels_strs: list[str], wl_equivs=False):
    levels = [parse_levels_str(s) for s in levels_strs] if levels_strs else [[0, 150, 10]]
    if wl_equivs:
        for wl in ['regular', 'veteran', 'elite']:
            skill_progression_wl_equiv(levels, wl)
    else:
        skill_progression_wl_equiv(levels, 'regular')


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy skill_progression')
    parser.add_argument('--wl-equivs', action='store_true')
    parser.add_argument('--levels', nargs='+', default=None)
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    skill_progression(args.levels, args.wl_equivs)


if __name__ == '__main__':
    main(sys.argv[1:])
