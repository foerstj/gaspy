import argparse

import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.map import Map
from bits.maps.terrain import TerrainNode
from gas.gas import Gas, Section, Attribute
from gas.molecules import Hex


ELE_MESHES = {
    # elevators - generic
    't_xxx_dgn_flr_ele-grate-a': 'tight',  # bit too small, but better than not
    't_xxx_dgn_flr_ele-grate-b': 'tight',  # bit too small, but better than not
    't_xxx_dgn_flr_ele-round-platform-01': 'tight',
    't_xxx_dgn_flr_ele-round-platform-02': 'tight',
    't_xxx_dgn_flr_ele-round-platform-03': 'main',
    't_xxx_dgn_flr_ele-round-platform-04': 'main',
    't_xxx_dgn_flr_ele-round-platform-05': 'tight',
    't_xxx_dgn_flr_ele-round-platform-nochain': 'tight',
    't_xxx_dgn_flr_ele-platform-04x04-a': 'main',
    't_xxx_keep_flr_ele-platform-a': 'main',
    't_xxx_ledg_ele-platform-a': 'tight',
    't_xxx_ruin_flr-sinkhole-ele-a': False,  # one-off and surprise
    't_xxx_wal_displacer_pad': 'main',
    # elevators - other
    't_ce_lv1_i-ele-platform': 'main',
    't_dgn02_flr_ele-round-platform-04': 'main',
    't_dm01_ele_1a-big': 'main',
    't_dm01_ele_crane-02-big': 'tight',
    't_dm01_ele_crane-swivel-big': False,  # off center
    't_dm01_ele_exit': 'main',
    't_gi_exit-ele': False,  # off center, big enough anyway
    't_gi_gad_plat-a': 'main',
    't_gi_lift_1-a': 'main',
    't_gom_ele-platform': False,  # too big
    't_icetwr_elevator-a': 'main',
    't_icetwr_final-elevator-a': 'main',
    't_nt01_watchtower-ele-plank': False,  # too small
    't_sd_cage': 'main',
    't_th01_teleport-hub-elevator-45-a': 'main',
    't_th01_teleport-hub-elevator-a': 'main',

    # not elevators - generic
    't_xxx_brdg_tx-rop-wal-32': False,  # koe
    't_xxx_cnr_32-cnvx': False,  # koe
    't_xxx_dgn_flr_trap-cover-a': False,
    't_xxx_dgn_flr_trap-cover-b': False,
    't_xxx_dgn_flr_trap-cover-c': False,
    't_xxx_dgn_flr_trap-cover-diaz-a': False,
    't_xxx_dgn_wal_ex-secretdoor-thin-a': False,
    't_xxx_flr_08x08-v0': False,  # yesterhaven
    't_xxx_wal_cave-split-24-rock-secret-a': False,
    't_xxx_wal_cave-split-24-slidingfloor-secret-a': False,
    # not elevators - other
    't_cd01_wd_wal-grate-door-a': False,
    't_cry01_sec_firehole-1b': False,
    't_cry01_sec_wal-1b-door': False,
    't_cry01_trap_flr-1b': False,
    't_cry01_trap_flr-2b': False,
    't_dc01_skull-dgn-jaw-a': False,
    't_dc01_skull-dgn-jaw-b': False,
    't_dgn02_bridge_bridge-ele-cos': False,
    't_dm01_quarters_door-a': False,
    't_dm01_ele_exit-base-door': False,
    't_dm01_gib-machine-trap': False,
    't_gi_flr_trap-1-b': False,
    't_gi_flr_trap-2-b': False,
    't_gi_flr_trap-3-b': False,
    't_gi_flr_trap-4-b': False,
    't_gi_flr_trap-4-c': False,
    't_gi_gad_closet-dor-a': False,
    't_gi_gad_closet-dor-b': False,
    't_gi_gad_flr-cplate-b': False,
    't_gom_throne-platform': False,
    't_sc01_shrine-bdg-tile-2x2': False,
    't_sc01_shrine-flr-press-plate': False,
    't_sd_cage-clamp': False,
    't_sd_wal_int_04-doorway-door-a': False,
    't_sd_wal_int_04-doorway-door-b': False,
    't_sd_wal_int_04-doorway-door-c': False,
    't_world3_obelisk-grs01-platform-a': False,  # no ele semantically, and has own positioning
}


def get_elevator_node_guids_for_map(the_map: Map, assert_no_unspecified_meshes=False) -> (list[Hex], list[Hex]):
    nodes_by_guid: dict[Hex, TerrainNode] = {}
    print('loading terrain', end='')
    for region in the_map.get_regions().values():
        print('.', end='')
        for node in region.get_terrain().nodes:
            nodes_by_guid[node.guid] = node
    print()

    print('reading gizmos')
    map_eles: list[GameObject] = list()
    for region in the_map.get_regions().values():
        region_eles = region.objects.do_load_objects_elevator()
        if region_eles is not None:
            map_eles.extend(region_eles)
    main_guids: list[Hex] = []
    tight_guids: list[Hex] = []
    unspecified_meshes: set[str] = set()
    for ele in map_eles:
        if 'hidden_stairwell' in ele.template_name:
            continue
        ele_section = ele.section.get_section(ele.template_name)
        ele_node_guid = ele_section.get_attr_value('elevator_node')
        assert ele_node_guid is not None, f'{ele.object_id} {ele.template_name}'
        assert ele_node_guid in nodes_by_guid, f'{ele.object_id} {ele.template_name}: {ele_node_guid}'
        ele_node = nodes_by_guid[ele_node_guid]
        formation_type = ELE_MESHES.get(ele_node.mesh_name.lower())
        print(f'{ele.object_id} {ele.template_name}: {ele_node_guid} {ele_node.mesh_name} -> {formation_type}')
        if formation_type == 'main':
            main_guids.append(ele_node_guid)
        elif formation_type == 'tight':
            tight_guids.append(ele_node_guid)
        if formation_type is None:
            unspecified_meshes.add(ele_node.mesh_name)
    print(f'ele gizmo node guids: {len(main_guids)} main, {len(tight_guids)} tight')
    if len(unspecified_meshes) > 0:
        print('unspecified meshes:')
        for mesh in sorted(unspecified_meshes):
            print(f' - {mesh.lower()}')
    if assert_no_unspecified_meshes and len(unspecified_meshes) > 0:
        assert False, 'unspecified meshes'
    return main_guids, tight_guids


