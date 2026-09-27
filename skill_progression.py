import argparse
import sys

from bits.bits import Bits
from gas.gas import Section
from printouts.common import parse_bool_value, parse_int_value
from printouts.csv import write_csv_dict
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


class LookupSkillRange:
    def __init__(self, name: str, min_range: int, max_range: int):
        self.name = name
        self.min_range = min_range
        self.max_range = max_range

    def __str__(self):
        return f'{self.name} {self.min_range}-{self.max_range}'

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'skill*'
        name = section.get_attr_value('name').strip('"')
        min_range = parse_int_value(section.get_attr_value('min_range'))
        max_range = parse_int_value(section.get_attr_value('max_range'))
        return LookupSkillRange(name, min_range, max_range)

    def matches(self, level: float) -> bool:
        return self.min_range <= int(level) <= self.max_range


class ClassDesignation:
    def __init__(self, screen_name: str, is_female: bool, is_male: bool, skills: list[LookupSkillRange]):
        self.screen_name = screen_name
        self.is_female = is_female
        self.is_male = is_male
        self.skills = skills

    def __str__(self):
        fm = ''.join(['f' if self.is_female else '', 'm' if self.is_male else ''])
        skills = ', '.join([f'{s}' for s in self.skills])
        return f'"{self.screen_name}" ({fm}): {skills}'

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'class_designation*'
        screen_name = section.get_attr_value('screen_name').strip('"')
        is_female = parse_bool_value(section.get_attr_value('is_female'))
        is_male = parse_bool_value(section.get_attr_value('is_male'))
        skills = [LookupSkillRange.from_gas(s) for s in section.get_sections('skill*')]
        return ClassDesignation(screen_name, is_female, is_male, skills)

    def matches(self, skill_levels: dict[str, float], female: bool) -> bool:
        if female and not self.is_female:
            return False
        if not female and not self.is_male:
            return False
        for skill in self.skills:
            level = skill_levels.get(skill.name, 0)
            if not skill.matches(level):
                return False
        return True


class ClassLookup:
    def __init__(self, designations: list[ClassDesignation]):
        self.designations = designations

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'class_lookup'
        designations = [ClassDesignation.from_gas(s) for s in section.get_sections('class_designation*')]
        return ClassLookup(designations)

    def look_up(self, skill_levels: dict[str, float]) -> str:
        designation = None
        for d in self.designations:
            if d.matches(skill_levels, False):
                designation = d
        return designation.screen_name if designation is not None else None


class Stat:
    def __init__(self, level: float = 0, xp: float = 0):
        self.level = level
        self.xp = xp


class Char:
    def __init__(self, class_lookup: ClassLookup = None):
        self.class_lookup = class_lookup
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
        title = self.lookup_class() if self.class_lookup is not None else None
        if title:
            skills_str += f' "{title}"'
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

    def _apply_new_uber(self, new_uber: Stat, skills_dist: dict[str, float]):
        old_uber = self.uber
        self.uber = new_uber
        added_uber_levels = new_uber.level - old_uber.level
        added_xp = new_uber.xp - old_uber.xp

        assert_nearly_equal(sum(skills_dist.values()), 1)
        for skill_name, skill_part in skills_dist.items():
            skill_stat = self.stat(skill_name)
            skill_stat.xp += added_xp * skill_part
            skill_stat.level = get_level_float(skill_stat.xp, LEVEL_XP)

            for sdi in ['strength', 'dexterity', 'intelligence']:
                sdi_stat = self.stat(sdi)
                sdi_skill_part = DIST[skill_name[0]][sdi[0]]
                sdi_stat.level += added_uber_levels * skill_part * sdi_skill_part
                sdi_stat.xp += added_xp * skill_part * sdi_skill_part

        self.check_stats()

    def add_uber_levels(self, skills_dist: dict[str, float], uber_levels: float):
        new_uber_level = self.uber.level + uber_levels
        new_uber_xp = get_xp_float(new_uber_level, LEVEL_XP)
        new_uber = Stat(new_uber_level, new_uber_xp)
        self._apply_new_uber(new_uber, skills_dist)

    def add_xp(self, skills_dist: dict[str, float], xp: float):
        new_uber_xp = self.uber.xp + xp
        new_uber_level = get_level_float(new_uber_xp, LEVEL_XP)
        new_uber = Stat(new_uber_level, new_uber_xp)
        self._apply_new_uber(new_uber, skills_dist)

    def check_stats(self):
        assert_nearly_equal(self.melee.xp + self.ranged.xp + self.nmagic.xp + self.cmagic.xp, self.uber.xp)
        assert_nearly_equal(self.strength.xp + self.dexterity.xp + self.intelligence.xp, self.uber.xp)
        assert_nearly_equal(self.strength.level + self.dexterity.level + self.intelligence.level, self.uber.level)

    def lookup_class(self) -> str:
        return self.class_lookup.look_up({'melee': self.melee.level, 'ranged': self.ranged.level, 'nature magic': self.nmagic.level, 'combat magic': self.cmagic.level})


