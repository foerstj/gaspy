# This script generates plants on *existing* regions
import argparse
import math
import os
import random
import sys
from typing import Optional

from bits.bits import Bits
from bits.maps.game_object_data import GameObjectData, Placement, Aspect, Common
from gas.gas import Position, Quaternion
from bits.maps.terrain import Terrain, TerrainNode


class PlantableArea:
    def __init__(self, x_min: float, z_min: float, x_max: float, z_max: float, y: float = 0):
        self.x_min = x_min
        self.z_min = z_min
        self.x_max = x_max
        self.z_max = z_max
        self.y = y

    def size(self) -> float:
        x = self.x_max - self.x_min
        z = self.z_max - self.z_min
        return x*z

    def random_position(self) -> (float, float, float):
        x = random.uniform(self.x_min, self.x_max)
        z = random.uniform(self.z_min, self.z_max)
        y = self.y
        return x, y, z


def load_mesh_info() -> dict[str, PlantableArea]:
    mesh_info = dict()
    with open('input/plantable-areas.txt') as file:
        for line in file:
            line = line.split('#')[0].strip()
            if not line:
                continue
            line_parts = line.split(':')
            assert 1 <= len(line_parts) <= 2
            mesh_name = line_parts[0].strip()
            assert mesh_name not in mesh_info
            mesh_info[mesh_name] = None
            if len(line_parts) != 2:
                continue
            pa_def = line_parts[1]
            pa_def_parts: list = pa_def.split()
            assert len(pa_def_parts) in [4, 5]
            x_min = float(pa_def_parts[0])
            z_min = float(pa_def_parts[1])
            x_max = float(pa_def_parts[2])
            z_max = float(pa_def_parts[3])
            y = float(pa_def_parts[4]) if len(pa_def_parts) == 5 else 0
            mesh_info[mesh_name] = PlantableArea(x_min, z_min, x_max, z_max, y)
    return mesh_info


def load_plantgen_profile_txt(file_path):
    plants_profile = dict()
    with open(file_path) as file:
        for line in file:
            if not line.strip() or line.startswith('#'):
                continue
            line = line.split('#')[0]  # remove comment at end of line
            line_parts = line.split(':')
            assert len(line_parts) == 2, line
            template_name, density_str = line_parts
            assert template_name not in plants_profile, f'duplicate template name {template_name}'
            plants_profile[template_name] = float(density_str)
    return plants_profile


def load_plantgen_profile(name):
    file_name = f'plantgen-{name}.txt'
    for base_path in [os.path.join(Bits.DSLOA_PATH, 'gaspy'), 'input']:
        file_path = os.path.join(base_path, file_name)
        if os.path.isfile(file_path):
            return load_plantgen_profile_txt(file_path)
    raise FileNotFoundError(file_name)


class Plant:
    def __init__(self, template_name=None, position=None, orientation=None, size: float = 1):
        self.template_name: str = template_name
        self.position: Position = position
        self.orientation: float = orientation  # rad within node coords
        self.size: float = size


class NodeMask:
    def __init__(self, section: int = -1, level: int = -1, object: int = -1):
        self.section = section
        self.level = level
        self.object = object

    @classmethod
    def parse(cls, node_mask_str: str) -> 'NodeMask':
        node_mask_3strs = (node_mask_str + '::').split(':')[:3]
        section, level, object = [int(s) if s else -1 for s in node_mask_3strs]
        return NodeMask(section, level, object)

    @classmethod
    def number_matches(cls, mask_number, node_number):
        return mask_number == -1 or mask_number == node_number

    def matches(self, section, level, object) -> bool:
        return self.number_matches(self.section, section) and self.number_matches(self.level, level) and self.number_matches(self.object, object)


def random_position(plantable_area: PlantableArea, node: TerrainNode, bits: Bits) -> Optional[Position]:
    sno = bits.snos.get_sno_by_name(node.mesh_name)
    x = y = z = None
    pos_found = False
    for n in range(16):
        x, y, z = plantable_area.random_position()
        assert sno.is_in_bounding_box_2d(x, z), f'{x}|{y}|{z} not in {sno.bb_str(sno.sno.bounding_box)} bounds of {node.mesh_name}'
        pos_found = sno.is_in_floor_2d(x, z)
        if pos_found:
            y = sno.snap_to_ground(x, z)
            break
    if not pos_found:
        print(f'no pos found for {node.mesh_name}')
        return None
    pos = Position(x, y, z, node.guid)
    return pos


