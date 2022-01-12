# This script generates plants on *existing* regions
import argparse
import math
import random
import sys

from bits import Bits
from game_object_data import GameObjectData, Placement, Aspect
from gas import Position
from mapgen_terrain import MapgenTerrain
from terrain import Terrain


class PlantableArea:
    def __init__(self, x_min, z_min, x_max, z_max, y=0):
        self.x_min = x_min
        self.z_min = z_min
        self.x_max = x_max
        self.z_max = z_max
        self.y = y

    def size(self) -> float:
        x = self.x_max - self.x_min
        z = self.z_max - self.z_min
        return x*z


def load_mesh_info() -> dict[str, PlantableArea]:
    mesh_info = dict()
    with open('input/plantable-areas.txt') as file:
        for line in file:
            if not line.strip() or line.startswith('#'):
                continue
            line_parts = line.split(':')
            mesh_name = line_parts[0].strip()
            assert mesh_name not in mesh_info
            mesh_info[mesh_name] = None
            if len(line_parts) != 2:
                continue
            pa_def = line_parts[1]
            pa_def_parts: list = pa_def.split()
            assert len(pa_def_parts) in [4, 5]
            x_min = int(pa_def_parts[0])
            z_min = int(pa_def_parts[1])
            x_max = int(pa_def_parts[2])
            z_max = int(pa_def_parts[3])
            y = int(pa_def_parts[4]) if len(pa_def_parts) == 5 else 0
            mesh_info[mesh_name] = PlantableArea(x_min, z_min, x_max, z_max, y)
    return mesh_info


def load_plants_profile(name):
    plants_profile = dict()
    with open('input/plantgen-'+name+'.txt') as file:
        for line in file:
            if not line.strip() or line.startswith('#'):
                continue
            template_name, density_str = line.split(':')
            assert template_name not in plants_profile
            plants_profile[template_name] = float(density_str)
    return plants_profile


class Plant:
    def __init__(self, template_name=None, position=None, orientation=None, size: float = 1):
        self.template_name: str = template_name
        self.position: Position = position
        self.orientation: float = orientation  # rad within node coords
        self.size: float = size


def generate_plants(terrain: Terrain, plants_profile: dict[str, float]) -> list[Plant]:
    mesh_info = load_mesh_info()

    unknown_meshes = set([node.mesh_name for node in terrain.nodes if node.mesh_name not in mesh_info])
    if len(unknown_meshes) > 0:
        print(str(len(unknown_meshes)) + ' unknown meshes! ' + repr(unknown_meshes))
    plantable_nodes = [node for node in terrain.nodes if node.mesh_name in mesh_info and mesh_info[node.mesh_name] is not None]
    print(str(len(plantable_nodes)) + ' plantable nodes')
    overall_plantable_area_size = 0
    for node in plantable_nodes:
        plantable_area_size = mesh_info[node.mesh_name].size()
        overall_plantable_area_size += plantable_area_size
    print('overall plantable area size: ' + str(overall_plantable_area_size))

    plants = list()
    for template_name, density in plants_profile.items():
        num_plants = int(overall_plantable_area_size * density)
        print(template_name + ' density ' + str(density) + '/m² -> num plants: ' + str(num_plants))

        overall_weighted = 0
        weighted_area_dist = list()
        for node in plantable_nodes:
            weight = random.uniform(0, 2)
            weighted = mesh_info[node.mesh_name].size() * weight
            overall_weighted += weighted
            weighted_area_dist.append((overall_weighted, node))

        for i in range(num_plants):
            rand_val = random.uniform(0, overall_weighted)
            node = None
            for max_rand_val, n in weighted_area_dist:
                if max_rand_val > rand_val:
                    node = n
                    break
            plantable_area = mesh_info[node.mesh_name]
            x = random.uniform(plantable_area.x_min, plantable_area.x_max)
            z = random.uniform(plantable_area.z_min, plantable_area.z_max)
            y = plantable_area.y
            orientation = random.uniform(0, math.tau)
            size = random.uniform(0.8, 1.0) if random.choice([True, False]) else random.uniform(1.0, 1.3)
            plant = Plant(template_name, Position(x, y, z, node.guid), orientation, size)
            plants.append(plant)
    return plants


def plant_gen(map_name, region_name, plants_profile_name):
    bits = Bits()
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    region.load_data()
    region.load_terrain()
    region.terrain.print()

    plants_profile = load_plants_profile(plants_profile_name)
    plants = generate_plants(region.terrain, plants_profile)

    region.generated_objects_non_interactive = [
        GameObjectData(
            plant.template_name,
            placement=Placement(position=plant.position, orientation=MapgenTerrain.rad_to_quat(plant.orientation)),
            aspect=Aspect(scale_multiplier=plant.size)
        ) for plant in plants
    ]
    region.terrain = None  # don't try to re-save the loaded terrain
    region.save()
    print('Done!')
    print('Open in SE and snap to ground.')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy PlantGen')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('plants_profile')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    plant_gen(args.map, args.region, args.plants_profile)


if __name__ == '__main__':
    main(sys.argv[1:])
