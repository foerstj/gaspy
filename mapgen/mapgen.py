import argparse
import math
import os
import sys

from bits.bits import Bits
from gas.gas import Hex
from gas.gas_dir import GasDir
from bits.map import Map, Region
from mapgen_plants import create_plants
from mapgen_terrain import MapgenTerrainFloor, MapgenTerrainDunes
from bits.region import DirectionalLight
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


def create_region(map_name, region_name, size='4x4', terrain_type='floor', plants=False):
    bits = Bits()
    m = bits.maps[map_name]
    region: Region = m.create_region(region_name, None)
    size_x, size_z = [int(s) for s in size.split('x')]
    if terrain_type == 'floor':
        flat_terrain_2d = MapgenTerrainFloor(size_x, size_z)
    elif terrain_type == 'dunes':
        flat_terrain_2d = MapgenTerrainDunes(size_x, size_z)
    else:
        assert False, 'unknown terrain type'
    terrain = flat_terrain_2d.make_terrain()
    region.terrain = terrain
    if plants:
        assert isinstance(plants, str)
        create_plants(flat_terrain_2d, plants)
        region.generated_objects_non_interactive = flat_terrain_2d.make_non_interactive_objects()
    region.lights = []
    region.lights.append(DirectionalLight(None, Hex(0xffffffcc), True, 1, True, True, (0, math.cos(math.tau/8), math.sin(math.tau/8))))
    region.lights.append(DirectionalLight(None, Hex(0xffccccff), False, 0.7, False, False, (0, math.cos(-math.tau/8), math.sin(-math.tau/8))))
    region.save()

    # start positions group
    if len(m.get_regions()) == 1 and m.start_positions is None:
        # 1st region, let's add a start pos
        map_center_x = flat_terrain_2d.size_x / 2
        map_center_z = flat_terrain_2d.size_z / 2
        position = flat_terrain_2d.map_pos_to_node_pos(map_center_x, map_center_z)
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
    parser.add_argument('--name')
    parser.add_argument('--screen-name')
    parser.add_argument('--map')
    parser.add_argument('--size')
    parser.add_argument('--terrain', choices=['floor', 'dunes'], default='floor')
    parser.add_argument('--plants', default=False)
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
        create_region(args.map, args.name, args.size, args.terrain, args.plants)
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