def generate_plants(terrain: Terrain, plants_profile: dict[str, float], include_nodes: list[NodeMask], exclude_nodes: list[NodeMask], bits: Bits) -> list[Plant]:
    mesh_info = load_mesh_info()

    terrain_nodes = terrain.nodes
    if len(include_nodes) > 0:
        terrain_nodes = [node for node in terrain_nodes if any([node_mask.matches(node.section, node.level, node.object) for node_mask in include_nodes])]
    if len(exclude_nodes) > 0:
        terrain_nodes = [node for node in terrain_nodes if not any([node_mask.matches(node.section, node.level, node.object) for node_mask in exclude_nodes])]

    unknown_meshes = set([node.mesh_name for node in terrain_nodes if node.mesh_name not in mesh_info])
    if len(unknown_meshes) > 0:
        print(str(len(unknown_meshes)) + ' unknown meshes:')
        for unknown_mesh in sorted(unknown_meshes):
            print(unknown_mesh)
    plantable_nodes = [node for node in terrain_nodes if node.mesh_name in mesh_info and mesh_info[node.mesh_name] is not None]
    print(f'nodes: {len(terrain.nodes)} total, {len(terrain_nodes)} included, {len(plantable_nodes)} plantable')
    overall_plantable_area_size = 0
    for node in plantable_nodes:
        plantable_area_size = mesh_info[node.mesh_name].size()
        overall_plantable_area_size += plantable_area_size
    print(f'overall plantable area size: {overall_plantable_area_size} m²')

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
            pos = random_position(plantable_area, node, bits)
            if pos is None:
                continue
            orientation = random.uniform(0, math.tau)
            size = random.uniform(0.8, 1.0) if random.choice([True, False]) else random.uniform(1.0, 1.3)
            plant = Plant(template_name, pos, orientation, size)
            plants.append(plant)
    return plants


def plant_gen(map_name: str, region_name: str, plants_profile_name: str, nodes: list[str], exclude_nodes: list[str], override: bool):
    bits = Bits()
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    region.load_data()
    region.load_terrain()
    region.terrain.print()
    nodes = [NodeMask.parse(nm_def) for nm_def in nodes]
    exclude_nodes = [NodeMask.parse(nm_def) for nm_def in exclude_nodes]

    plants_profile = load_plantgen_profile(plants_profile_name)
    plants = generate_plants(region.terrain, plants_profile, nodes, exclude_nodes, bits)
    print(f'{len(plants)} plants generated')

    region.terrain = None  # don't try to re-save the loaded terrain
    if override:
        region.objects.load_objects()
        num_objs_before = len(region.objects.objects_non_interactive)
        region.objects.objects_non_interactive = [go for go in region.objects.objects_non_interactive if go.get_own_value('common', 'dev_instance_text') != '"gaspy plant_gen"']
        print(f'override: removing {num_objs_before - len(region.objects.objects_non_interactive)} of {num_objs_before} plants/nios, {len(region.objects.objects_non_interactive)} remaining')
        region.save()
        region.objects.unload_objects()

    region.objects.generated_objects = [
        GameObjectData(
            plant.template_name,
            placement=Placement(position=plant.position, orientation=Quaternion.rad_to_quat(plant.orientation)),
            aspect=Aspect(scale_multiplier=plant.size),
            common=Common(dev_instance_text='"gaspy plant_gen"')
        ) for plant in plants
    ]

    region.save()
    print('Done!')
    print('Open & save in SE.')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy PlantGen')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('plants_profile')
    parser.add_argument('--nodes', nargs='*', default=[])
    parser.add_argument('--exclude-nodes', nargs='*', default=[])
    parser.add_argument('--override', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    plant_gen(args.map, args.region, args.plants_profile, args.nodes, args.exclude_nodes, args.override)


if __name__ == '__main__':
    main(sys.argv[1:])
