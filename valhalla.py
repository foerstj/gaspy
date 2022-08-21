import sys

from bits.bits import Bits
from bits.templates import Template


def scale_enemy(template: Template):
    scale_base = float(template.compute_value('aspect', 'scale_base') or 1)
    veteran_factor = 2 ** (1 / 3)  # double volume
    elite_factor = 4 ** (1 / 3)  # double volume again
    if template.name.lower().startswith('2w_'):
        scale_base *= veteran_factor
    elif template.name.lower().startswith('3w_'):
        scale_base *= elite_factor
    template.section.get_or_create_section('aspect').set_attr_value('scale_base', scale_base)


def pimp_enemy(enemy: Template):
    scale_enemy(enemy)


def valhalla(bits: Bits):
    for name, template in bits.templates.get_enemy_templates().items():
        pimp_enemy(template)
    bits.templates.gas_dir.get_subdir('veteran').save()
    bits.templates.gas_dir.get_subdir('elite').save()


def main(argv):
    bits_path = argv[0] if len(argv) > 0 else None
    bits = Bits(bits_path)
    valhalla(bits)


if __name__ == '__main__':
    main(sys.argv[1:])
