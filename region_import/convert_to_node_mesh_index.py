import sys

from bits.node_mesh_guids import NodeMeshGuids
from gas.gas import Section, Hex, Gas, Attribute
from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region


def print_node_mesh_guids(node_mesh_guids: dict[str, str]):
    print('node_mesh_guids:')
    for guid, file_name in sorted(node_mesh_guids.items()):
        print(f'  {guid}: {file_name}')


def convert_region(region: Region, nmg: NodeMeshGuids):
    index_dir = region.gas_dir.get_subdir('index')
    if index_dir.has_gas_file('node_mesh_index'):
        return
    nodes_file = region.gas_dir.get_subdir('terrain_nodes').get_gas_file('nodes')
    node_gas = nodes_file.get_gas()
    nodes_section: Section = node_gas.items[0]
    node_sections = nodes_section.get_sections()
    mesh_guid_attrs = [ns.get_attr('mesh_guid') for ns in node_sections]
    node_mesh_index = {}
    node_mesh_guids = nmg.get_node_mesh_guids()
    for mesh_guid_attr in mesh_guid_attrs:
        mesh_guid = mesh_guid_attr.value.to_str_lower()
        if mesh_guid == '0x0a801037':
            mesh_guid = '0xa801037g'  # wtf - map_world gi_r10 node 0xf0cce721 - 0xa801037g: t_gi_flr_04x04-b
        if mesh_guid not in node_mesh_guids:
            print_node_mesh_guids(node_mesh_guids)
            assert mesh_guid in node_mesh_guids, f'{mesh_guid} is not in node_mesh_guids!'
        if mesh_guid not in node_mesh_index:
            node_mesh_index[mesh_guid] = Hex(len(node_mesh_index) + 1)
        mesh_id = node_mesh_index[mesh_guid]
        mesh_guid_attr.value = mesh_id
    nodes_file.save()
    node_mesh_index_attrs = [Attribute(mesh_id, node_mesh_guids[mesh_guid]) for mesh_guid, mesh_id in node_mesh_index.items()]
    index_dir.create_gas_file('node_mesh_index', Gas([Section('node_mesh_index', node_mesh_index_attrs)])).save()
    region_data = region.get_data()
    if region_data.mesh_range == 0:
        if 0 < region_data.scid_range < Hex.parse('0x00001000'):
            region_data.mesh_range = region_data.scid_range
        elif 0 < region_data.id < Hex.parse('0x00001000'):
            region_data.mesh_range = region_data.id
        if region_data.mesh_range != 0:
            region.save()
    print(f'Converted region {region.get_name()} to NMI')


def convert_map(m: Map):
    if not m.get_data().use_node_mesh_index:
        m.get_data().use_node_mesh_index = True
        m.save()
        print(f'Converted map {m.get_data().screen_name} to NMI')


def convert_to_node_mesh_index(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]

    assert bits.gas_dir.has_subdir('world'), 'Conversion to NMI requires Bits/world/global/siege_nodes to be extracted'
    assert bits.gas_dir.get_subdir('world').has_subdir('global'), 'Conversion to NMI requires Bits/world/global/siege_nodes to be extracted'
    assert bits.gas_dir.get_subdir('world').get_subdir('global').has_subdir('siege_nodes'), 'Conversion to NMI requires Bits/world/global/siege_nodes to be extracted'
    nmg = bits.nmg

    if region_name is not None:
        print(region_name)
        region = m.get_region(region_name)
        convert_region(region, nmg)
    else:
        print(map_name)
        convert_map(m)
        for r_name, region in m.get_regions().items():
            print(r_name)
            convert_region(region, nmg)

    print('Done.')
    print('You have to open the converted region(s) in Siege Editor to complete the process.')


def main(argv):
    map_name = argv[0]
    region_name = argv[1] if len(argv) > 1 else None
    convert_to_node_mesh_index(map_name, region_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
