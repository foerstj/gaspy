import os
import sys

from bits.bits import Bits
from bits.maps.region import Region
from gas.molecules import Hex
from region_import import check_dupe_node_ids
from region_import.edit_region_ids import edit_region_guid, edit_region_scid_range, edit_region_mesh_range
from region_import.import_region import copy_region_dir
from region_import.replace_hexes import replace_hexes_in_dir


def inc_region_node_ids(region: Region, inc=1):
    # step 1: collect node ids and delete the terrain lnc file
    node_ids = region.get_node_ids()
    lnc_file = os.path.join(region.gas_dir.get_subdir('terrain_nodes').path, 'siege_nodes.lnc')
    if os.path.isfile(lnc_file):
        os.remove(lnc_file)

    # step 2: textually replace all node ids in all region files
    hexes = [(node_id, Hex(node_id + inc)) for node_id in node_ids]
    replace_hexes_in_dir(region.gas_dir.path, hexes)


def copy_region(map_name, old_region_name, new_region_name):
    bits = Bits()
    m = bits.maps[map_name]
    check_dupe_node_ids.check_map(m)
    regions = m.get_regions()
    old_region = regions.get(old_region_name)
    assert old_region is not None, f'Region {old_region_name} does not exist'
    assert regions.get(new_region_name) is None, f'Region {new_region_name} already exists'
    print(f'Copying region in map {map_name}: {old_region_name} -> {new_region_name}')

    new_region = copy_region_dir(old_region, m, new_region_name)
    # Ok now world-levels aren't a problem and neither is NMI,
    # but of course now we have conflicting region ids and node ids!

    edit_region_guid(new_region, Hex(old_region.get_data().id+1), isolated=True)
    edit_region_scid_range(new_region, Hex(old_region.get_data().scid_range+1), isolated=True)
    edit_region_mesh_range(new_region, Hex(old_region.get_data().mesh_range+1))  # technically not necessary but for good measure...
    print('Incrementing node ids of new region...')
    inc_region_node_ids(new_region)

    new_region.print()
    print('Copying region done. Recommend to git-commit, then open & save in Siege Editor.')


def main(argv):
    map_name = argv[0]
    old_region_name = argv[1]
    new_region_name = argv[2]
    copy_region(map_name, old_region_name, new_region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
