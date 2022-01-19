import argparse
import os
import shutil
import sys

from bits.bits import Bits


def rem_world_levels(map_name, bits_dir=None):
    bits = Bits(bits_dir)
    _map = bits.maps[map_name]
    for region_name, region in _map.get_regions().items():
        print(region_name)

        index_dir = region.gas_dir.get_subdir('index')
        os.rename(os.path.join(index_dir.path, 'regular', 'streamer_node_content_index.gas'), os.path.join(index_dir.path, 'streamer_node_content_index.gas'))
        for wl in ['regular', 'veteran', 'elite']:
            shutil.rmtree(os.path.join(index_dir.path, wl))

        objects_dir = region.gas_dir.get_subdir('objects')
        for file_name in os.listdir(os.path.join(objects_dir.path, 'regular')):
            os.rename(os.path.join(objects_dir.path, 'regular', file_name), os.path.join(objects_dir.path, file_name))
        for wl in ['regular', 'veteran', 'elite']:
            shutil.rmtree(os.path.join(objects_dir.path, wl))


def add_world_levels(map_name, bits_dir=None):
    bits = Bits(bits_dir)
    _map = bits.maps[map_name]
    for region_name, region in _map.get_regions().items():
        print(region_name)

        index_dir = region.gas_dir.get_subdir('index')
        for wl in ['regular', 'veteran', 'elite']:
            os.mkdir(os.path.join(index_dir.path, wl))
            shutil.copy(os.path.join(index_dir.path, 'streamer_node_content_index.gas'), os.path.join(index_dir.path, wl, 'streamer_node_content_index.gas'))
        os.remove(os.path.join(index_dir.path, 'streamer_node_content_index.gas'))

        objects_dir = region.gas_dir.get_subdir('objects')
        for wl in ['regular', 'veteran', 'elite']:
            os.mkdir(os.path.join(objects_dir.path, wl))
            for file_name in os.listdir(objects_dir.path):
                if not file_name.endswith('.gas'):
                    continue
                shutil.copy(os.path.join(objects_dir.path, file_name), os.path.join(objects_dir.path, wl, file_name))
        for file_name in os.listdir(objects_dir.path):
            if not file_name.endswith('.gas'):
                continue
            os.remove(os.path.join(objects_dir.path, file_name))


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
