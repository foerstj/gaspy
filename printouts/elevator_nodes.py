import argparse

import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.terrain import TerrainNode
from gas.molecules import Hex


def elevator_nodes(map_name: str, bits_path: str):
    bits = Bits(bits_path)
    elevators_file = bits.gas_dir.get_subdir('world').get_subdir('global').get_gas_file('elevators')
    gas = elevators_file.get_gas()
    list_eles = gas.get_section('elevators').get_section('maps').get_section(map_name)
    list_eles_main = list_eles.get_section('elevatorGuids')
    list_eles_tight = list_eles.get_section('elevatorTightGuids')
    list_eles_main = [Hex.parse(attr.value) for attr in list_eles_main.get_attrs()]
    list_eles_tight = [Hex.parse(attr.value) for attr in list_eles_tight.get_attrs()]
    print('list main', ', '.join([str(guid) for guid in list_eles_main]))
    print('list tight', ', '.join([str(guid) for guid in list_eles_tight]))

    the_map = bits.maps[map_name]
    nodes_by_guid: dict[Hex, TerrainNode] = {}
    meshes: set[str] = set()
    print('loading terrain', end='')
    for region in the_map.get_regions().values():
        print('.', end='')
        for node in region.get_terrain().nodes:
            nodes_by_guid[node.guid] = node
        meshes.update(set(region.get_terrain().node_mesh_index.values()))
    print()
    matching_meshes = [mesh for mesh in meshes if 'ele' in mesh or 'plat' in mesh or 'pad' in mesh or 'hub' in mesh]
    matching_meshes = [mesh for mesh in matching_meshes if not ('tube' in mesh or 'strip' in mesh or 'doortop' in mesh or 'doorsides' in mesh)]
    print('used matching mesh names', matching_meshes)

    print('meshes in main list')
    for guid in list_eles_main:
        node = nodes_by_guid[guid]
        print(f'{guid}: {node.mesh_name}')
    print('meshes in tight list')
    for guid in list_eles_tight:
        node = nodes_by_guid.get(guid)
        print(f'{guid}: {node.mesh_name if node else None}')

    main_meshes = set([nodes_by_guid[guid].mesh_name for guid in list_eles_main])
    print('main meshes', main_meshes)
    tight_nodes = [nodes_by_guid.get(guid) for guid in list_eles_tight]
    tight_meshes = set([node.mesh_name for node in tight_nodes if node is not None])
    print('tight meshes', tight_meshes)

    print('reading gizmos')
    map_eles: list[GameObject] = list()
    for region in the_map.get_regions().values():
        region_eles = region.objects.do_load_objects_elevator()
        if region_eles is not None:
            map_eles.extend(region_eles)
    ele_node_guids: list[Hex] = []
    for ele in map_eles:
        ele_section = ele.section.get_section(ele.template_name)
        ele_node_guid = ele_section.get_attr_value('elevator_node')
        ele_node = nodes_by_guid[ele_node_guid]
        print(f'{ele.object_id} {ele.template_name}: {ele_node_guid} {ele_node.mesh_name}')
        ele_node_guids.append(ele_node_guid)
    print(f'ele gizmo node guids: {len(ele_node_guids)}')
    print(f'ele list node guids: {len(list_eles_main) + len(list_eles_tight)}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printout elevator nodes')
    parser.add_argument('map_name')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    elevator_nodes(args.map_name, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
