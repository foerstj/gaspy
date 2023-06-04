import argparse
import math
import random
import sys

from bits.bits import Bits
from bits.maps.decals_gas import Decal
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode
from gas.molecules import Position
from landscaping.node_mask import NodeMasks


def add_path_decals(region: Region, node: TerrainNode, num_tiles: int) -> int:
    num_added_decals = 0
    for _ in range(num_tiles):
        if random.uniform(0, 1) > 0.5:
            continue
        decal_texture = f'art\\bitmaps\\decals\\b_d_{node.texture_set}-path.raw'  # naming convention established by minibits/generic-decals
        decal_origin = Position(random.uniform(-2, 2), 1, random.uniform(-2, 2), node.guid)
        decal_orientation = Decal.rad_to_decal_orientation(random.uniform(0, math.tau))
        region.get_decals().decals.append(Decal(texture=decal_texture, decal_origin=decal_origin, decal_orientation=decal_orientation))
        num_added_decals += 1
    return num_added_decals


def unpath_region(region: Region, node_masks: NodeMasks):
    print(region.get_name())
    region.load_terrain()
    terrain_nodes = [node for node in region.terrain.nodes if node_masks.is_included(node)]
    if len(terrain_nodes) != len(region.terrain.nodes):
        print(f'{len(region.terrain.nodes) - len(terrain_nodes)} terrain nodes excluded')
    num_changed_nodes = 0
    num_added_decals = 0
    sizes_generic = {'04x04': 1, '08x04': 2, '08x08': 4}
    sizes_grass1 = {'4': 1, '4x8': 2, '8': 4}
    sizes_nt = {'4a': 1, '4b': 1, '4x8a': 2, '8a': 4, '8b': 4, '8c': 4, '8d': 4, '8e': 4, '8f': 4, '8g': 4, '8h': 4}
    sizes_wall = ['thick', 'thin']
    sizes_corner = ['ccav', 'cnvx']
    for node in terrain_nodes:
        if 'pth' not in node.mesh_name and 'cobblestone-tx' not in node.mesh_name and 'path' not in node.mesh_name:
            continue
        changed = False

        for size in sizes_generic:
            if node.mesh_name.startswith(f't_xxx_pth_{size}-'):
                changed = True
                flr_size = size if size != '08x04' else '04x08'  # sigh
                node.mesh_name = f't_xxx_flr_{flr_size}-v0'
                num_added_decals += add_path_decals(region, node, sizes_generic[size])
                if node.texture_set == 'grs01cbbl':
                    node.texture_set = 'grs01'
                if node.texture_set == 'nt':
                    node.texture_set = 'sn02'
        for size in sizes_grass1:
            if node.mesh_name.startswith(f't_grs01_path_{size}') and len(node.mesh_name) == 13 + len(size) + 1:
                changed = True
                flr_size = {'4': '04x04', '4x8': '04x08', '8': '08x08'}[size]
                node.mesh_name = f't_xxx_flr_{flr_size}-v0'
                num_added_decals += add_path_decals(region, node, sizes_grass1[size])
        for size in sizes_nt:
            if node.mesh_name == f't_nt03_path_{size}':
                changed = True
                flr_size = '04x08' if size.startswith('4x8') else '04x04' if size.startswith('4') else '08x08'
                node.mesh_name = f't_xxx_flr_{flr_size}-v0'
                num_added_decals += add_path_decals(region, node, sizes_nt[size])
                node.texture_set = 'sn02'
        for size in sizes_wall:
            if node.mesh_name == f't_xxx_pth_02b-{size}':
                changed = True
                node.mesh_name = f't_xxx_wal_02b-{size}'
        for size in sizes_corner:
            if node.mesh_name == f't_xxx_pth_02b-{size}':
                changed = True
                node.mesh_name = f't_xxx_cnr_02b-{size}'
        if node.mesh_name.startswith('t_grs01_cobblestone-tx-04x04-'):
            changed = True
            node.mesh_name = 't_xxx_flr_04x04-v0'
            node.texture_set = 'grs01cbbl'
            num_added_decals += add_path_decals(region, node, 1)
            node.texture_set = 'grs01'

        if changed:
            num_changed_nodes += 1
        else:
            print(f'Warning: unhandled path node: {node.mesh_name} {node.guid}')

    if num_changed_nodes:
        print(f'Converted {num_changed_nodes} nodes, added {num_added_decals} decals')
        region.save()
        if num_added_decals:
            region.delete_lnc()


def unpath(bits_path: str, map_name: str, region_names: list[str], nodes: list[str], exclude_nodes: list[str]):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    node_masks = NodeMasks(nodes, exclude_nodes)

    if len(region_names) > 0:
        for region_name in region_names:
            unpath_region(m.get_region(region_name), node_masks)
    else:
        for region in m.get_regions().values():
            unpath_region(region, node_masks)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Un-path')
    parser.add_argument('map')
    parser.add_argument('region', nargs='*')
    parser.add_argument('--nodes', nargs='*', default=[])
    parser.add_argument('--exclude-nodes', nargs='*', default=[])
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    unpath(args.bits, args.map, args.region, args.nodes, args.exclude_nodes)


if __name__ == '__main__':
    main(sys.argv[1:])
