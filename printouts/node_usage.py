import argparse

import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.snos import SNOs
from gas.gas_parser import GasParser


def get_node_usage(m: Map, usages: dict):
    for region in m.get_regions().values():
        num_nodes = len(region.get_terrain().nodes)
        num_meshes = len(region.get_node_meshes())
        print(f'  {region.get_name()}: {num_nodes} nodes, {num_meshes} meshes')
        for node_mesh_name in region.get_node_meshes():
            assert node_mesh_name in usages, node_mesh_name
            usages[node_mesh_name] = True


def node_usage(map_names: list[str] = None, count_usage_values=False, bits_path=None, node_bits_path=None):
    if map_names is None:
        map_names = list()

    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)
    node_bits = bits if node_bits_path is None else Bits(node_bits_path)

    snos = node_bits.snos
    print(f'SNOs: {len(snos.snos)}')
    usages = {SNOs.get_name_for_path(sno_path): None for sno_path in snos.snos}

    maps = bits.maps
    maps = {n: m for n, m in maps.items() if len(map_names) == 0 or n in map_names}
    print(f'Maps: {len(maps)}')
    for m in maps.values():
        m.print()
        get_node_usage(m, usages)

    print('Usages:')
    for node_mesh_name, usage in usages.items():
        print(f'  {node_mesh_name}: {usage}')
    if count_usage_values:
        usage_value_counts = {v: 0 for v in usages.values()}
        for usage_value in usages.values():
            usage_value_counts[usage_value] += 1
        print('Usage value summary:')
        for usage_value, count in usage_value_counts.items():
            print(f'  {usage_value}: {count}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printouts node_usage')
    parser.add_argument('--maps', nargs='*')
    parser.add_argument('--count-usage-values', action='store_true')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--node-bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    node_usage(args.maps, args.count_usage_values, args.bits, args.node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
