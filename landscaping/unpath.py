import argparse
import math
import random
import sys

from bits.bits import Bits
from bits.maps.decals_gas import Decal
from bits.maps.region import Region
from gas.molecules import Position


def unpath_region(region: Region):
    print(region.get_name())
    region.load_terrain()
    num_changed_nodes = 0
    num_added_decals = 0
    sizes = {'04x04': 1, '08x04': 2, '08x08': 4}
    for node in region.terrain.nodes:
        if 'pth' not in node.mesh_name:
            continue
        changed = False
        for size in sizes:
            if node.mesh_name.startswith(f't_xxx_pth_{size}-'):
                changed = True
                flr_size = size if size != '08x04' else '04x08'  # sigh
                node.mesh_name = f't_xxx_flr_{flr_size}-v0'
                # add decals
                for _ in range(sizes[size]):
                    if random.uniform(0, 1) > 0.5:
                        continue
                    decal_texture = f'art\\bitmaps\\decals\\b_d_{node.texture_set}-path.raw'  # naming convention established by minibits/generic-decals
                    decal_origin = Position(random.uniform(-2, 2), 1, random.uniform(-2, 2), node.guid)
                    decal_orientation = Decal.rad_to_decal_orientation(random.uniform(0, math.tau))
                    region.get_decals().decals.append(Decal(texture=decal_texture, decal_origin=decal_origin, decal_orientation=decal_orientation))
                    num_added_decals += 1
        if changed:
            num_changed_nodes += 1
        else:
            print(f'Warning: unhandled path node: {node.mesh_name} {node.guid}')
    if num_changed_nodes:
        print(f'Converted {num_changed_nodes} nodes, added {num_added_decals} decals')
        region.save()
        if num_added_decals:
            region.delete_lnc()


def unpath(bits_path: str, map_name: str, region_names: list[str]):
    bits = Bits(bits_path)
    m = bits.maps[map_name]

    if len(region_names) > 0:
        for region_name in region_names:
            unpath_region(m.get_region(region_name))
    else:
        for region in m.get_regions().values():
            unpath_region(region)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Un-path')
    parser.add_argument('map')
    parser.add_argument('region', nargs='*')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    unpath(args.bits, args.map, args.region)


if __name__ == '__main__':
    main(sys.argv[1:])
