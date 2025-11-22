import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region
from gas.molecules import Quaternion, Position


def check_shrines_in_region(region: Region):
    num_misaligned = 0
    objs = region.objects.do_load_objects_special()
    if objs is None:
        return num_misaligned
    shrines = [obj for obj in objs if obj.template_name in ['mana_shrine', 'life_shrine']]
    for shrine in shrines:
        problems = []
        pos: Position = shrine.get_own_value('placement', 'position')
        ori: Quaternion = shrine.get_own_value('placement', 'orientation')
        if ori is not None:
            problems.append('misoriented')  # shrine gizmos should be default-oriented
        correct_y = 0 if shrine.template_name == 'mana_shrine' else -0.5
        if pos.x != 0 or pos.y != correct_y or pos.z != 0:
            problems.append('misplaced')
        if len(problems) > 0:
            print(f'  {shrine.template_name} in region {region.get_name()}: ' + ', '.join(problems))
            num_misaligned += 1
    return num_misaligned


def check_shrines(bits: Bits, map_name: str):
    m = bits.maps[map_name]
    num_misaligned = 0
    print(f'Checking shrines in {map_name}...')
    for region in m.get_regions().values():
        num_misaligned += check_shrines_in_region(region)
    print(f'Checking shrines in {map_name}: {num_misaligned} misaligned shrine gizmos')
    return num_misaligned == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_shrines')
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
    valid = check_shrines(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
