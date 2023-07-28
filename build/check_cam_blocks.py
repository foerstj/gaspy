import argparse
import os
import sys

from bits.bits import Bits
from bits.maps.region import Region
from landscaping.brush_up import contains_any


def check_cam_blocks_in_region(region: Region, recommendations: dict[str, bool], fix=False) -> int:
    num_bad_cam_blocks = 0
    for node in region.get_terrain().nodes:
        if recommendations[node.mesh_name.lower()] is False:
            if node.bounds_camera:
                print(f'Bad cam-block in {region.get_name()}: {node.guid} {node.mesh_name}')
                num_bad_cam_blocks += 1
                if fix:
                    node.bounds_camera = False
    return num_bad_cam_blocks


def load_usage_bounds_camera():
    bounds_camera_usage = dict()
    with open(os.path.join('input', 'bounds_camera.txt')) as file:
        for line in file:
            k, v = [x.strip() for x in line.split(':')]
            bounds_camera_usage[k] = v
    return bounds_camera_usage


BAD_CAM_BLOCK_NODES = [
    # bridges
    '_brdg_rop',
    '_brdg-wood',
    '-stonebridge',
    # ele wheels
    '-ele-wheels-a',
    # houses
    '-door-top',
    '_fh00_hfloor_1b',
    # house related
    '_coop-a',
    '_well-a',
    '_flr_gravestone',
    '_toolshed',
    # cave entrances
    '-back-top',
    '-front-top',
    '_wal_cave-04',
    # dungeon doors
    '-celar-b',  # house cellar entrance
    '_dgn_wal_archway',
    '_dgn_wal_h2o_archway',
    '_dgn_zportal-base-a',
    '_cry01_portal-base-a',
    '_cry01_room_archdor',
    '_cry01_wal_arch-1-a',
    '_cry01_wal_r1a',
    '_cry01_str_cnr',
    '_cry01_room_2a',
    '_cry01_room_2c',
    '_cry01_room_3a',
    '_cry01_str_spiral-1a',
    # dungeon pillars
    '_dgn_flr_pillar-a',
    '_dgn_flr_h2o_pillar-a',
    '_cry01_flr_pedestal-a',
    '_cry01_flr_pillar-a',
    # dungeon spiral stairs
    '_dgn_stair_spiral-top-stairs-a',
    '_dgn_stair_spiral-stair-a',
    '_dgn_stair_h2o_spiral-base-floor-a',
    # stone ridges
    '_flr_rockwall',
    # town gate
    '_bt_towngate-entrance-top',
]


def get_bounds_camera_recommendations():
    usages = load_usage_bounds_camera()
    recommendations = dict()
    for mesh_name in usages:
        usage = usages[mesh_name]
        rec = True if usage == 'true' else False if usage == 'false' else None
        if contains_any(mesh_name, BAD_CAM_BLOCK_NODES):
            rec = False
        recommendations[mesh_name] = rec
    return recommendations


def check_cam_blocks(bits: Bits, map_name: str, fix=False) -> bool:
    _map = bits.maps[map_name]
    recommendations = get_bounds_camera_recommendations()
    num_bad_cam_blocks = 0
    print(f'Checking cam-blocks in {map_name}...')
    for region in _map.get_regions().values():
        region_bad_cam_blocks = check_cam_blocks_in_region(region, recommendations, fix)
        if region_bad_cam_blocks and fix:
            region.save()
        num_bad_cam_blocks += region_bad_cam_blocks
    print(f'Checking cam-blocks in {map_name}: {num_bad_cam_blocks} bad cam-blocks')
    return num_bad_cam_blocks == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_cam_blocks')
    parser.add_argument('map')
    parser.add_argument('--fix', action='store_true')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    bits = Bits(args.bits)
    valid = check_cam_blocks(bits, args.map, args.fix)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
