import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region


def check_empty_emitters_in_region(region: Region):
    emitters = region.objects.do_load_objects_emitter()
    # TODO then some magic happens
    return 0


def check_empty_emitters(bits: Bits, map_name: str):
    m = bits.maps[map_name]
    num_empty_emitters = 0
    print(f'Checking empty emitters in {map_name}...')
    for region in m.get_regions().values():
        num_empty_emitters += check_empty_emitters_in_region(region)
    print(f'Checking empty emitters in {map_name}: {num_empty_emitters} empty emitters')
    return num_empty_emitters == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_empty_emitters')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    map_name = args.map
    bits_path = args.bits
    bits = Bits(bits_path)
    valid = check_empty_emitters(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
