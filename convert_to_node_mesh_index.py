import sys

from bits import Bits
from gas import Section
from map import Map
from region import Region


def convert_region(region: Region):
    if 'node_mesh_index' in region.gas_dir.get_subdir('index').get_gas_files():
        return
    node_gas = region.gas_dir.get_subdir('terrain_nodes').get_gas_file('nodes').get_gas()
    nodes_section: Section = node_gas.items[0]
    node_sections = nodes_section.get_sections()
    mesh_guid_attrs = [ns.get_attr('mesh_guid') for ns in node_sections]
    mesh_guids = [str(a.value) for a in mesh_guid_attrs]
    print(set(mesh_guids))


def convert_map(m: Map):
    if not m.get_data().use_node_mesh_index:
        m.get_data().use_node_mesh_index = True
        m.save()


def convert_to_node_mesh_index(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]
    if region_name is not None:
        print(region_name)
        region = m.get_region(region_name)
        convert_region(region)
    else:
        print(map_name)
        convert_map(m)
        for r_name, region in m.get_regions().items():
            print(r_name)
            convert_region(region)


def main(argv):
    map_name = argv[0]
    region_name = argv[1] if len(argv) > 1 else None
    convert_to_node_mesh_index(map_name, region_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
