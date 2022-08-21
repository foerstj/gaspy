import sys

from bits.bits import Bits


def main(argv):
    bits_path = argv[0] if len(argv) > 0 else None
    bits = Bits(bits_path)
    for name, template in bits.templates.get_leaf_templates('actor').items():
        size_base = template.compute_value('aspect', 'scale_base') or 1
        print(f'{name}: {size_base}')


if __name__ == '__main__':
    main(sys.argv[1:])
