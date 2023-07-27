import argparse

import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.snos import SNOs
from gas.gas_parser import GasParser


def init_usages(usage_type: str, mesh_names: list[str]):
    default_value = False if usage_type == 'used' else 0
    usages = {mesh_name: default_value for mesh_name in mesh_names}
    return usages


def get_node_usage_in_map(usage_type: str, m: Map, usages: dict):
    assert usage_type in ['used', 'count-maps']
    map_usages = init_usages(usage_type, list(usages.keys()))

    for region in m.get_regions().values():
        num_nodes = len(region.get_terrain().nodes)
        num_meshes = len(region.get_node_meshes())
        print(f'  {region.get_name()}: {num_nodes} nodes, {num_meshes} meshes')

        for mesh_name in region.get_node_meshes():
            assert mesh_name in map_usages, mesh_name
            map_usages[mesh_name] = True

    for mesh_name in usages:
        if usage_type == 'used':
            usages[mesh_name] |= map_usages[mesh_name]
        elif usage_type == 'count-maps':
            usages[mesh_name] += map_usages[mesh_name]


def get_node_usage(usage_type: str, maps, mesh_names: list[str]):
    usages = init_usages(usage_type, mesh_names)

    print(f'Maps: {len(maps)}')
    for m in maps.values():
        m.print()
        get_node_usage_in_map(usage_type, m, usages)

    return usages


def node_usage(usage_type: str, map_names: list[str] = None, count_usage_values=False, bits_path=None, node_bits_path=None):
    if map_names is None:
        map_names = list()

    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)
    node_bits = bits if node_bits_path is None else Bits(node_bits_path)

    snos = node_bits.snos
    print(f'SNOs: {len(snos.snos)}')
    mesh_names = [SNOs.get_name_for_path(sno_path) for sno_path in snos.snos]

    maps = bits.maps
    maps = {n: m for n, m in maps.items() if len(map_names) == 0 or n in map_names}

    usages = get_node_usage(usage_type, maps, mesh_names)

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
    parser.add_argument('--usage', choices=['used', 'count-maps'], default='used')
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
    node_usage(args.usage, args.maps, args.count_usage_values, args.bits, args.node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
