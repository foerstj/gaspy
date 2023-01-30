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


BAD_CAM_BLOCK_NODES = ['t_xxx_brdg_rop', '-ele-wheels-a']


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


def main(argv) -> int:
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    valid = check_cam_blocks(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
