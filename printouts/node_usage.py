import argparse

import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.snos import SNOs
from gas.gas_parser import GasParser


def get_node_usage(m: Map, usages: dict):
    for region in m.get_regions().values():
        for node_mesh_name in region.get_node_meshes():
            assert node_mesh_name in usages, node_mesh_name
            usages[node_mesh_name] = True


def node_usage(bits: Bits, node_bits: Bits):
    snos = node_bits.snos
    print(f'SNOs: {len(snos.snos)}')
    # snos.print('  ', None)
    usages = {SNOs.get_name_for_path(sno_path): None for sno_path in snos.snos}

    maps = bits.maps
    print(f'Maps: {len(maps)}')
    for m in maps.values():
        m.print()
        get_node_usage(m, usages)

    print('Usages:')
    for node_mesh_name, usage in usages.items():
        print(f'  {node_mesh_name}: {usage}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printouts node_usage')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--node-bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    GasParser.get_instance().print_warnings = False
    bits = Bits(args.bits)
    node_bits = bits if args.node_bits is None else Bits(args.node_bits)
    node_usage(bits, node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
