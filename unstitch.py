import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region


def unstitch_region(region: Region) -> int:
    region_stitches = region.get_stitch_helper()
    num_rem_stitches = sum([len(se.node_ids) for se in region_stitches.stitch_editors])
    region_stitches.stitch_editors = list()
    print(f'  {region.get_name()}: {num_rem_stitches}')
    if num_rem_stitches > 0:
        region.save()
    return num_rem_stitches


def unstitch(m: Map):
    print(f'Unstitching {m.get_name()}...')
    num_rem_stitches = 0
    for region in m.get_regions().values():
        num_rem_stitches += unstitch_region(region)
    print(f'Unstitching {m.get_name()} done: {num_rem_stitches} stitches removed.')


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description='GasPy Unstitch')
    parser.add_argument('map', help='name of the map to unstitch')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_name = args.map
    bits = Bits()
    m = bits.maps[map_name]
    unstitch(m)


if __name__ == '__main__':
    main(sys.argv[1:])
