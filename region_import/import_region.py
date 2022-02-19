import shutil
import sys
import argparse
import os
import time

from bits.bits import Bits
from bits.map import Map
from bits.region import Region
from region_import.check_dupe_node_ids import check_dupe_node_ids
from region_import.convert_to_node_mesh_index import convert_region, NodeMeshGuids


def copy_region(old_region: Region, to_map: Map) -> Region:
    src = old_region.gas_dir.path
    dst = os.path.join(to_map.gas_dir.path, 'regions', old_region.gas_dir.dir_name)
    shutil.copytree(src, dst)
    time.sleep(0.1)  # shutil...
    to_map.gas_dir.clear_cache()
    return to_map.get_region(old_region.get_name())


def import_region(bits: Bits, region_name: str, from_map_name: str, to_map_name: str):
    print(f'Importing region {region_name} from map {from_map_name} into map {to_map_name}')
    assert from_map_name in bits.maps, f'Map {from_map_name} does not exist'
    from_map = bits.maps[from_map_name]
    assert to_map_name in bits.maps, f'Map {to_map_name} does not exist'
    to_map = bits.maps[to_map_name]
    assert region_name not in to_map.get_regions(), f'Region {region_name} already exists in map {to_map_name}'
    old_region = from_map.get_region(region_name)

    print('Checking for duplicate node guids...')
    check_dupe_node_ids(to_map_name, [from_map_name])

    new_region = copy_region(old_region, to_map)

    if to_map.get_data().use_node_mesh_index:
        if not new_region.gas_dir.get_subdir('index').has_gas_file('node_mesh_index'):
            convert_region(new_region, NodeMeshGuids(bits))

    new_region.print()
    print('Importing region done.')


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
