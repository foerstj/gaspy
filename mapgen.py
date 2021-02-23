import argparse
import os
import sys

from bits import Bits
from gas import Gas, Section, Attribute, Hex
from gas_dir import GasDir
from map import Map, Region
from terrain import Terrain, TerrainNode


def create_map(name, screen_name):
    bits = Bits()
    assert name not in bits.maps
    m = bits.maps[name] = Map(GasDir(os.path.join(bits.gas_dir.path, 'world', 'maps', name)), bits)
    data = Map.Data(name, screen_name)
    data.dev_only = False
    data.timeofday = '0h0m'
    data.use_node_mesh_index = True
    data.use_player_journal = False
    data.camera.azimuth = 70.0
    data.camera.distance = 13.0
    data.camera.position = '0,0,0,0x0'
    m.data = data
    m.save()


def delete_map(name):
    bits = Bits()
    m = bits.maps[name]
    m.delete()


def create_region(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]
    region: Region = m.create_region(region_name, None)
    terrain = Terrain()
    target_node = TerrainNode(terrain.new_node_guid(), 't_xxx_flr_04x04-v0', 'grs01')
    terrain.nodes.append(target_node)
    terrain.target_node = target_node
    region.terrain = terrain
    region.save()

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
            Attribute('position', '0,0,0,'+str(target_node.guid))
        ])
    ]))
    info_dir.save()


def delete_region(map_name, region_name):
    bits = Bits()
    m: Map = bits.maps[map_name]
    m.delete_region(region_name)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen')
    parser.add_argument('action', choices=['create-map', 'delete-map', 'create-region', 'delete-region'])
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
    elif args.action == 'delete-region':
        print('deleting region: {} in map {}'.format(args.name, args.map))
        delete_region(args.map, args.name)
        print('region deleted')
    else:
        assert False, 'unexpected action ' + args.action


def main(argv):
    args = parse_args(argv)
    mapgen(args)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
