import argparse
import sys

from printouts.level_xp import load_level_xp, get_xp_float, get_level_float

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

    def stat(self, stat_name: str) -> Stat:
        if stat_name == 'uber':
            return self.uber
        elif stat_name == 'melee':
            return self.melee
        elif stat_name == 'ranged':
            return self.ranged
        elif stat_name == 'nmagic':
            return self.nmagic
        elif stat_name == 'cmagic':
            return self.cmagic
        elif stat_name == 'strength':
            return self.strength
        elif stat_name == 'dexterity':
            return self.dexterity
        elif stat_name == 'intelligence':
            return self.intelligence


def assert_nearly_equal(a: float, b: float):
    if a == b:
        return
    assert abs(a - b) / ((a + b) / 2) < 0.00001, f'{round(a, 6)} == {round(b, 6)}'


def char_at_uber_level(skills: set[str], uber_level: float) -> Char:
    xp = get_xp_float(uber_level, LEVEL_XP)
    char = Char()
    char.uber = Stat(uber_level, xp)

    skill_part = 1 / len(skills)
    for skill in skills:
        skill_stat = char.stat(skill)
        skill_stat.xp = xp * skill_part
        skill_stat.level = get_level_float(int(skill_stat.xp), LEVEL_XP)

        for sdi in ['strength', 'dexterity', 'intelligence']:
            sdi_stat = char.stat(sdi)
            sdi_skill_part = DIST[skill[0]][sdi[0]]
            sdi_stat.level += uber_level * skill_part * sdi_skill_part
            sdi_stat.xp += xp * skill_part * sdi_skill_part

    assert_nearly_equal(char.melee.xp + char.ranged.xp + char.nmagic.xp + char.cmagic.xp, xp)
    assert_nearly_equal(char.strength.xp + char.dexterity.xp + char.intelligence.xp, xp)
    assert_nearly_equal(char.strength.level + char.dexterity.level + char.intelligence.level, uber_level)
    return char


def skill_progression_wl_equiv(levels: list[list[int]], wl='regular'):
    m, c = WL_EQUIVS[wl]
    for skills in [{'melee'}, {'ranged'}, {'nmagic'}, {'cmagic'}, {'melee', 'nmagic'}]:
        for levels_def in levels:
            for regular_level in range(levels_def[0], levels_def[1]+1, levels_def[2] if len(levels_def) > 2 else 1):
                equiv_level = m * regular_level + c
                char = char_at_uber_level(skills, equiv_level)
                level_str = f'{equiv_level:>3}' if wl == 'regular' else f'{wl:<7} {round(equiv_level, 2)} (eq. regular {regular_level:>3})'
                skills_str = '+'.join([f'{s:<6}' for s in skills])
                print(f'{skills_str:<6} level {level_str}: {char}')


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
