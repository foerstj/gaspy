import sys

from bits.bits import Bits


def main(argv):
    bits_path = argv[0] if len(argv) > 0 else None
    bits = Bits(bits_path)
    for name, template in bits.templates.get_enemy_templates().items():
        scale_base = float(template.compute_value('aspect', 'scale_base') or 1)
        # print(f'{name}: {scale_base}')
        if name.lower().startswith('2w_'):
            scale_base *= 1.2
        elif name.lower().startswith('3w_'):
            scale_base *= 1.5
        template.section.get_or_create_section('aspect').set_attr_value('scale_base', scale_base)
    bits.templates.gas_dir.get_subdir('veteran').save()
    bits.templates.gas_dir.get_subdir('elite').save()


if __name__ == '__main__':
    main(sys.argv[1:])
