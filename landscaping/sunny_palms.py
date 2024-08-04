import argparse
import math
import random
import sys

from perlin_noise import PerlinNoise

from bits.bits import Bits
from bits.maps.game_object_data import GameObjectData, Placement, Aspect, Common
from bits.maps.terrain import Terrain, TerrainNode
from gas.molecules import Quaternion, Position
from landscaping.node_mask import NodeMasks
from landscaping.plant_gen import Plant
from mapgen.flat.perlin_plant_profile import load_perlin_plant_profile, PerlinPlantProfile, PerlinPlantDistribution
from sno.sno_handler import SnoHandler
from terrain_layout import TerrainMetaData, NodeMetaData


def random_position(node: TerrainNode, sno: SnoHandler) -> Position or None:
    x = random.uniform(sno.sno.bounding_box.min.x, sno.sno.bounding_box.max.x)
    z = random.uniform(sno.sno.bounding_box.min.z, sno.sno.bounding_box.max.z)
    pos_found = sno.is_in_floor_2d(x, z)
    if not pos_found:
        return None
    y = sno.snap_to_ground(x, z)
    return Position(x, y, z, node.guid)


def generate_plants_sub(terrain: TerrainMetaData, plants_profile: PerlinPlantDistribution, perlin) -> list[Plant]:
    plants = list()
    size_factor = terrain.get_bbs2d_sizes_sqm()  # m²
    num_seeds = int(size_factor * plants_profile.seed_factor)
    print(f'  num seeds: {num_seeds}')
    nodes = list(terrain.nodes.values())
    node_weights = [node.sno.bounding_box_2d_size() for node in nodes]
    random_choices = random.choices(nodes, weights=node_weights, k=num_seeds)
    for nmd in random_choices:
        assert isinstance(nmd, NodeMetaData)
        pos = random_position(nmd.node, nmd.sno)
        if pos is None:
            continue
        assert isinstance(pos, Position)

        abs_pos = nmd.get_external_position(pos)
        if abs_pos is None:
            continue
        perlin_value = perlin([abs_pos.x, abs_pos.z])  # -0.5 .. +0.5
        probability = 0.5 + ((perlin_value + plants_profile.perlin_offset) * plants_profile.perlin_spread)  # offset 0, spread 3 => -1 .. +2
        probability = min(1, max(0, probability))
        grows = bool(random.uniform(0, 1) < probability)
        if grows:
            template_name = random.choice(plants_profile.plant_templates)
            orientation = random.uniform(0, math.tau)
            size = random.uniform(plants_profile.size_from, plants_profile.size_to)  # + perlin_value*2*plants_profile.size_perlin
            plant = Plant(template_name, pos, orientation, size)
            plants.append(plant)
    print(f'  num plants: {len(plants)}')
    return plants


def generate_plants(terrain: Terrain, plants_profile: PerlinPlantProfile, node_masks: NodeMasks, node_bits: Bits):
    octaves = 1/32
    perlin = PerlinNoise(octaves)
    tmd = TerrainMetaData(terrain, node_bits.snos)
    plants = list()
    for pp in plants_profile.plant_distributions:
        print(pp)
        plants_sub = generate_plants_sub(tmd, pp, perlin)
        plants.extend(plants_sub)
    return plants


def sunny_palms(map_name: str, region_name: str, plants_profile_name: str, nodes: list[str], exclude_nodes: list[str], override: bool, bits_path: str, node_bits_path: str):
    bits = Bits(bits_path)
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    region.load_data()
    region.load_terrain()
    region.terrain.print()
    node_masks = NodeMasks(nodes, exclude_nodes)
    plants_profile = load_perlin_plant_profile(plants_profile_name, bits.gas_dir.path)
    assert isinstance(plants_profile, PerlinPlantProfile)
    node_bits = bits if node_bits_path is None else Bits(node_bits_path)

    plants = generate_plants(region.terrain, plants_profile, node_masks, node_bits)
    print(f'{len(plants)} plants generated')

    terrain = region.terrain
    region.terrain = None  # don't try to re-save the loaded terrain
    if override:
        region.objects.load_objects()
        num_objs_before = len(region.objects.objects_non_interactive)
        region.objects.objects_non_interactive = [
            go for go in region.objects.objects_non_interactive
            if go.get_own_value('common', 'dev_instance_text') != '"gaspy sunny-palms"'
               or not node_masks.is_included(terrain.find_node(go.get_own_value('placement', 'position').node_guid))
        ]
        print(f'override: removing {num_objs_before - len(region.objects.objects_non_interactive)} of {num_objs_before} plants/nios, {len(region.objects.objects_non_interactive)} remaining')
        region.save()
        region.objects.unload_objects()

    region.objects.generated_objects = [
        GameObjectData(
            plant.template_name,
            placement=Placement(position=plant.position, orientation=Quaternion.rad_to_quat(plant.orientation)),
            aspect=Aspect(scale_multiplier=plant.size),
            common=Common(dev_instance_text='"gaspy sunny-palms"')
        ) for plant in plants
    ]

    region.save()
    print('Done!')
    print('Open & save in SE.')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy TBD')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('plants_profile')
    parser.add_argument('--nodes', nargs='*', default=[])
    parser.add_argument('--exclude-nodes', nargs='*', default=[])
    parser.add_argument('--override', action='store_true')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--node-bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    sunny_palms(args.map, args.region, args.plants_profile, args.nodes, args.exclude_nodes, args.override, args.bits, args.node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
