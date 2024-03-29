import argparse
import os
import sys

from bits.bits import Bits
from bits.maps.region import Region
from landscaping.brush_up import contains_any


# These should all have bounds_camera set to false
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
    '_sundial-a',
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
    # keep nodes - added for generic keep nodes in UPZA
    '_keep_cnr_cncv',
    '_keep_cnr_cnvx',
    '_keep_cnr_outside-top',
    '_keep_flr_outside-pillar',
    '_keep_wall_cap',
    '_keep_wall_clm',
    '_keep_wall_clmn',
    '_keep_wall_diag',
    '_keep_wall_doorway',
    '_keep_wall_outside-bridge-spacer',
    '_keep_wall_outside-clmn',
    '_keep_wall_outside-top',
    '_keep_wall_portal',
    '_keep_wall_thick',
    '_keep_wall_thin',
    # shrines
    'heal-area',
    'mana-area',
    # stalagmites
    '_flr_stalagmite-4',
    '_flr_h2o_stalagmite-4',
    # EoS nodes
    '_shack-',
    '_brdwlk-broken-',
    # EE chapel (GR)
    '_ee_chapel',
]
# ...except these
BAD_CAM_BLOCK_NODES_EXCLUDE = [
    'top-secret',
]

# These should all have bounds_camera set to true
GOOD_CAM_BLOCK_NODES = [
    # EoS nodes:
    '_sea03_',
    '_jng01_h2o-',
    '_brdwlk-dock-',
]


def recommend(mesh_name: str, usages: dict):
    if contains_any(mesh_name, BAD_CAM_BLOCK_NODES) and not contains_any(mesh_name, BAD_CAM_BLOCK_NODES_EXCLUDE):
        return False
    if contains_any(mesh_name, GOOD_CAM_BLOCK_NODES):
        return True

    if mesh_name not in usages:
        print(f'Note: no ground truth for node mesh {mesh_name}')
        return None
    usage = usages[mesh_name]
    if usage == 'true':
        return True
    if usage == 'false':
        return False
    return None  # ambiguous / no recommendation


def check_cam_blocks_in_region(region: Region, usages: dict, fix=False) -> int:
    num_bad_cam_blocks = 0
    for node in region.get_terrain().nodes:
        mesh_name = node.mesh_name.lower()
        recommendation = recommend(mesh_name, usages)
        if recommendation is False and node.bounds_camera:
            print(f'Bad cam-block in {region.get_name()}: {node.guid} {mesh_name}')
            num_bad_cam_blocks += 1
            if fix:
                node.bounds_camera = False
        if recommendation is True and not node.bounds_camera:
            print(f'Missing cam-block in {region.get_name()}: {node.guid} {mesh_name}')
            num_bad_cam_blocks += 1
            if fix:
                node.bounds_camera = True
    return num_bad_cam_blocks


def load_usage_bounds_camera():
    bounds_camera_usage = dict()
    with open(os.path.join('input', 'bounds_camera.txt')) as file:
        for line in file:
            k, v = [x.strip() for x in line.split(':')]
            bounds_camera_usage[k] = v
    return bounds_camera_usage


def check_cam_blocks(bits: Bits, map_name: str, fix=False) -> bool:
    _map = bits.maps[map_name]
    usages = load_usage_bounds_camera()
    num_bad_cam_blocks = 0
    print(f'Checking cam-blocks in {map_name}...')
    for region in _map.get_regions().values():
        region_bad_cam_blocks = check_cam_blocks_in_region(region, usages, fix)
        if region_bad_cam_blocks and fix:
            region.save()
        num_bad_cam_blocks += region_bad_cam_blocks
    print(f'Checking cam-blocks in {map_name}: {num_bad_cam_blocks} bad or missing cam-blocks')
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
