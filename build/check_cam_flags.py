import argparse
import os
import sys

from bits.bits import Bits
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode
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
    # shrines
    'heal-area',
    'mana-area',
    # stalagmites
    '_flr_stalagmite-4',
    '_flr_h2o_stalagmite-4',
    # ruins
    '_ruin_alcove',
    '_ruin_arch',
    '_ruin_block',
    '_ruin_pedestal',
    '_ruin_pillar',
    '_ruin_support',
    '_ruin_wall',
    # drips
    '_drips-',
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
    # EoS nodes
    '_shack-',
    '_brdwlk-broken-',
    # GR
    't_nt01_towngate-top',
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
    '_brdwlk-dock-04x08-a',  # a = ground, b = boardwalk
]

AMBIGUOUS_CAM_BLOCK_NODES = [
    'ele-round-tube',  # I want these to be cam-blocking in Collab24
]

BAD_CAM_FADE_NODES = [
    # EoS nodes:
    '_sea03_',
    '_jng01_h2o-',
    '_shack-',
    '_brdwlk-dock-04x08-a',  # a = ground, b = boardwalk
    '_brdwlk-broken-',
]

GOOD_CAM_FADE_NODES = []

AMBIGUOUS_CAM_FADE_NODES = [
    # GR
    't_nt01_towngate-top',  # I don't want them to fade in GR
    # no need to fade if faded manually
    't_xxx_wal_cave-split-12-front-top',
    't_xxx_wal_cave-split-12-back-top',
    't_dm01_mine-entry-front-top',
    # no need to fade manually if cam-faded
    't_bt_roof-blacksmith-canopy',
    't_grs01_houses_tudor-blksmith-a-canopy',
    # doesn't hurt to cam-fade this additionally
    't_dc01_dunes-temple-entrance-8',
]


def recommend(mesh_name: str, usages: dict):
    if mesh_name not in usages:
        print(f'Note: no ground truth for node mesh {mesh_name}')
        return None
    usage = usages[mesh_name]
    if usage == 'true':
        return True
    if usage == 'false':
        return False
    return None  # ambiguous / no recommendation


# reduce custom meshes to their base/original
def reduce_mesh_name(mesh_name: str) -> str:
    reductions = {
        # Green Range generic droog dwelling
        't_xxx_dg_dwelling': 't_dc01_dwelling',
        't_xxx_dg_statue': 't_dc01_statue',
        # EE / GR chapel
        't_ee_chapel': 't_swp_chapel',
    }
    for custom, base in reductions.items():
        if mesh_name.startswith(custom):
            return mesh_name.replace(custom, base, 1)

    return mesh_name


def recommend_cam_block(mesh_name: str, usages: dict):
    mesh_name = reduce_mesh_name(mesh_name)

    if contains_any(mesh_name, BAD_CAM_BLOCK_NODES) and not contains_any(mesh_name, BAD_CAM_BLOCK_NODES_EXCLUDE):
        return False
    if contains_any(mesh_name, GOOD_CAM_BLOCK_NODES):
        return True
    if contains_any(mesh_name, AMBIGUOUS_CAM_BLOCK_NODES):
        return None

    return recommend(mesh_name, usages)


def recommend_cam_fade(mesh_name: str, usages: dict):
    mesh_name = reduce_mesh_name(mesh_name)

    if contains_any(mesh_name, BAD_CAM_FADE_NODES):
        return False
    if contains_any(mesh_name, GOOD_CAM_FADE_NODES):
        return True
    if contains_any(mesh_name, AMBIGUOUS_CAM_FADE_NODES):
        return None

    return recommend(mesh_name, usages)


def check_cam_block(node: TerrainNode, usages: dict, region_name: str, fix=False) -> bool:
    mesh_name = node.mesh_name.lower()
    recommendation = recommend_cam_block(mesh_name, usages)
    is_bad = False
    if recommendation is False and node.bounds_camera:
        print(f'  Bad cam-block in {region_name}: {node.guid} {mesh_name}')
        is_bad = True
        if fix:
            node.bounds_camera = False
    if recommendation is True and not node.bounds_camera:
        print(f'  Missing cam-block in {region_name}: {node.guid} {mesh_name}')
        is_bad = True
        if fix:
            node.bounds_camera = True
    return is_bad


def check_cam_fade(node: TerrainNode, usages: dict, region_name: str, fix=False) -> bool:
    mesh_name = node.mesh_name.lower()
    recommendation = recommend_cam_fade(mesh_name, usages)
    is_bad = False
    if recommendation is False and node.camera_fade:
        print(f'  Bad cam-fade in {region_name}: {node.guid} {mesh_name}')
        is_bad = True
        if fix:
            node.camera_fade = False
    if recommendation is True and not node.camera_fade:
        print(f'  Missing cam-fade in {region_name}: {node.guid} {mesh_name}')
        is_bad = True
        if fix:
            node.camera_fade = True
    return is_bad


def check_cam_flags_in_region(region: Region, usages_bounds_camera: dict, usages_camera_fade: dict, fix=False) -> tuple[int, int]:
    num_bad_cam_blocks = 0
    num_bad_cam_fades = 0
    for node in region.get_terrain().nodes:
        if check_cam_block(node, usages_bounds_camera, region.get_name(), fix):
            num_bad_cam_blocks += 1
        if check_cam_fade(node, usages_camera_fade, region.get_name(), fix):
            num_bad_cam_fades += 1
    return num_bad_cam_blocks, num_bad_cam_fades


def load_usages_bounds_camera():
    usages = dict()
    with open(os.path.join('input', 'bounds_camera.txt')) as file:
        for line in file:
            k, v = [x.strip() for x in line.split(':')]
            usages[k] = v
    return usages


def load_usages_camera_fade():
    usages = dict()
    with open(os.path.join('input', 'camera_fade.txt')) as file:
        for line in file:
            k, v = [x.strip() for x in line.split(':')]
            usages[k] = v
    return usages


def check_cam_flags(bits: Bits, map_name: str, fix=False) -> bool:
    _map = bits.maps[map_name]
    usages_bounds_camera = load_usages_bounds_camera()
    usages_camera_fade = load_usages_camera_fade()
    num_bad_cam_blocks = 0
    num_bad_cam_fades = 0
    print(f'Checking cam flags in {map_name}...')
    for region in _map.get_regions().values():
        region_bad_cam_blocks, region_bad_cam_fades = check_cam_flags_in_region(region, usages_bounds_camera, usages_camera_fade, fix)
        if (region_bad_cam_blocks or region_bad_cam_fades) and fix:
            region.save()
        num_bad_cam_blocks += region_bad_cam_blocks
        num_bad_cam_fades += region_bad_cam_fades
    print(f'Checking cam flags in {map_name}: {num_bad_cam_blocks} bad or missing cam-blocks, {num_bad_cam_fades} bad or missing cam-fades')
    return num_bad_cam_blocks == 0 and num_bad_cam_fades == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_cam_flags')
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
    valid = check_cam_flags(bits, args.map, args.fix)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