class CharQuery:
    def __init__(self, level, skills, wl_eq):
        self.level = level
        self.skills = skills
        self.wl_eq = wl_eq


class CharCalc:
    def __init__(self, query: CharQuery, char: Char):
        self.query = query
        self.char = char


def assert_nearly_equal(a: float, b: float):
    if a == b:
        return
    assert abs(a - b) / ((abs(a) + abs(b)) / 2) < 0.000001, f'{round(a, 6)} == {round(b, 6)}'


def char_at_uber_level(skills_dist: dict[str, float], uber_level: float, class_lookup: ClassLookup = None) -> Char:
    char = Char(class_lookup)
    char.add_uber_levels(skills_dist, uber_level)
    return char


def get_wl_eq_level(regular_level, wl_eq='regular'):
    m, c = WL_EQUIVS[wl_eq]
    return m * regular_level + c


def skill_progression_wl_equiv(levels: list[list[int]], skill_sets: list[set[str]], wl='regular', class_lookup: ClassLookup = None) -> list[CharCalc]:
    char_calcs = list()
    for skills in skill_sets:
        for levels_def in levels:
            for regular_level in range(levels_def[0], levels_def[1]+1, levels_def[2] if len(levels_def) > 2 else 1):
                equiv_level = get_wl_eq_level(regular_level, wl)
                query = CharQuery(regular_level, skills, wl)
                skills_dist = {s: 1/len(skills) for s in skills}
                char = char_at_uber_level(skills_dist, equiv_level, class_lookup)
                char_calcs.append(CharCalc(query, char))
    return char_calcs


def parse_levels_str(levels_str: str):
    level_parts = [int(s) for s in levels_str.split(':')]
    assert 2 <= len(level_parts) <= 3
    return level_parts


def parse_skills_str(skills_str: str):
    skills = skills_str.split('+')
    assert 1 <= len(skills) <= 4
    return set(skills)


def print_csv(char_calcs: list[CharCalc], output_dir: str = None):
    keys = ['wl_eq', 'level', 'skills', 'xp', 'uber', 'm', 'r', 'n', 'c', 'str', 'dex', 'int', 'title']
    header_dict = {
        'wl_eq': 'wl', 'level': 'level', 'skills': 'skills', 'xp': 'xp', 'uber': 'uber', 'title': 'title',
        'm': 'melee', 'r': 'ranged', 'n': 'nmagic', 'c': 'cmagic', 'str': 'strength', 'dex': 'dexterity', 'int': 'intelligence'
    }
    data_dicts = [
        {
            'wl_eq': c.query.wl_eq if c.query.wl_eq != 'regular' else None, 'level': c.query.level, 'skills': '+'.join(c.query.skills),
            'xp': int(c.char.uber.xp), 'uber': round(c.char.uber.level, 2),
            'm': round(c.char.melee.level, 2), 'r': round(c.char.ranged.level, 2), 'n': round(c.char.nmagic.level, 2), 'c': round(c.char.cmagic.level, 2),
            'str': round(c.char.strength.level, 2), 'dex': round(c.char.dexterity.level, 2), 'int': round(c.char.intelligence.level, 2),
            'title': c.char.lookup_class(),
        }
        for c in char_calcs
    ]
    write_csv_dict('skill-progression', keys, header_dict, data_dicts, output_dir=output_dir, sep=';')


