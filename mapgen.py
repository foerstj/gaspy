import argparse
import math
import os
import random
import sys

from perlin_noise import PerlinNoise

from bits import Bits
from gas import Hex
from gas_dir import GasDir
from map import Map, Region
from mapgen_terrain import MapgenTerrain, MapgenTerrainFloor, MapgenTerrainDunes, Plant
from region import DirectionalLight
from start_positions import StartPositions, StartGroup, StartPos, Camera


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


def create_plants_fairy_circles(flat_terrain_2d: MapgenTerrain):
    template_names = [
        'bush_grs_04', 'bush_grs_05', 'bush_grs_button_01', 'cornstalk_glb_grn_01', 'fern_grs_01', 'flowers_grs_04', 'flowers_grs_05', 'flowers_grs_06', 'flowers_grs_08', 'flowers_grs_blue',
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


def create_plant_random(flat_terrain_2d: MapgenTerrain, templates):
    template = random.choice(templates)
    orientation = random.uniform(0, math.tau)
    x = random.uniform(0, flat_terrain_2d.size_x)
    z = random.uniform(0, flat_terrain_2d.size_z)
    flat_terrain_2d.plants.append(Plant(template, (x, z), orientation))


def create_plants_random(flat_terrain_2d: MapgenTerrain):
    tree_templates = ['tree_grs_deciduous_{:02}'.format(i+1) for i in range(24)]
    bush_templates = ['bush_des_{:02}'.format(i+1) for i in range(6)] + ['bush_grs_{:02}'.format(i+1) for i in range(2, 9)]
    rock_templates = ['rock_grs_{:02}'.format(i+1) for i in range(8)]
    rock_templates.remove('rock_grs_04')
    num_trees = 40
    num_bushes = 70
    num_rocks = 60
    for _ in range(num_trees):
        create_plant_random(flat_terrain_2d, tree_templates)
    for _ in range(num_bushes):
        create_plant_random(flat_terrain_2d, bush_templates)
    for _ in range(num_rocks):
        create_plant_random(flat_terrain_2d, rock_templates)


def create_plants_perlin_sub(flat_terrain_2d: MapgenTerrain, plants_profile, perlin):
    (perlin_offset, perlin_spread, seed_factor, plant_templates) = plants_profile
    max_xz = max(flat_terrain_2d.size_x, flat_terrain_2d.size_z)
    size_factor = flat_terrain_2d.size_x/4 * flat_terrain_2d.size_z/4
    for _ in range(int(size_factor*seed_factor)):
        x = random.uniform(0, flat_terrain_2d.size_x)
        z = random.uniform(0, flat_terrain_2d.size_z)
        pos = (x, z)
        noise = perlin([x/max_xz, z/max_xz])  # -0.5 .. +0.5
        probability = 0.5+perlin_offset + perlin_spread*noise  # offset 0, spread 3 => -1 .. +2
        probability = min(1, max(0, probability))
        grows = bool(random.uniform(0, 1) < probability)
        if grows:
            template = random.choice(plant_templates)
            orientation = random.uniform(0, math.tau)
            flat_terrain_2d.plants.append(Plant(template, pos, orientation))


def load_plants_profile(name):
    plants_profile = []
    with open('input/'+name+'.txt') as pf:
        for line in pf:
            if not line or line.startswith('#'):
                continue
            (perlin_offset, perlin_spread, seed_factor, plant_templates) = line.split(',')
            perlin_offset = float(perlin_offset)
            perlin_spread = float(perlin_spread)
            seed_factor = float(seed_factor)
            plant_templates = plant_templates.split()
            plants_profile.append((perlin_offset, perlin_spread, seed_factor, plant_templates))
    return plants_profile


def create_plants_perlin(flat_terrain_2d: MapgenTerrain, plants_profile):
    octaves = math.sqrt(max(flat_terrain_2d.size_x, flat_terrain_2d.size_z) / 2)
    print('perlin octaves: ' + str(octaves))
    perlin = PerlinNoise(octaves)
    for pp in plants_profile:
        print(pp)
        create_plants_perlin_sub(flat_terrain_2d, pp, perlin)


def create_plants(flat_terrain_2d: MapgenTerrain, plants_arg: str):
    if plants_arg == 'fairy-circles':
        create_plants_fairy_circles(flat_terrain_2d)
    elif plants_arg == 'random':
        create_plants_random(flat_terrain_2d)
    elif plants_arg == 'perlin' or plants_arg.startswith('perlin:'):
        if plants_arg == 'perlin':
            profile_name = 'perlin-grs'
        else:
            profile_name = plants_arg.split(':', 1)[1]
        create_plants_perlin(flat_terrain_2d, load_plants_profile(profile_name))
    else:
        assert not plants_arg, plants_arg


def create_region(map_name, region_name, size='4x4', terrain_type='floor', plants=False):
    bits = Bits()
    m = bits.maps[map_name]
    region: Region = m.create_region(region_name, None)
    size_x, size_z = [int(s) for s in size.split('x')]
    flat_terrain_2d = MapgenTerrainFloor(size_x, size_z) if terrain_type == 'floor' else MapgenTerrainDunes(size_x, size_z)
    terrain = flat_terrain_2d.make_terrain()
    region.terrain = terrain
    if plants:
        assert isinstance(plants, str)
        create_plants(flat_terrain_2d, plants)
        region.objects_non_interactive = flat_terrain_2d.make_non_interactive_objects()
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
