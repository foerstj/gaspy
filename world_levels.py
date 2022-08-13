# Script to add/remove the world level subfolders (regular/veteran/elite) in regions' objects dirs
import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits
from bits.map import Map
from bits.region import Region
from gas.gas_dir import GasDir


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


def copy_wl_files(region: Region):
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


def adapt_file_templates(wl_dir: GasDir, wl_prefix: str, file_name: str, static_template_names: list[str]):
    if wl_dir.has_gas_file(file_name):
        objs_gas_file = wl_dir.get_gas_file(file_name)
        objs_gas = objs_gas_file.get_gas()
        changed = False
        for section in objs_gas.get_sections():
            template_name, object_id = section.get_t_n_header()
            if template_name not in static_template_names:
                wl_template_name = f'{wl_prefix}{template_name}'
                section.set_t_n_header(wl_template_name, object_id)
                changed = True
        if changed:
            objs_gas_file.save()


def adapt_templates(region: Region, static_template_names: dict[str, list[str]]):
    objects_dir = region.gas_dir.get_subdir('objects')
    for wl, prefix in {'veteran': '2W_', 'elite': '3W_'}.items():
        wl_dir = objects_dir.get_subdir(wl)
        adapt_file_templates(wl_dir, prefix, 'actor', static_template_names['core'])
        adapt_file_templates(wl_dir, prefix, 'container', static_template_names['core'] + static_template_names['decorative_containers'])


def do_add_region_world_levels(region: Region, static_template_names: dict[str, list[str]]):
    copy_wl_files(region)
    adapt_templates(region, static_template_names)


def get_static_templates_names(bits: Bits) -> dict[str, list[str]]:
    core_template_names = bits.templates.get_core_template_names()
    decorative_container_template_names = bits.templates.get_decorative_container_template_names()
    return {'core': core_template_names, 'decorative_containers': decorative_container_template_names}


def add_region_world_levels(region: Region, bits: Bits):
    static_template_names = get_static_templates_names(bits)
    do_add_region_world_levels(region, static_template_names)


def add_map_world_levels(_map: Map, bits: Bits):
    static_template_names = get_static_templates_names(bits)
    for region_name, region in _map.get_regions().items():
        print(region_name)
        do_add_region_world_levels(region, static_template_names)
    # add worlds in main.gas - todo


def world_levels(action, map_name, region_name=None, bits_path=None):
    bits = Bits(bits_path)
    _map = bits.maps[map_name]
    if action == 'rem' or action == 'rem+add':
        if region_name is None:
            rem_map_world_levels(_map)
        else:
            rem_region_world_levels(_map.get_region(region_name))
    if action == 'add' or action == 'rem+add':
        if region_name is None:
            add_map_world_levels(_map, bits)
        else:
            add_region_world_levels(_map.get_region(region_name), bits)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world levels')
    parser.add_argument('action', choices=['rem', 'add', 'rem+add'])
    parser.add_argument('map')
    parser.add_argument('region', default=None, nargs='?')
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
