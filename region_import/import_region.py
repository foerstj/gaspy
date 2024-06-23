import shutil
import sys
import argparse
import os
import time

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from region_import import check_dupe_node_ids
from region_import.convert_to_node_mesh_index import convert_region, NodeMeshGuids
from world_levels import rem_region_world_levels


# copy files
def copy_region_dir(old_region: Region, to_map: Map, new_region_name=None) -> Region:
    if new_region_name is None:
        new_region_name = old_region.get_name()
    src = old_region.gas_dir.path
    dst = os.path.join(to_map.gas_dir.path, 'regions', new_region_name)
    shutil.copytree(src, dst)
    time.sleep(0.1)  # shutil...
    to_map.gas_dir.clear_cache()
    return to_map.get_region(new_region_name)


# check if guid/scid-range/mesh-range already exist in target map
def check_conflicting_region_ids(m: Map, region_data: Region.Data):
    for region in m.get_regions().values():
        assert region.get_data().id != region_data.id, f'Region GUID {region_data.id} already exists in map'
        assert region.get_data().mesh_range != region_data.mesh_range, f'Region mesh range {region_data.mesh_range} already exists in map'
        assert region.get_data().scid_range != region_data.scid_range, f'Region scid range {region_data.scid_range} already exists in map'


def are_world_levels_compatible(worlds_a: dict[str, Map.Data.World], worlds_b: dict[str, Map.Data.World]) -> bool:
    if len(worlds_a) != len(worlds_b):
        return False
    if worlds_a.keys() != worlds_b.keys():
        return False
    for name, a in worlds_a.items():
        b = worlds_b[name]
        if a.required_level != b.required_level:
            return False
    return True


def handle_multi_world_levels(from_map: Map, to_map: Map, new_region: Region):
    if not to_map.is_multi_world():
        if not from_map.is_multi_world():
            pass  # easy
        else:
            print(f'Note: Imported region is multi-world but target map is not. Removing world levels.')
            rem_region_world_levels(new_region)
    else:
        if not from_map.is_multi_world():
            print(f'Warning: Target map is multi-world but imported region is not! Please add manually.')  # add_region_world_levels is not really working
        else:
            if are_world_levels_compatible(from_map.get_data().worlds, to_map.get_data().worlds):
                pass  # phew
            else:
                print(f'Warning: Both maps are multi-world, but their world levels differ! Good luck sorting that out.')


def import_region(bits: Bits, region_name: str, from_map_name: str, to_map_name: str):
    print(f'Importing region {region_name} from map {from_map_name} into map {to_map_name}')
    assert from_map_name in bits.maps, f'Map {from_map_name} does not exist'
    from_map = bits.maps[from_map_name]
    assert to_map_name in bits.maps, f'Map {to_map_name} does not exist'
    to_map = bits.maps[to_map_name]
    assert region_name not in to_map.get_regions(), f'Region {region_name} already exists in map {to_map_name}'
    old_region = from_map.get_region(region_name)

    # pre-checks - might one day auto-fix instead
    print('Checking for duplicate node guids...')
    check_dupe_node_ids.check_map(to_map)
    check_dupe_node_ids.check_map_vs_region(to_map, old_region)
    check_conflicting_region_ids(to_map, old_region.get_data())

    # copy region directory
    new_region = copy_region_dir(old_region, to_map)

    # convert to NMI if required
    if to_map.get_data().use_node_mesh_index:
        if not new_region.gas_dir.get_subdir('index').has_gas_file('node_mesh_index'):
            convert_region(new_region, NodeMeshGuids(bits.gas_dir))

    # handle multi-world levels
    # handle_multi_world_levels(from_map, to_map, new_region)

    new_region.print()
    print('Importing region done. Recommend to git-commit, then open & save in Siege Editor.')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy import region')
    parser.add_argument('--region', required=True)
    parser.add_argument('--from-map', required=True)
    parser.add_argument('--to-map', required=True)
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits = Bits(args.bits)
    import_region(bits, args.region, args.from_map, args.to_map)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
