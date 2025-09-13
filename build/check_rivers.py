import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode

IN = True
OUT = False
RIVER_DATA = {
    't_xxx_rvr_08-left-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-left-b': {4: IN, 1: OUT},
    't_xxx_rvr_08-left-turn': {4: IN, 3: OUT},
    't_xxx_rvr_08-left-tx-right-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-right-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-right-b': {4: IN, 1: OUT},
    't_xxx_rvr_08-right-turn': {5: IN, 6: OUT},
    't_xxx_rvr_08-right-tx-left-a': {4: IN, 1: OUT},
}


def check_rivers_in_region(region: Region) -> int:
    num_mismatches = 0
    terrain = region.get_terrain()
    for node in terrain.nodes:
        if node.mesh_name in RIVER_DATA:
            node_river_data = RIVER_DATA[node.mesh_name]
            for door in node_river_data:
                if door not in node.doors:
                    continue  # door not connected
                other_node, other_door = node.doors[door]
                assert isinstance(other_node, TerrainNode)
                if other_node.guid > node.guid:
                    continue  # count each pair only once
                other_node_river_data = RIVER_DATA[other_node.mesh_name]
                if node_river_data[door] == other_node_river_data[other_door]:
                    print(f'River mismatch in {region.get_name()}: {node.guid} {door}')
                    num_mismatches += 1
    return num_mismatches


def check_rivers(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    num_mismatches = 0
    print(f'Checking rivers in {map_name}...')
    for region in _map.get_regions().values():
        num_mismatches += check_rivers_in_region(region)
    print(f'Checking rivers in {map_name}: {num_mismatches} mismatches')
    return num_mismatches == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_rivers')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    bits = Bits(args.bits)
    valid = check_rivers(bits, args.map)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
