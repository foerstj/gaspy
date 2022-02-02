import argparse
import os
import sys

from bits.terrain import Terrain, TerrainNode
from gas.gas import Position
from gas.gas_dir import GasDir
from bits.bits import Bits
from bits.map import Map, Region
from bits.start_positions import StartPositions, StartGroup, StartPos, Camera


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


def create_region(map_name, region_name, node='t_xxx_flr_04x04-v0'):
    bits = Bits()
    m = bits.maps[map_name]
    region: Region = m.create_region(region_name, None)
    region.terrain = Terrain(TerrainNode(None, node))
    region.save()

    # start positions group
    if len(m.get_regions()) == 1 and m.start_positions is None:
        # 1st region, let's add a start pos
        position = Position(0, 0, 0, region.terrain.target_node.guid)
        m.start_positions = StartPositions({
            'default': StartGroup(
                'This is the default group.', False, 0, '', [
                    StartPos(
                        1,
                        position,
                        Camera(0.5, 20, 0, position)
                    )
                ]
            )
        }, 'default')
        m.save()


def delete_region(map_name, region_name):
    bits = Bits()
    m: Map = bits.maps[map_name]
    m.delete_region(region_name)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen')
    parser.add_argument('action', choices=['create-map', 'delete-map', 'create-region', 'delete-region'])
    parser.add_argument('--name', help='name of map or region')
    parser.add_argument('--screen-name', help='screen name for new map')
    parser.add_argument('--map', help='name of the map')
    parser.add_argument('--node', help='mesh name of target node for new region')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def basic_map_action(args):
    if args.action == 'create-map':
        print('creating map: {} "{}"'.format(args.name, args.screen_name))
        create_map(args.name, args.screen_name)
        print('map created')
    elif args.action == 'create-region':
        print('creating region: {} in map {}'.format(args.name, args.map))
        create_region(args.map, args.name, args.node)
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
    basic_map_action(args)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
