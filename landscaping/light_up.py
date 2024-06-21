import argparse
import random
import sys

from bits.bits import Bits
from bits.maps.light import PointLight, PosDir
from bits.maps.terrain import Terrain, TerrainNode
from landscaping.node_mask import NodeMasks


def random_position(node: TerrainNode, bits: Bits) -> PosDir or None:
    sno = bits.snos.get_sno_by_name(node.mesh_name)
    x = random.uniform(sno.sno.bounding_box.min.x, sno.sno.bounding_box.max.x)
    z = random.uniform(sno.sno.bounding_box.min.z, sno.sno.bounding_box.max.z)
    pos_found = sno.is_in_floor_2d(x, z)
    if not pos_found:
        return None
    y = sno.snap_to_ground(x, z)
    return PosDir(x, y, z, node.guid)


def generate_point_lights(terrain: Terrain, node_masks: NodeMasks, bits: Bits) -> list[PointLight]:
    terrain_nodes = [node for node in terrain.nodes if node_masks.is_included(node)]
    overall_size = 0
    print(f'nodes: {len(terrain.nodes)} total, {len(terrain_nodes)} included')
    for node in terrain_nodes:
        sno = bits.snos.get_sno_by_name(node.mesh_name)
        overall_size += sno.bounding_box_2d_size()
    print(f'nodes: {len(terrain.nodes)} total, {len(terrain_nodes)} included, overall size: {overall_size}')

    lights = list()
    density = 0.25 / 16  # one point light per 8x8m tile
    num_lights = int(overall_size * density)
    print(f'point-light density {density}/m² -> num point-lights: {num_lights}')
    terrain_nodes_weights = [bits.snos.get_sno_by_name(node.mesh_name).bounding_box_2d_size() for node in terrain_nodes]
    random_choices = random.choices(terrain_nodes, terrain_nodes_weights, k=num_lights)
    for random_choice in random_choices:
        assert isinstance(random_choice, TerrainNode)
        pos = random_position(random_choice, bits)
        if pos is None:
            continue
        assert isinstance(pos, PosDir)
        pos.y += 4
        light = PointLight(position=pos)
        light.inner_radius = 4
        light.outer_radius = 12
        lights.append(light)
    return lights


def light_up(map_name: str, region_name: str, nodes: list[str], exclude_nodes: list[str], override: bool, bits_path: str, node_bits_path: str):
    bits = Bits(bits_path)
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    region.load_data()
    region.load_terrain()
    region.terrain.print()
    node_masks = NodeMasks(nodes, exclude_nodes)
    node_bits = bits if node_bits_path is None else Bits(node_bits_path)

    point_lights = generate_point_lights(region.terrain, node_masks, node_bits)
    print(f'{len(point_lights)} point-lights generated')
    region_lights = region.get_lights()
    if override:
        # clear pre-existing point lights
        region_lights = [light for light in region_lights if not isinstance(light, PointLight)]
    region_lights.extend(point_lights)
    region.lights = region_lights

    region.terrain = None  # don't try to re-save the loaded terrain
    region.save()
    region.delete_lnc()
    print('Done!')
    print('Open & save in SE.')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy light_up')
    parser.add_argument('map')
    parser.add_argument('region')
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
    light_up(args.map, args.region, args.nodes, args.exclude_nodes, args.override, args.bits, args.node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
