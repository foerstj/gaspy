import argparse

import sys

from bits.bits import Bits
from bits.maps.terrain import TerrainNode
from gas.molecules import Hex


def elevator_nodes(bits_path: str):
    bits = Bits(bits_path)
    elevators_file = bits.gas_dir.get_subdir('world').get_subdir('global').get_gas_file('elevators')
    gas = elevators_file.get_gas()
    loa_eles = gas.get_section('elevators').get_section('maps').get_section('map_expansion')
    loa_eles_main = loa_eles.get_section('elevatorGuids')
    loa_eles_tight = loa_eles.get_section('elevatorTightGuids')
    loa_eles_main = [Hex.parse(attr.value) for attr in loa_eles_main.get_attrs()]
    loa_eles_tight = [Hex.parse(attr.value) for attr in loa_eles_tight.get_attrs()]
    print(loa_eles_main)
    print(loa_eles_tight)

    loa_map = bits.maps['map_expansion']
    nodes_by_id: dict[Hex, TerrainNode] = {}
    meshes: set[str] = set()
    print('Loading terrain', end='')
    for region in loa_map.get_regions().values():
        print('.', end='')
        for node in region.get_terrain().nodes:
            nodes_by_id[node.guid] = node
        meshes.update(set(region.get_terrain().node_mesh_index.values()))
    print()
    print([mesh for mesh in meshes if 'ele' in mesh or 'plat' in mesh or 'pad' in mesh or 'hub' in mesh])

    for guid in loa_eles_main:
        node = nodes_by_id[guid]
        print(f'{guid}: {node.mesh_name}')
    print()
    for guid in loa_eles_tight:
        node = nodes_by_id[guid]
        print(f'{guid}: {node.mesh_name}')

    main_meshes = set([nodes_by_id[guid].mesh_name for guid in loa_eles_main])
    print(main_meshes)
    tight_meshes = set([nodes_by_id[guid].mesh_name for guid in loa_eles_tight])
    print(tight_meshes)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printout elevator nodes')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    elevator_nodes(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