def read_elevators_gas(bits: Bits) -> dict[str, (list[Hex], list[Hex])]:
    elevators_file = bits.gas_dir.get_subdir('world').get_subdir('global').get_gas_file('elevators')
    gas = elevators_file.get_gas()
    maps_section = gas.get_section('elevators').get_section('maps')
    data = {}
    for map_section in maps_section.get_sections():
        map_name = map_section.header
        main_section = map_section.get_section('elevatorGuids')
        tight_section = map_section.get_section('elevatorTightGuids')
        main_guids = [Hex.parse(attr.value) for attr in main_section.get_attrs()]
        tight_guids = [Hex.parse(attr.value) for attr in tight_section.get_attrs()]
        print(f'{map_name}: ' + ', '.join([str(g) for g in main_guids]) + '; tight: ' + ', '.join([str(g) for g in tight_guids]))
        data[map_name] = (main_guids, tight_guids)
    return data


def write_elevators_gas(bits: Bits, data: dict[str, (list[Hex], list[Hex])]):
    map_sections: list[Section] = []
    for map_name, (main_guids, tight_guids) in data.items():
        main_section = Section('elevatorGuids', [Attribute('*', str(guid)) for guid in main_guids])
        tight_section = Section('elevatorTightGuids', [Attribute('*', str(guid)) for guid in tight_guids])
        map_section = Section(map_name, [main_section, tight_section])
        map_sections.append(map_section)
    gas = Gas([
        Section('elevators', [
            Section('maps', map_sections)
        ])
    ])
    elevators_file = bits.gas_dir.get_subdir('world').get_subdir('global').get_gas_file('elevators')
    elevators_file.gas = gas
    elevators_file.save()


def compare_map_with_list(map_main_guids: list[Hex], map_tight_guids: list[Hex], list_main_guids: list[Hex], list_tight_guids: list[Hex], assert_guids_in_list=False):
    missing_main_list = [guid for guid in map_main_guids if guid not in list_main_guids]
    missing_main_map = [guid for guid in list_main_guids if guid not in map_main_guids]
    missing_tight_list = [guid for guid in map_tight_guids if guid not in list_tight_guids]
    missing_tight_map = [guid for guid in list_tight_guids if guid not in map_tight_guids]
    if len(missing_main_list) > 0:
        print('missing in main list', ', '.join([str(m) for m in missing_main_list]))
    if len(missing_tight_list) > 0:
        print('missing in tight list', ', '.join([str(m) for m in missing_tight_list]))
    if len(missing_main_map) > 0:
        print('main missing in map', ', '.join([str(m) for m in missing_main_map]))
    if len(missing_tight_map) > 0:
        print('tight missing in map', ', '.join([str(m) for m in missing_tight_map]))
    if assert_guids_in_list:
        if len(missing_main_list) + len(missing_tight_list) > 0:
            assert False, 'guids missing in list'


def evaluate_map(map_name: str, bits: Bits, list_data: dict[str, (list[Hex], list[Hex])], asserts: list[str]):
    the_map = bits.maps[map_name]
    assert_no_unspecified_meshes = 'no-unspecified-meshes' in asserts
    map_main_guids, map_tight_guids = get_elevator_node_guids_for_map(the_map, assert_no_unspecified_meshes)

    if map_name not in list_data:
        print(f'map {map_name} is not in node guids list')
        if 'map-in-list' in asserts:
            assert False, map_name
        return
    list_main_guids, list_tight_guids = list_data[map_name]
    assert_guids_in_list = 'guids-in-list' in asserts
    compare_map_with_list(map_main_guids, map_tight_guids, list_main_guids, list_tight_guids, assert_guids_in_list)


def elevator_nodes(map_names: list[str], assert_no_unspecified_meshes: bool, update_lists: bool, bits_path: str):
    bits = Bits(bits_path)
    list_data = read_elevators_gas(bits)

    if map_names is not None:
        for map_name in map_names:
            the_map = bits.maps[map_name]
            map_main_guids, map_tight_guids = get_elevator_node_guids_for_map(the_map, assert_no_unspecified_meshes)
            if map_name in list_data:
                list_main_guids, list_tight_guids = list_data[map_name]
                compare_map_with_list(map_main_guids, map_tight_guids, list_main_guids, list_tight_guids)
            list_data[map_name] = map_main_guids, map_tight_guids

    if update_lists:
        write_elevators_gas(bits, list_data)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy elevator-nodes')
    parser.add_argument('--eval-maps', nargs='+', help='evaluate these maps (extract ele guids and compare with lists)')
    parser.add_argument('--assert-no-unspecified-meshes', action='store_true')
    parser.add_argument('--update-lists', action='store_true')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    elevator_nodes(args.eval_maps, args.assert_no_unspecified_meshes, args.update_lists, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
