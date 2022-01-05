# This script generates plants on *existing* regions
import math
import random
import sys

from bits import Bits
from gas import Position
from mapgen_terrain import MapgenTerrain


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


mesh_info = {
    't_xxx_flr_04x04-v0': PlantableArea(-2, -2, 2, 2),
    't_xxx_flr_04x04-v1': PlantableArea(-2, -2, 2, 2),
    't_xxx_flr_04x08-v0': PlantableArea(-4, -2, 4, 2),
    't_xxx_flr_08x08-v0': PlantableArea(-4, -4, 4, 4),
    't_xxx_flr_08x08-v1': PlantableArea(-4, -4, 4, 4),

    't_xxx_cnr_h2o_02a-ccav': PlantableArea(-2, -1, 1, 2, 1),
    't_xxx_cnr_h2o_02a-tx-02b-ccav-thick-l': PlantableArea(-2, -4, 4, 4, 1),
    't_xxx_cnr_h2o_02a-tx-02b-ccav-thin-l': PlantableArea(-2, -2, 2, 4, 1),
    't_xxx_cnr_02a-cnvx': PlantableArea(0, -2, 2, 0, -1),
    't_xxx_cnr_02a-tx-02b-ccav-thick-r': PlantableArea(-4, -4, 4, 4, 1),
    't_xxx_cnr_02a-tx-02b-ccav-thin-l': PlantableArea(-2, -4, 2, 4, 1),
    't_xxx_cnr_02a-tx-02b-ccav-thin-r': PlantableArea(-2, -4, 2, 4, 1),
    't_xxx_cnr_02a-tx-02b-cnvx-thin-l': PlantableArea(-2, -4, 2, 4, -1),
    't_xxx_cnr_02b-ccav': PlantableArea(-4, -4, 4, 4, 1),
    't_xxx_cnr_02b-cnvx': PlantableArea(-4, -4, 4, 4, -1),
    't_xxx_cnr_tee-02b-02b-rmp-l': PlantableArea(-3, -4, 4, 4, 2),
    't_xxx_cnr_tee-02b-02b-rmp-r': PlantableArea(-4, -4, 3, 4, 2),
    't_xxx_cnr_tee-02b-04-ccav-l': PlantableArea(-4, -4, 4, 4, 1),

    't_xxx_wal_02a-tx-02b-ccav-thick-r': PlantableArea(-4, -4, 4, 4, 1),
    't_xxx_wal_02a-tx-02b-ccav-thin-r': PlantableArea(-2, -4, 2, 4, 1),
    't_xxx_wal_02b-thick': PlantableArea(-4, -4, 4, 4, 1),
    't_xxx_wal_02b-thin': PlantableArea(-2, -4, 2, 4, 1),

    't_grs02_grs01-08x04-a': PlantableArea(-4, -2, 4, 2),
    't_grs02_grs01-tx-grs02-04x04-b': PlantableArea(-2, -2, 2, 2),
    't_grs02_grs01-tx-grs02-04x04-c': PlantableArea(-2, -2, 2, 2),
    't_grs02_grs01-tx-grs02-08x04-d': PlantableArea(-4, -2, 4, 2),
    't_grs02_grs01-tx-grs02-08x04-e': PlantableArea(-4, -2, 4, 2),
}


class Plant:
    def __init__(self, template_name=None, position=None, orientation=None, size: float = 1):
        self.template_name: str = template_name
        self.position: Position = position
        self.orientation: float = orientation  # rad within node coords
        self.size: float = size


def plant_gen(map_name, region_name):
    bits = Bits()
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    region.load_data()
    region.load_terrain()
    region.terrain.print()

    known_nodes = [node for node in region.terrain.nodes if node.mesh_name in mesh_info]
    print(str(len(known_nodes)) + ' known nodes')
    overall_plantable_area_size = 0
    area_dist = list()
    for node in known_nodes:
        plantable_area_size = mesh_info[node.mesh_name].size()
        overall_plantable_area_size += plantable_area_size
        area_dist.append((overall_plantable_area_size, node))
    print('overall plantable area size: ' + str(overall_plantable_area_size))

    plants = list()
    density = 0.1337  # num plants per square meter
    num_plants = int(overall_plantable_area_size * density)
    print('num plants: ' + str(num_plants))
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
        plant = Plant('flowers_grs_05', Position(x, y, z, node.guid), orientation, size)
        plants.append(plant)

    region.generated_objects_non_interactive = [(plant.template_name, plant.position, MapgenTerrain.rad_to_quat(plant.orientation), plant.size) for plant in plants]
    region.terrain = None  # don't try to re-save the loaded terrain
    region.save()


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    plant_gen(map_name, region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
