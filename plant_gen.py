# This script generates plants on *existing* regions
import math
import random
import sys

from bits import Bits
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

    def size(self):
        x = self.x_max - self.x_min
        z = self.z_max - self.z_min
        return x*z


def load_mesh_info():
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
    area_dist = list()
    for node in plantable_nodes:
        plantable_area_size = mesh_info[node.mesh_name].size()
        overall_plantable_area_size += plantable_area_size
        area_dist.append((overall_plantable_area_size, node))
    print('overall plantable area size: ' + str(overall_plantable_area_size))

    plants = list()
    for template_name, density in plants_profile.items():
        num_plants = int(overall_plantable_area_size * density)
        print(template_name + ' density ' + str(density) + '/m² -> num plants: ' + str(num_plants))
        for i in range(num_plants):
            rand_val = random.uniform(0, overall_plantable_area_size)
            node = None
            for max_rand_val, n in area_dist:
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


def plant_gen(map_name, region_name):
    bits = Bits()
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    region.load_data()
    region.load_terrain()
    region.terrain.print()

    plants = generate_plants(region.terrain, {'flowers_grs_04': 0.07, 'flowers_grs_05': 0.01, 'flowers_grs_06': 0.07})

    region.generated_objects_non_interactive = [(plant.template_name, plant.position, MapgenTerrain.rad_to_quat(plant.orientation), plant.size) for plant in plants]
    region.terrain = None  # don't try to re-save the loaded terrain
    region.save()
    print('Done!')
    print('Open in SE and snap to ground.')


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    plant_gen(map_name, region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
