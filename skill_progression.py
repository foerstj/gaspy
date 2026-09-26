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


def skill_progression(_):
    for wl in ['regular', 'veteran', 'elite']:
        m, c = WL_EQUIVS[wl]
        for skill in ['melee', 'ranged', 'nmagic', 'cmagic']:
            for regular_level in range(0, 151, 10):
                equiv_level = m * regular_level + c
                char = char_at(skill, equiv_level)
                level_str = f'{equiv_level}' if wl == 'regular' else f'{wl} {round(equiv_level, 2)} (eq. regular {regular_level})'
                print(f'{skill} level {level_str}: {char}')


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy skill_progression')
    parser.add_argument('--csv-out', default=None)
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    skill_progression(args.csv_out)


if __name__ == '__main__':
    main(sys.argv[1:])
