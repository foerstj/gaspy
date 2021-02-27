import argparse
import math
import os
import random
import sys

from bits import Bits
from gas import Quaternion
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


class Plant:
    def __init__(self, template_name=None, map_pos=None, orientation=None):
        self.template_name = template_name
        self.map_pos = map_pos
        self.orientation = orientation
        self.node_pos = None


class FlatTerrain2D:
    def __init__(self, size_x=0, size_z=0):
        assert size_x % 4 == 0
        assert size_z % 4 == 0
        self.size_x = size_x
        self.size_z = size_z
        node_size_x = int(size_x / 4)
        node_size_z = int(size_z / 4)
        self.node_size_x = node_size_x
        self.node_size_z = node_size_z
        nodes_2d = [[TerrainNode(None, 't_xxx_flr_04x04-v0', 'grs01') for _ in range(node_size_z)] for _ in range(node_size_x)]
        self.nodes_2d = nodes_2d
        for x in range(node_size_x):
            for z in range(node_size_z):
                node = nodes_2d[x][z]
                if x > 0:
                    nn = nodes_2d[x-1][z]
                    node.connect_doors(2, nn, 4)
                if x < node_size_x-1:
                    nn = nodes_2d[x+1][z]
                    node.connect_doors(4, nn, 2)
                if z > 0:
                    nn = nodes_2d[x][z-1]
                    node.connect_doors(1, nn, 3)
                if z < node_size_z-1:
                    nn = nodes_2d[x][z+1]
                    node.connect_doors(3, nn, 1)
        self.plants: list[Plant] = []

    def make_terrain(self):
        terrain = Terrain()
        for x in range(self.node_size_x):
            for z in range(self.node_size_z):
                node = self.nodes_2d[x][z]
                node.guid = terrain.new_node_guid()
                terrain.nodes.append(node)
        i_tn_x = int(self.node_size_x / 2)
        i_tn_z = int(self.node_size_z / 2)
        target_node = self.nodes_2d[i_tn_x][i_tn_z]
        terrain.target_node = target_node
        return terrain

    def map_pos_to_node_pos(self, map_pos_x, map_pos_z):
        xn = int(map_pos_x / 4)
        zn = int(map_pos_z / 4)
        node = self.nodes_2d[xn][zn]
        nx = map_pos_x % 4 - 2
        nz = map_pos_z % 4 - 2
        node_pos = Position(nx, 0, nz, node.guid)
        return node_pos

    @staticmethod
    def rad_to_quat(rad):
        y = math.sin(rad / 2)
        w = math.cos(rad / 2)
        return Quaternion(0, y, 0, w)

    def make_non_interactive_objects(self):
        for plant in self.plants:
            (map_pos_x, map_pos_z) = plant.map_pos
            node_pos = self.map_pos_to_node_pos(map_pos_x, map_pos_z)
            plant.node_pos = node_pos
        objects_non_interactive = [(plant.template_name, plant.node_pos, self.rad_to_quat(plant.orientation)) for plant in self.plants]
        return objects_non_interactive


def create_plants(flat_terrain_2d: FlatTerrain2D):
    template_names = [
        'bush_grs_03', 'bush_grs_04', 'bush_grs_05', 'bush_grs_08', 'cornstalk_glb_grn_01', 'fern_grs_01', 'flowers_grs_04', 'flowers_grs_05', 'flowers_grs_06', 'flowers_grs_08', 'flowers_grs_blue',
        'foliage_grs_01', 'grass_grs_07', 'groundcover_grs_03', 'mushroom_glb_10', 'mushrooms_cav_06'
    ]
    size = math.sqrt(flat_terrain_2d.size_x*flat_terrain_2d.size_x + flat_terrain_2d.size_z*flat_terrain_2d.size_z)
    num_circles = max(3, random.randint(int(size/4), int(size)))
    map_center_x = flat_terrain_2d.size_x / 2
    map_center_z = flat_terrain_2d.size_z / 2
    print(str(num_circles) + ' circles')
    for i_circle in range(num_circles):
        r = random.uniform(0, size / 2)
        num_plants = max(3, random.randint(0, int(r*math.tau)))
        template_name = random.choice(template_names)
        orientation = random.uniform(0, math.tau)
        print('circle ' + str(i_circle) + ': radius ' + str(r) + ', ' + str(num_plants) + ' plants')
        for i_plant in range(num_plants):
            a = math.tau / num_plants * i_plant
            x = math.sin(a)
            z = math.cos(a)
            map_x = map_center_x + r*x
            map_z = map_center_z + r*z
            if map_x < 0 or map_x > flat_terrain_2d.size_x or map_z < 0 or map_z > flat_terrain_2d.size_z:
                continue
            flat_terrain_2d.plants.append(Plant(template_name, (map_x, map_z), orientation+a))


def create_region(map_name, region_name, size='4x4'):
    bits = Bits()
    m = bits.maps[map_name]
    region: Region = m.create_region(region_name, None)
    size_x, size_z = [int(s) for s in size.split('x')]
    flat_terrain_2d = FlatTerrain2D(size_x, size_z)
    terrain = flat_terrain_2d.make_terrain()
    region.terrain = terrain
    create_plants(flat_terrain_2d)
    region.objects_non_interactive = flat_terrain_2d.make_non_interactive_objects()
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
