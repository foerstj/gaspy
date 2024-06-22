import argparse
import colorsys
import random
import sys
from argparse import Namespace

from bits.bits import Bits
from bits.maps.light import PointLight, PosDir
from bits.maps.terrain import Terrain, TerrainNode
from gas.color import Color
from landscaping.node_mask import NodeMasks


class LightProfile:
    def __init__(self, args: Namespace):
        self.density: float = args.density
        self.y: float = args.y
        self.y_var: float = args.y_var
        self.irad: float = args.irad
        self.irad_var: float = args.irad_var
        self.orad: float = args.orad
        self.orad_var: float = args.orad_var
        self.intensity: float = args.intensity
        self.intensity_var: float = args.intensity_var
        self.hue: float = args.hue
        self.hue_var: float = args.hue_var
        self.sat: float = args.sat
        self.sat_var: float = args.sat_var
        self.val: float = args.val
        self.val_var: float = args.val_var

    def random_point_light(self, pos: PosDir) -> PointLight:
        pos.y += random.uniform(self.y - self.y_var, self.y + self.y_var)
        light = PointLight(position=pos)
        light.inner_radius = random.uniform(self.irad - self.irad_var, self.irad + self.irad_var)
        light.outer_radius = random.uniform(self.orad - self.orad_var, self.orad + self.orad_var)
        light.intensity = random.uniform(self.intensity - self.intensity_var, self.intensity + self.intensity_var)
        hue = random.uniform(self.hue - self.hue_var, self.hue + self.hue_var)
        sat = random.uniform(self.sat - self.sat_var, self.sat + self.sat_var)
        val = random.uniform(self.val - self.val_var, self.val + self.val_var)
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        r, g, b = [int(x * 255) for x in (r, g, b)]
        light.color = Color.from_argb(255, r, g, b)
        return light


def random_position(node: TerrainNode, bits: Bits) -> PosDir or None:
    sno = bits.snos.get_sno_by_name(node.mesh_name)
    x = random.uniform(sno.sno.bounding_box.min.x, sno.sno.bounding_box.max.x)
    z = random.uniform(sno.sno.bounding_box.min.z, sno.sno.bounding_box.max.z)
    pos_found = sno.is_in_floor_2d(x, z)
    if not pos_found:
        return None
    y = sno.snap_to_ground(x, z)
    return PosDir(x, y, z, node.guid)


def generate_point_lights(terrain: Terrain, node_masks: NodeMasks, profile: LightProfile, bits: Bits) -> list[PointLight]:
    terrain_nodes = [node for node in terrain.nodes if node_masks.is_included(node)]
    overall_size = 0
    print(f'nodes: {len(terrain.nodes)} total, {len(terrain_nodes)} included')
    for node in terrain_nodes:
        sno = bits.snos.get_sno_by_name(node.mesh_name)
        overall_size += sno.bounding_box_2d_size()
    print(f'nodes: {len(terrain.nodes)} total, {len(terrain_nodes)} included, overall size: {overall_size}')

    lights = list()
    num_lights = int(overall_size * profile.density)
    print(f'point-light density {profile.density}/m² -> num point-lights: {num_lights}')
    terrain_nodes_weights = [bits.snos.get_sno_by_name(node.mesh_name).bounding_box_2d_size() for node in terrain_nodes]
    random_choices = random.choices(terrain_nodes, terrain_nodes_weights, k=num_lights)
    for random_choice in random_choices:
        assert isinstance(random_choice, TerrainNode)
        pos = random_position(random_choice, bits)
        if pos is None:
            continue
        assert isinstance(pos, PosDir)

        light = profile.random_point_light(pos)

        lights.append(light)
    return lights


def light_up(map_name: str, region_name: str, nodes: list[str], exclude_nodes: list[str], profile: LightProfile, override: bool, bits_path: str, node_bits_path: str):
    bits = Bits(bits_path)
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    region.load_data()
    region.load_terrain()
    region.terrain.print()
    node_masks = NodeMasks(nodes, exclude_nodes)
    node_bits = bits if node_bits_path is None else Bits(node_bits_path)

    point_lights = generate_point_lights(region.terrain, node_masks, profile, node_bits)
    print(f'{len(point_lights)} point-lights generated')
    region_lights = region.get_lights()
    if override:
        # clear pre-existing point lights
        region_lights = [light for light in region_lights if not isinstance(light, PointLight) or not node_masks.is_included(region.terrain.find_node(light.position.node_guid))]
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

    parser.add_argument('--density', type=float, default=1/8/8)  # default one light per 8x8m tile
    parser.add_argument('--y', type=float, default=10)
    parser.add_argument('--y-var', type=float, default=2)
    parser.add_argument('--irad', type=float, default=0)
    parser.add_argument('--irad-var', type=float, default=0)
    parser.add_argument('--orad', type=float, default=20)
    parser.add_argument('--orad-var', type=float, default=4)
    parser.add_argument('--intensity', type=float, default=0.5)
    parser.add_argument('--intensity-var', type=float, default=0.2)
    parser.add_argument('--hue', type=float, default=1)
    parser.add_argument('--hue-var', type=float, default=0)
    parser.add_argument('--sat', type=float, default=1)
    parser.add_argument('--sat-var', type=float, default=0)
    parser.add_argument('--val', type=float, default=1)
    parser.add_argument('--val-var', type=float, default=0)

    parser.add_argument('--override', action='store_true')

    parser.add_argument('--bits', default=None)
    parser.add_argument('--node-bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    profile = LightProfile(args)
    light_up(args.map, args.region, args.nodes, args.exclude_nodes, profile, args.override, args.bits, args.node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
