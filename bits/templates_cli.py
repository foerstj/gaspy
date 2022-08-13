import sys

from bits.bits import Bits


def print_core_templates(bits: Bits):
    core_template_names = bits.templates.get_core_template_names()
    print(f'{len(core_template_names)} core templates:')
    for name in core_template_names:
        print(name)


def print_enemies(bits: Bits):
    enemies_dict = bits.templates.get_enemy_templates()
    enemies = [e for n, e in enemies_dict.items() if 'base' not in n and 'summon' not in n]
    enemy_names = list({e.compute_value('common', 'screen_name') for e in enemies})
    enemy_names = [e.strip('"') for e in enemy_names if e is not None]
    enemy_names.sort()
    print(f'{len(enemy_names)} enemies:')
    for name in enemy_names:
        print(name)


def main(argv):
    bits_arg = argv[0] if len(argv) > 0 else None
    bits = Bits(bits_arg)
    # print_enemies(bits)
    print_core_templates(bits)


if __name__ == '__main__':
    main(sys.argv[1:])