def print_console(char_calcs: list[CharCalc]):
    for char_calc in char_calcs:
        wl_eq = char_calc.query.wl_eq
        if wl_eq is not None:
            equiv_level = get_wl_eq_level(char_calc.query.level, wl_eq)
            level_str = f'{equiv_level:>3}' if wl_eq == 'regular' else f'{wl_eq:<7} {round(equiv_level, 2)} (eq. regular {char_calc.query.level:>3})'
        else:
            level_str = f'{char_calc.query.level:>3}'
        skills_str = '+'.join([f'{s:<6}' for s in char_calc.query.skills])
        print(f'{skills_str:<6} level {level_str}: {char_calc.char}')


def skill_progression(levels_strs: list[str], wl_equivs=False, eq_levels_strs: list[str] = None, skills_strs: list[str] = None, output_csv: str = None, class_lookup_bits_path: str = None):
    levels = [parse_levels_str(s) for s in levels_strs] if levels_strs else [[0, 150, 10]]
    skill_sets = [parse_skills_str(s) for s in skills_strs] if skills_strs else [{'melee'}, {'ranged'}, {'nmagic'}, {'cmagic'}, {'melee', 'ranged', 'nmagic', 'cmagic'}]
    class_lookup_bits = None if class_lookup_bits_path == '' else Bits(class_lookup_bits_path)
    class_lookup = None if class_lookup_bits is None else ClassLookup.from_gas(
        class_lookup_bits.gas_dir.get_subdir(['world', 'global']).get_gas_file('class_lookup').get_gas().get_section('class_lookup')
    )

    char_calcs: list[CharCalc] = list()
    if wl_equivs:
        eq_levels = [parse_levels_str(s) for s in eq_levels_strs] if eq_levels_strs else levels
        char_calcs.extend(skill_progression_wl_equiv(levels, skill_sets, class_lookup=class_lookup, wl='regular'))
        for wl in ['veteran', 'elite']:
            char_calcs.extend(skill_progression_wl_equiv(eq_levels, skill_sets, class_lookup=class_lookup, wl=wl))
    else:
        char_calcs.extend(skill_progression_wl_equiv(levels, skill_sets, class_lookup=class_lookup))

    print_console(char_calcs)
    if output_csv != '':
        print_csv(char_calcs, output_csv)

    # do_examples(class_lookup)


def do_examples(class_lookup: ClassLookup = None):
    # Example taken from https://dungeonsiege.fandom.com/wiki/Character_Leveling_and_Spell_Guide#Example_Demonstrating_How_Attribute_Scores_Increase
    # "Consider the following example. A Nature mage has trained to Level 50. He suddenly has a mid-life crisis. His Strength is only 14. What is he doing to himself? He wants more Strength."
    char = Char(class_lookup)
    char.add_uber_levels({'nmagic': 1}, 50)
    print(f'\nLevel 50 NMagic: {char}')
    char.add_uber_levels({'melee': 1}, 1)
    print(f'+1 Uber Level Melee: {char}')
    # Another example with weighted skills:
    char2 = Char(class_lookup)
    char2.add_uber_levels({'melee': 0.75, 'nmagic': 0.25}, 20)
    print(f'\nChar with wonky multi-classing m/n 3:1: {char2}')
    char2.add_uber_levels({'melee': 0.25, 'nmagic': 0.75}, 20)
    print(f'Tried to fix wonky char with m/n 1:3: {char2}')
    char2.add_xp({'melee': 0.5, 'nmagic': 0.5}, char2.uber.xp)
    print(f'Then doubled xp m/n 1:1: {char2}')


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy skill_progression')
    parser.add_argument('--wl-equivs', action='store_true')
    parser.add_argument('--levels', nargs='+', default=None)
    parser.add_argument('--eq-levels', nargs='+', default=None)
    parser.add_argument('--skills', nargs='+', default=None)
    parser.add_argument('--output-csv', nargs='?', default='')
    parser.add_argument('--class-lookup', nargs='?', default='')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    skill_progression(args.levels, args.wl_equivs, args.eq_levels, args.skills, args.output_csv, args.class_lookup)


if __name__ == '__main__':
    main(sys.argv[1:])
