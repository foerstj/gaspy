# Script to remove the world level subfolders (regular/veteran/elite) in regions' objects dirs
import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region


def rem_region_world_levels(region: Region):
    index_dir = region.gas_dir.get_subdir('index')
    os.rename(os.path.join(index_dir.path, 'regular', 'streamer_node_content_index.gas'), os.path.join(index_dir.path, 'streamer_node_content_index.gas'))
    for wl in ['regular', 'veteran', 'elite']:
        shutil.rmtree(os.path.join(index_dir.path, wl))
    time.sleep(0.1)  # shutil...

    objects_dir = region.gas_dir.get_subdir('objects')
    if objects_dir is None:
        print(f'  {region.get_name()} has no objects dir')
    else:
        for file_name in os.listdir(os.path.join(objects_dir.path, 'regular')):
            os.rename(os.path.join(objects_dir.path, 'regular', file_name), os.path.join(objects_dir.path, file_name))
        for wl in ['regular', 'veteran', 'elite']:
            shutil.rmtree(os.path.join(objects_dir.path, wl))
        time.sleep(0.1)  # shutil...


def rem_map_world_levels(_map: Map):
    for region_name, region in _map.get_regions().items():
        print(region_name)
        rem_region_world_levels(region)
    # remove worlds in main.gas - todo


def remove_world_levels(map_name, region_name=None, bits_path=None):
    bits = Bits(bits_path)
    _map = bits.maps[map_name]
    if region_name is None:
        rem_map_world_levels(_map)
    else:
        rem_region_world_levels(_map.get_region(region_name))


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy remove world levels')
    parser.add_argument('map')
    parser.add_argument('region', default=None, nargs='?')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    remove_world_levels(args.map, args.region, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
