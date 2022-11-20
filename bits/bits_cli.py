import argparse
import sys

from bits.bits import Bits


def print_maps(bits: Bits, map_info=None, region_info=None):
    maps = bits.maps
    print('Maps: ' + str(len(maps)))
    for m in maps.values():
        m.print(map_info, region_info)


def print_templates(bits: Bits, template_info=None):
    templates = bits.templates.get_templates()
    print('Templates: ' + str(len(templates)))
    for template in templates.values():
        template.print(template_info)


def print_snos(bits: Bits):
    bits.snos.print()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Bits')
    parser.add_argument('--bits', default='DSLOA')
    parser.add_argument('--print', choices=['maps', 'templates', 'snos'])
    parser.add_argument('--print-map-info', nargs='?', choices=['npcs', 'enemies-total', 'shops'])
    parser.add_argument('--print-region-info', nargs='?', choices=['actors', 'stitches', 'xp', 'plants', 'data'])
    parser.add_argument('--print-template-info', nargs='?', choices=['base', 'children'])
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits = Bits(args.bits)
    if args.print == 'maps':
        print_maps(bits, args.print_map_info, args.print_region_info)
    if args.print == 'templates':
        print_templates(bits, args.print_template_info)
    if args.print == 'snos':
        print_snos(bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
