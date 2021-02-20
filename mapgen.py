import argparse
import os
import sys

from bits import Bits
from gas import Gas, Section, Attribute
from gas_dir import GasDir


def create_map(name, screen_name):
    bits = Bits()
    # assert name not in bits.maps
    map_dir = GasDir(os.path.join(bits.gas_dir.path, 'world', 'maps', name), {
        'regions': {},
        'main': Gas([
            Section('t:map,n:map', [
                Attribute('screen_name', screen_name),
                Attribute('dev_only', 'false', 'b'),
                Attribute('timeofday', '0h0m'),
                Attribute('use_node_mesh_index', 'true', 'b'),
                Attribute('use_player_journal', 'false', 'b'),
                Section('camera', [
                    Attribute('azimuth', '70', 'f'),
                    Attribute('distance', '13', 'f'),
                    Attribute('position', '0,0,0,0x0')
                ])
            ])
        ])
    })
    map_dir.save()


def create_region(map_name, region_name):
    bits = Bits()
    map = bits.maps[map_name]
    # assert region_name not in map.get_regions()
    target_node_id = '0x3ce49755'
    target_node_id_upper = '0x3CE49755'
    target_node_mesh = '0x001006AA'  # generic floor 8x8 v0
    region_id = '0x00000001'
    region_dir = GasDir(os.path.join(map.gas_dir.path, 'regions', region_name), {
        'index': {
            'streamer_node_index': Gas([
                Section('streamer_node_index', [
                    Attribute('*', target_node_id_upper, 'x')
                ])
            ])
        },
        'terrain_nodes': {
            'nodes': Gas([
                Section('t:terrain_nodes,n:siege_node_list', [
                    Attribute('targetnode', target_node_id_upper, 'x'),
                    Section('t:snode,n:'+target_node_id, [
                        Attribute('guid', target_node_id_upper, 'x'),
                        Attribute('mesh_guid', target_node_mesh, 'x'),
                        Attribute('texsetabbr', 'grs01')
                    ])
                ])
            ])
        },
        'main': Gas([
            Section('t:region,n:region', [
                Attribute('guid', region_id, 'x'),
                Attribute('mesh_range', region_id, 'x'),
                Attribute('scid_range', region_id, 'x')
            ])
        ])
    })
    region_dir.save()
    # start positions group
    if 'info' in map.gas_dir.subdirs:
        info_dir = map.gas_dir.get_subdirs()['info']
        start_positions = info_dir.get_gas_files()['start_positions.gas'].get_gas().items[0]
    else:
        start_positions = Section('start_positions')
        info_dir = GasDir(os.path.join(map.gas_dir.path, 'info'), {
            'start_positions': Gas([
                start_positions
            ])
        })
    start_positions.items.append(Section('t:start_group,n:'+region_name, [
        Attribute('default', 'true' if len(start_positions.items) == 0 else 'false', 'b'),
        Attribute('id', str(len(start_positions.items)+1), 'i'),
        Section('start_position', [
            Attribute('id', '1', 'i'),
            Attribute('position', '0,0,0,'+target_node_id_upper)
            # camera block
        ])
    ]))
    info_dir.save()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen')
    parser.add_argument('--create-map', action='store_true')
    parser.add_argument('--name')
    parser.add_argument('--screen-name')
    parser.add_argument('--create-region', action='store_true')
    parser.add_argument('--map')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def mapgen(args):
    if args.create_map:
        print('creating map: {} "{}"'.format(args.name, args.screen_name))
        create_map(args.name, args.screen_name)
        print('map created successfully')
    elif args.create_region:
        print('creating region: {} in map {}'.format(args.name, args.map))
        create_region(args.map, args.name)
        print('region created successfully')
    else:
        print('dunno what 2 do')


def main(argv):
    args = parse_args(argv)
    mapgen(args)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
