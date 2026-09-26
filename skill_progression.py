import argparse
import sys


DIST = {
    'm': {'s': 0.64, 'd': 0.27, 'i': 0.09},
    'r': {'s': 0.25, 'd': 0.62, 'i': 0.13},
    'n': {'s': 0.09, 'd': 0.18, 'i': 0.73},
    'c': {'s': 0.13, 'd': 0.17, 'i': 0.70},
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
        return f'u{self.uber} [m{self.melee} r{self.ranged} n{self.nmagic} c{self.cmagic}] [s{self.strength}+10 d{self.dexterity}+10 i{self.intelligence}+10]'


def char_at(skill: str, level: int) -> Char:
    char = Char()
    char.uber = level
    char.melee = level if skill == 'melee' else 0
    char.ranged = level if skill == 'ranged' else 0
    char.nmagic = level if skill == 'nmagic' else 0
    char.cmagic = level if skill == 'cmagic' else 0
    char.strength = round(level * DIST[skill[0]]['s'], 2)
    char.dexterity = round(level * DIST[skill[0]]['d'], 2)
    char.intelligence = round(level * DIST[skill[0]]['i'], 2)
    return char


def skill_progression(_):
    for skill in ['melee', 'ranged', 'nmagic', 'cmagic']:
        for level in range(0, 151, 10):
            char = char_at(skill, level)
            print(f'{skill} level {level}: {char}')


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy skill_progression')
    parser.add_argument('--csv-out', default=None)
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    skill_progression(args.csv_out)


if __name__ == '__main__':
    main(sys.argv[1:])
