"""
Script to convert wal_08-pth nodes to separate nodes by door texture (floor or path).
See minibits:dev/door-tx-nodes
"""

import argparse

import sys

from bits.bits import Bits
from bits.maps.region import Region


def convert_door_tx_nodes_region(region: Region):
    terrain = region.get_terrain()
    num_changed = 0
    for node in terrain.nodes:
        if node.mesh_name in ['t_xxx_wal_08-pth-l', 't_xxx_wal_08-pth-r']:
            door_texture = {'grs01': 'path', 'grs02': 'floor'}[node.texture_set]
            node.mesh_name += f'-{door_texture}'
            num_changed += 1
    print(f'{region.get_name()}: {num_changed} nodes changed')
    if num_changed > 0:
        region.save()


def run_door_tx_nodes(bits_path: str, map_name: str, region_name: str):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    convert_door_tx_nodes_region(region)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy door-tx-nodes')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    run_door_tx_nodes(args.bits, args.map, args.region)


if __name__ == '__main__':
    main(sys.argv[1:])
