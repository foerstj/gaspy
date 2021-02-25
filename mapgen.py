import argparse
import os
import sys

from bits import Bits
from gas_dir import GasDir
from map import Map, Region
from start_positions import StartPositions, StartGroup, StartPos, Position, Camera
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


def create_terrain(size=1):
    terrain = Terrain()
    nodes_2d = [[TerrainNode(terrain.new_node_guid(), 't_xxx_flr_04x04-v0', 'grs01') for _ in range(size)] for _ in range(size)]
    for x in range(size):
        for z in range(size):
            node = nodes_2d[x][z]
            if x > 0:
                nn = nodes_2d[x-1][z]
                node.connect_doors(2, nn, 4)
            if x < size-1:
                nn = nodes_2d[x+1][z]
                node.connect_doors(4, nn, 2)
            if z > 0:
                nn = nodes_2d[x][z-1]
                node.connect_doors(1, nn, 3)
            if z < size-1:
                nn = nodes_2d[x][z+1]
                node.connect_doors(3, nn, 1)
    i2d_target_node = int(size/2)
    target_node = nodes_2d[i2d_target_node][i2d_target_node]
    for x in range(size):
        terrain.nodes.extend(nodes_2d[x])
    terrain.target_node = target_node
    return terrain


def create_plants(terrain: Terrain):
    # just put a plant right at the center of the target node
    target_node = terrain.target_node
    template_name = 'flowers_grs_05'  # iris violet
    plants = [
        (template_name, Position(0, 0, 0, target_node.guid))
    ]
    return plants


def create_region(map_name, region_name, size=1):
    bits = Bits()
    m = bits.maps[map_name]
    region: Region = m.create_region(region_name, None)
    terrain = create_terrain(size)
    region.terrain = terrain
    plants = create_plants(terrain)
    region.objects_non_interactive = plants
    region.save()

    # start positions group
    if len(m.get_regions()) == 1 and m.start_positions is None:
        # 1st region, let's add a start pos
        m.start_positions = StartPositions({
            'default': StartGroup(
                'This is the default group.', False, 0, '', [
                    StartPos(
                        1,
                        Position(0, 0, 0, terrain.target_node.guid),
                        Camera(0.5, 20, 0, Position(0, 0, 0, terrain.target_node.guid))
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
    parser.add_argument('--name')
    parser.add_argument('--screen-name')
    parser.add_argument('--map')
    parser.add_argument('--size', type=int, default=1)
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
        create_region(args.map, args.name, args.size)
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
