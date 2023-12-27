import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region


def check_tips_in_region(region: Region, tip_names: list[str]) -> set[str]:
    invalid_tip_names = set()
    special_objects = region.objects.do_load_objects_special() or list()
    for obj in special_objects:
        tip_section = obj.section.get_section('tip')
        if not tip_section:
            continue
        tip_attr = tip_section.get_attr('tip')
        assert tip_attr
        tip_name = tip_attr.value.strip().strip('"').strip()
        if tip_name not in tip_names:
            print(f'Invalid tip name in {region.get_name()} {obj.object_id}: {tip_name}')
            invalid_tip_names.add(tip_name)
    return invalid_tip_names


def check_tips(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    _map.load_tips()
    tip_names = list(_map.tips.tips.keys())
    invalid_tip_names = set()
    print(f'Checking tips in {map_name}...')
    for region in _map.get_regions().values():
        region_invalid_tip_names = check_tips_in_region(region, tip_names)
        invalid_tip_names.update(region_invalid_tip_names)
    print(f'Checking tips in {map_name}: {len(invalid_tip_names)} distinct invalid tip names')
    return len(invalid_tip_names) == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_tips')
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
    valid = check_tips(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
