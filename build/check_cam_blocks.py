import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region
from landscaping.brush_up import contains_any


def check_cam_blocks_in_region(region: Region, bad_cam_block_nodes: list[str]) -> int:
    num_bad_cam_blocks = 0
    for node in region.get_terrain().nodes:
        if contains_any(node.mesh_name, bad_cam_block_nodes):
            if node.bounds_camera:
                print(f'Bad cam-block in {region.get_name()}: {node.guid} {node.mesh_name}')
                num_bad_cam_blocks += 1
    return num_bad_cam_blocks


BAD_CAM_BLOCK_NODES = [
    # bridges
    '_brdg_rop',
    '_brdg-wood',
    '-stonebridge',
    # ele wheels
    '-ele-wheels-a',
    # houses
    '-door-top',
    # house related
    '_coop-a',
    '_well-a',
    '_flr_gravestone',
    # cave entrances
    '-back-top',
    '-front-top',
    '_wal_cave-04',
    # dungeon doors
    '-celar-b',  # house cellar entrance
    '_dgn_wal_archway',
    '_dgn_wal_h2o_archway',
    '_cry01_portal-base-a',
    '_cry01_room_archdor',
    '_cry01_wal_arch-1-a',
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


def check_cam_blocks(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    bad_cam_block_nodes = BAD_CAM_BLOCK_NODES
    num_bad_cam_blocks = 0
    print(f'Checking cam-blocks in {map_name}...')
    for region in _map.get_regions().values():
        region_bad_cam_blocks = check_cam_blocks_in_region(region, bad_cam_block_nodes)
        num_bad_cam_blocks += region_bad_cam_blocks
    print(f'Checking cam-blocks in {map_name}: {num_bad_cam_blocks} bad cam-blocks')
    return num_bad_cam_blocks == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_cam_blocks')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    bits = Bits(args.bits)
    valid = check_cam_blocks(bits, args.map)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
