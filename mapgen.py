import argparse
import os
import string
import sys
import random

from bits import Bits
from gas import Gas, Section, Attribute, Hex
from gas_dir import GasDir


def create_map(name, screen_name):
    bits = Bits()
    # assert name not in bits.maps
    map_dir = GasDir(os.path.join(bits.gas_dir.path, 'world', 'maps', name), {
        'regions': {},
        'main': Gas([
            Section('t:map,n:map', [
                Attribute('screen_name', screen_name),
                Attribute('dev_only', False),
                Attribute('timeofday', '0h0m'),
                Attribute('use_node_mesh_index', True),
                Attribute('use_player_journal', False),
                Section('camera', [
                    Attribute('azimuth', float(70)),
                    Attribute('distance', float(13)),
                    Attribute('position', '0,0,0,0x0')
                ])
            ])
        ])
    })
    map_dir.save()


def delete_map(name):
    bits = Bits()
    m = bits.maps[name]
    m.delete()


def random_hex(length=8):
    return '0x' + ''.join([random.choice(string.hexdigits) for _ in range(length)])


def create_region(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]
    # assert region_name not in m.get_regions()
    region_id = Hex(1)
    target_node_id = Hex.parse(random_hex())
    target_node_mesh = 't_xxx_flr_04x04-v0'
    mesh_guid = Hex.parse('0x{:03X}006a5'.format(region_id))
    region_dir = GasDir(os.path.join(m.gas_dir.path, 'regions', region_name), {
        'editor': {
            'hotpoints': Gas([
                Section('hotpoints', [
                    Section('t:hotpoint_directional,n:'+str(Hex(1)), [
                        Attribute('direction', '1,0,0'),
                        Attribute('id', Hex(1))
                    ])
                ])
            ])
        },
        'index': {
            'node_mesh_index': Gas([
                Section('node_mesh_index', [
                    Attribute(str(mesh_guid), target_node_mesh)
                ])
            ]),
            'streamer_node_index': Gas([
                Section('streamer_node_index', [
                    Attribute('*', target_node_id)
                ])
            ])
        },
        'terrain_nodes': {
            'nodes': Gas([
                Section('t:terrain_nodes,n:siege_node_list', [
                    Attribute('targetnode', target_node_id),
                    Section('t:snode,n:'+str(target_node_id), [
                        Attribute('guid', target_node_id),
                        Attribute('mesh_guid', mesh_guid),
                        Attribute('texsetabbr', 'grs01')
                    ])
                ])
            ])
        },
        'main': Gas([
            Section('t:region,n:region', [
                Attribute('guid', region_id),
                Attribute('mesh_range', region_id),
                Attribute('scid_range', region_id)
            ])
        ])
    })
    region_dir.save()
    # start positions group
    if 'info' in m.gas_dir.subdirs:
        info_dir = m.gas_dir.get_subdirs()['info']
        start_positions = info_dir.get_gas_files()['start_positions.gas'].get_gas().items[0]
    else:
        start_positions = Section('start_positions')
        info_dir = GasDir(os.path.join(m.gas_dir.path, 'info'), {
            'start_positions': Gas([
                start_positions
            ])
        })
    start_positions.items.append(Section('t:start_group,n:'+region_name, [
        Attribute('default', len(start_positions.items) == 0),
        Attribute('dev_only', False),
        Attribute('id', len(start_positions.items)+1),
        Section('start_position', [
            Attribute('id', 1),
            Attribute('position', '0,0,0,'+str(target_node_id))
        ])
    ]))
    info_dir.save()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen')
    parser.add_argument('action', choices=['create-map', 'delete-map', 'create-region'])
    parser.add_argument('--name')
    parser.add_argument('--screen-name')
    parser.add_argument('--map')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def mapgen(args):
    if args.action == 'create-map':
        print('creating map: {} "{}"'.format(args.name, args.screen_name))
        create_map(args.name, args.screen_name)
        print('map created')
    elif args.action == 'create-region':
        print('creating region: {} in map {}'.format(args.name, args.map))
        create_region(args.map, args.name)
        print('region created')
    elif args.action == 'delete-map':
        print('deleting map: {}'.format(args.name))
        delete_map(args.name)
        print('map deleted')
    else:
        assert False, 'unexpected action ' + args.action


def main(argv):
    args = parse_args(argv)
    mapgen(args)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
