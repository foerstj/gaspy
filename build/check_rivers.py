import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode

IN = True
OUT = False
RIVER_DATA = {
    't_fh00_barn_1a': {5: IN, 3: OUT},
    't_fh00_bridge_1a': {5: IN, 6: IN, 1: OUT, 2: OUT},
    't_fh00_wfall_1b': {5: IN, 1: OUT},
    't_fh00_wheeletc': {6: IN, 7: IN, 1: OUT, 2: OUT},

    't_xxx_rvr_08-bridge-left-tx-right-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-bridge-right-tx-left-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-left-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-left-b': {4: IN, 1: OUT},
    't_xxx_rvr_08-left-turn': {4: IN, 3: OUT},
    't_xxx_rvr_08-left-tx-right-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-right-a': {4: IN, 1: OUT},
    't_xxx_rvr_08-right-b': {4: IN, 1: OUT},
    't_xxx_rvr_08-right-turn': {5: IN, 6: OUT},
    't_xxx_rvr_08-right-tx-left-a': {4: IN, 1: OUT},
    't_xxx_rvr_12-left-a': {3: IN, 1: OUT},
    't_xxx_rvr_12-left-b': {3: IN, 1: OUT},
    't_xxx_rvr_12-left-c': {3: IN, 1: OUT},
    't_xxx_rvr_12-right-a': {4: IN, 1: OUT},
    't_xxx_rvr_12-right-b': {4: IN, 1: OUT},
    't_xxx_rvr_12-right-c': {4: IN, 1: OUT},
    't_xxx_rvr_12-tx-08-left-a': {5: IN, 6: IN, 1: OUT},
    't_xxx_rvr_12-tx-08-left-b': {6: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_12-tx-08-right-a': {5: IN, 6: IN, 2: OUT},
    't_xxx_rvr_12-tx-08-right-b': {5: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_wfall-04-tx-12': {4: IN, 5: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_wfall-04-tx-wal-02': {6: IN, 7: IN},
    't_xxx_rvr_wfall-08-tx-12': {4: IN, 5: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_wfall-08-tx-wal-02': {6: IN, 7: IN},
    't_xxx_rvr_wfall-12-tx-12': {4: IN, 5: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_wfall-12-tx-wal-02': {6: IN, 7: IN},
    't_xxx_rvr_wfall-24-tx-12': {4: IN, 5: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_wfall-24-tx-wal-02': {6: IN, 7: IN},
    't_xxx_rvr_wfall-32-tx-12': {4: IN, 5: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_wfall-32-tx-wal-02': {6: IN, 7: IN},
    't_xxx_rvr_wfall-rmp-tx-12': {4: IN, 5: IN, 1: OUT, 2: OUT},
    't_xxx_rvr_wfall-rmp-tx-wal-02': {6: IN, 7: IN},

    't_xxx_wal_04-tx-rvr-in': {1: IN, 2: IN},
    't_xxx_wal_04-tx-rvr-out': {1: OUT, 2: OUT},
    't_xxx_wal_08-tx-rvr-in': {1: IN, 2: IN},
    't_xxx_wal_08-tx-rvr-out': {1: OUT, 2: OUT},
    't_xxx_wal_12-tx-rvr-in': {1: IN, 2: IN},
    't_xxx_wal_12-tx-rvr-out': {1: OUT, 2: OUT},
    't_xxx_wal_24-tx-rvr-in': {1: IN, 2: IN},
    't_xxx_wal_24-tx-rvr-out': {1: OUT, 2: OUT},
    't_xxx_wal_32-tx-rvr-in': {1: IN, 2: IN},
    't_xxx_wal_32-tx-rvr-out': {1: OUT, 2: OUT},

    't_grs01_waterfall-alcove-d': {9: OUT, 10: OUT},
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
