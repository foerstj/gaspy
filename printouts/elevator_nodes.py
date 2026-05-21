import argparse

import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.terrain import TerrainNode
from gas.molecules import Hex


ELE_MESHES = {
    't_xxx_wal_displacer_pad': 'main',
    't_xxx_dgn_flr_ele-round-platform-01': 'tight',
    't_xxx_dgn_flr_ele-round-platform-03': 'main',
    't_dgn02_flr_ele-round-platform-04': 'main',
    't_xxx_ledg_ele-platform-a': 'tight',
    't_gi_gad_closet-dor-a': False,
    't_gi_gad_closet-dor-b': False,
    't_xxx_dgn_wal_ex-secretdoor-thin-a': False,
    't_dc01_skull-dgn-jaw-b': False,
}


def elevator_nodes(map_name: str, bits_path: str):
    bits = Bits(bits_path)

    the_map = bits.maps[map_name]
    nodes_by_guid: dict[Hex, TerrainNode] = {}
    print('loading terrain', end='')
    for region in the_map.get_regions().values():
        print('.', end='')
        for node in region.get_terrain().nodes:
            nodes_by_guid[node.guid] = node
    print()

    elevators_file = bits.gas_dir.get_subdir('world').get_subdir('global').get_gas_file('elevators')
    gas = elevators_file.get_gas()
    list_eles = gas.get_section('elevators').get_section('maps').get_section(map_name)
    list_eles_main: list[Hex] = list()
    list_eles_tight: list[Hex] = list()
    if list_eles is not None:
        list_section_main = list_eles.get_section('elevatorGuids')
        list_section_tight = list_eles.get_section('elevatorTightGuids')
        list_eles_main = [Hex.parse(attr.value) for attr in list_section_main.get_attrs()]
        list_eles_tight = [Hex.parse(attr.value) for attr in list_section_tight.get_attrs()]
        print('list main', ', '.join([str(guid) for guid in list_eles_main]))
        print('list tight', ', '.join([str(guid) for guid in list_eles_tight]))

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
    unspecified_meshes: set[str] = set()
    for ele in map_eles:
        if 'hidden_stairwell' in ele.template_name:
            continue
        ele_section = ele.section.get_section(ele.template_name)
        ele_node_guid = ele_section.get_attr_value('elevator_node')
        assert ele_node_guid is not None, f'{ele.object_id} {ele.template_name}'
        assert ele_node_guid in nodes_by_guid, f'{ele.object_id} {ele.template_name}: {ele_node_guid}'
        ele_node = nodes_by_guid[ele_node_guid]
        formation_type = ELE_MESHES.get(ele_node.mesh_name)
        print(f'{ele.object_id} {ele.template_name}: {ele_node_guid} {ele_node.mesh_name} -> {formation_type}')
        if formation_type:
            ele_node_guids.append(ele_node_guid)
        if formation_type is None:
            unspecified_meshes.add(ele_node.mesh_name)
    print(f'ele gizmo node guids: {len(ele_node_guids)}')
    print(f'ele list node guids: {len(list_eles_main) + len(list_eles_tight)}')
    missing = [guid for guid in ele_node_guids if guid not in list_eles_main and guid not in list_eles_tight]
    print('missing', ', '.join([str(m) for m in missing]))
    print('unspecified', ', '.join(unspecified_meshes))


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
