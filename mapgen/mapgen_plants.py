import math
import random

from perlin_noise import PerlinNoise

from .mapgen_terrain import MapgenTerrain, Plant


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


class PlantDistribution:
    def __init__(self, perlin_offset, perlin_spread, seed_factor, plant_templates, size=None):
        self.perlin_offset = perlin_offset
        self.perlin_spread = perlin_spread
        self.seed_factor = seed_factor  # seeds/m²
        self.plant_templates = plant_templates
        if not size:
            size = (1, 1, 0)
        self.size_from = size[0]
        self.size_to = size[1]
        self.size_perlin = size[2]

    def __str__(self):
        return '{} {} {} {} {} {} {}'.format(self.perlin_offset, self.perlin_spread, self.seed_factor, self.plant_templates, self.size_from, self.size_to, self.size_perlin)


def create_plants_perlin_sub(flat_terrain_2d: MapgenTerrain, plants_profile: PlantDistribution, perlin):
    max_xz = max(flat_terrain_2d.size_x, flat_terrain_2d.size_z)
    size_factor = flat_terrain_2d.size_x * flat_terrain_2d.size_z  # m²
    for _ in range(int(size_factor*plants_profile.seed_factor)):
        x = random.uniform(0, flat_terrain_2d.size_x)
        z = random.uniform(0, flat_terrain_2d.size_z)
        pos = (x, z)
        perlin_value = perlin([x/max_xz, z/max_xz])  # -0.5 .. +0.5
        probability = 0.5+plants_profile.perlin_offset + plants_profile.perlin_spread*perlin_value  # offset 0, spread 3 => -1 .. +2
        probability = min(1, max(0, probability))
        grows = bool(random.uniform(0, 1) < probability)
        if grows:
            template = random.choice(plants_profile.plant_templates)
            orientation = random.uniform(0, math.tau)
            size = random.uniform(plants_profile.size_from, plants_profile.size_to) + perlin_value*2*plants_profile.size_perlin
            flat_terrain_2d.plants.append(Plant(template, pos, orientation, size))


def load_plants_profile(name):
    plants_profile = []
    with open('input/'+name+'.txt') as pf:
        for line in pf:
            if not line.strip() or line.startswith('#'):
                continue
            line_parts = line.split(',')
            (seed_factor, perlin_offset, perlin_spread, plant_templates) = line_parts[:4]
            size = line_parts[4] if len(line_parts) > 4 else None
            perlin_offset = float(perlin_offset)
            perlin_spread = float(perlin_spread)
            seed_factor = float(seed_factor)
            plant_templates = plant_templates.split()
            size = [float(s) for s in size.split()] if size else None
            plants_profile.append(PlantDistribution(perlin_offset, perlin_spread, seed_factor, plant_templates, size))
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
