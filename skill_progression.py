import argparse
import sys

from printouts.level_xp import load_level_xp, get_xp_float

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


LEVEL_XP = load_level_xp()


class Stat:
    def __init__(self, level: float = 0, xp: float = 0):
        self.level = level
        self.xp = xp


class Char:
    def __init__(self):
        self.uber = Stat()
        self.melee = Stat()
        self.ranged = Stat()
        self.nmagic = Stat()
        self.cmagic = Stat()
        self.strength = Stat()
        self.dexterity = Stat()
        self.intelligence = Stat()

    def __str__(self):
        skills_dict = {'m': self.melee, 'r': self.ranged, 'n': self.nmagic, 'c': self.cmagic}
        skills_str = ' '.join([f'{x}{round(s.level, 2)}' for x, s in skills_dict.items()])
        stats_dict = {'s': self.strength, 'd': self.dexterity, 'i': self.intelligence}
        stats_str = ' '.join([f'{x}{round(s.level, 2)}+10' for x, s in stats_dict.items()])
        return f'u{round(self.uber.level, 2)} [{skills_str}] [{stats_str}] ({int(self.uber.xp)}xp)'


def char_at_uber_level(skill: str, uber_level: float) -> Char:
    xp = get_xp_float(uber_level, LEVEL_XP)
    char = Char()
    char.uber = Stat(uber_level, xp)
    char.melee = Stat(uber_level, xp) if skill == 'melee' else Stat()
    char.ranged = Stat(uber_level, xp) if skill == 'ranged' else Stat()
    char.nmagic = Stat(uber_level, xp) if skill == 'nmagic' else Stat()
    char.cmagic = Stat(uber_level, xp) if skill == 'cmagic' else Stat()
    strength = DIST[skill[0]]['s']
    char.strength = Stat(uber_level * strength, xp * strength)
    dexterity = DIST[skill[0]]['d']
    char.dexterity = Stat(uber_level * dexterity, xp * dexterity)
    intelligence = DIST[skill[0]]['i']
    char.intelligence = Stat(uber_level * intelligence, xp * intelligence)
    return char


def skill_progression_wl_equiv(levels: list[list[int]], wl='regular'):
    m, c = WL_EQUIVS[wl]
    for skill in ['melee', 'ranged', 'nmagic', 'cmagic']:
        for levels_def in levels:
            for regular_level in range(levels_def[0], levels_def[1]+1, levels_def[2] if len(levels_def) > 2 else 1):
                equiv_level = m * regular_level + c
                char = char_at_uber_level(skill, equiv_level)
                level_str = f'{equiv_level}' if wl == 'regular' else f'{wl:<7} {round(equiv_level, 2)} (eq. regular {regular_level})'
                print(f'{skill:<6} level {level_str}: {char}')


def parse_levels_str(levels_str: str):
    level_parts = [int(s) for s in levels_str.split(':')]
    assert 2 <= len(level_parts) <= 3
    return level_parts


def skill_progression(levels_strs: list[str], wl_equivs=False, eq_levels_strs: list[str] = None):
    levels = [parse_levels_str(s) for s in levels_strs] if levels_strs else [[0, 150, 10]]
    if wl_equivs:
        eq_levels = [parse_levels_str(s) for s in eq_levels_strs] if eq_levels_strs else levels
        skill_progression_wl_equiv(levels, 'regular')
        for wl in ['veteran', 'elite']:
            skill_progression_wl_equiv(eq_levels, wl)
    else:
        skill_progression_wl_equiv(levels, 'regular')


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy skill_progression')
    parser.add_argument('--wl-equivs', action='store_true')
    parser.add_argument('--levels', nargs='+', default=None)
    parser.add_argument('--eq-levels', nargs='+', default=None)
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    skill_progression(args.levels, args.wl_equivs, args.eq_levels)


if __name__ == '__main__':
    main(sys.argv[1:])
