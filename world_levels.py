# Script to add/remove the world level subfolders (regular/veteran/elite) in regions' objects dirs
import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits
from bits.map import Map
from bits.region import Region


def rem_region_world_levels(region: Region):
    index_dir = region.gas_dir.get_subdir('index')
    os.rename(os.path.join(index_dir.path, 'regular', 'streamer_node_content_index.gas'), os.path.join(index_dir.path, 'streamer_node_content_index.gas'))
    for wl in ['regular', 'veteran', 'elite']:
        shutil.rmtree(os.path.join(index_dir.path, wl))
        time.sleep(0.1)  # shutil...

    objects_dir = region.gas_dir.get_subdir('objects')
    for file_name in os.listdir(os.path.join(objects_dir.path, 'regular')):
        os.rename(os.path.join(objects_dir.path, 'regular', file_name), os.path.join(objects_dir.path, file_name))
    for wl in ['regular', 'veteran', 'elite']:
        shutil.rmtree(os.path.join(objects_dir.path, wl))
        time.sleep(0.1)  # shutil...


def rem_map_world_levels(_map: Map):
    for region_name, region in _map.get_regions().items():
        print(region_name)
        rem_region_world_levels(region)


def rem_world_levels(map_name, bits_dir=None):
    bits = Bits(bits_dir)
    _map = bits.maps[map_name]
    rem_map_world_levels(_map)


def add_region_world_levels(region: Region):
    # yeah this currently simply copies the existing objects without adapting them at all. just poc

    index_dir = region.gas_dir.get_subdir('index')
    for wl in ['regular', 'veteran', 'elite']:
        os.mkdir(os.path.join(index_dir.path, wl))
        shutil.copy(os.path.join(index_dir.path, 'streamer_node_content_index.gas'), os.path.join(index_dir.path, wl, 'streamer_node_content_index.gas'))
        time.sleep(0.1)  # shutil...
    os.remove(os.path.join(index_dir.path, 'streamer_node_content_index.gas'))

    objects_dir = region.gas_dir.get_subdir('objects')
    for wl in ['regular', 'veteran', 'elite']:
        os.mkdir(os.path.join(objects_dir.path, wl))
        for file_name in os.listdir(objects_dir.path):
            if not file_name.endswith('.gas'):
                continue
            shutil.copy(os.path.join(objects_dir.path, file_name), os.path.join(objects_dir.path, wl, file_name))
            time.sleep(0.1)  # shutil...
    for file_name in os.listdir(objects_dir.path):
        if not file_name.endswith('.gas'):
            continue
        os.remove(os.path.join(objects_dir.path, file_name))


def add_map_world_levels(_map: Map):
    for region_name, region in _map.get_regions().items():
        print(region_name)
        add_region_world_levels(region)


def add_world_levels(map_name, bits_dir=None):
    bits = Bits(bits_dir)
    _map = bits.maps[map_name]
    add_map_world_levels(_map)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world levels')
    parser.add_argument('action', choices=['rem', 'add'])
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    if args.action == 'rem':
        rem_world_levels(args.map, args.bits)
    elif args.action == 'add':
        add_world_levels(args.map, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
