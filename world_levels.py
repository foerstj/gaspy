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
    # remove worlds in main.gas - todo


def add_region_world_levels(region: Region, core_template_names):
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

    for wl, prefix in {'veteran': '2w_', 'elite': '3w_'}.items():
        wl_dir = objects_dir.get_subdir(wl)
        if wl_dir.has_gas_file('actor'):
            actor_file = wl_dir.get_gas_file('actor')
            actor_gas = actor_file.get_gas()
            changed = False
            for section in actor_gas.get_sections():
                template_name, object_id = section.get_t_n_header()
                if template_name not in core_template_names:
                    wl_template_name = f'{prefix}{template_name}'
                    print(f'{template_name} -> {wl_template_name}')
                    section.set_t_n_header(wl_template_name, object_id)
                    changed = True
            if changed:
                actor_file.save()


def add_map_world_levels(_map: Map, bits: Bits):
    for region_name, region in _map.get_regions().items():
        print(region_name)
        add_region_world_levels(region, bits.templates.get_core_template_names())
    # add worlds in main.gas - todo


def world_levels(action, map_name, region_name=None, bits_path=None):
    bits = Bits(bits_path)
    _map = bits.maps[map_name]
    if action == 'rem':
        if region_name is None:
            rem_map_world_levels(_map)
        else:
            rem_region_world_levels(_map.get_region(region_name))
    elif action == 'add':
        if region_name is None:
            add_map_world_levels(_map, bits)
        else:
            core_template_names = bits.templates.get_core_template_names()
            add_region_world_levels(_map.get_region(region_name), core_template_names)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world levels')
    parser.add_argument('action', choices=['rem', 'add'])
    parser.add_argument('map')
    parser.add_argument('region', default=None)
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    world_levels(args.action, args.map, args.region, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
