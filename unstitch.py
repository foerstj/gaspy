import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from gas.molecules import Hex


MESH_INFO = {
    # better read from file at some point
    't_xxx_wal_04-thin': [True, False, True, False],
    't_xxx_wal_08-thin': [True, False, True, False],
    't_xxx_wal_12-thin': [True, False, True, False],
}


def should_unstitch(node_id: Hex, node_door: int, region: Region, impassable_doors: bool) -> bool:
    if not impassable_doors:
        return True  # unstitch all

    node = region.get_terrain().find_node(node_id)
    assert node, f'Node {node_id} not found'
    if node.mesh_name in MESH_INFO:
        door_is_passable = MESH_INFO[node.mesh_name][node_door - 1]
        return not door_is_passable  # unstitch if door is not passable
    return False  # not sure, keep stitch


def unstitch_region(region: Region, impassable_doors: bool) -> int:
    region_stitches = region.get_stitch_helper()
    num_rem_stitches = 0
    for stitch_editor in region_stitches.stitch_editors:
        stitch_ids_to_remove = list()
        for stitch_id, (node_id, door) in stitch_editor.node_ids.items():
            if should_unstitch(node_id, door, region, impassable_doors):
                stitch_ids_to_remove.append(stitch_id)
        num_rem_stitches += len(stitch_ids_to_remove)
        for stitch_id in stitch_ids_to_remove:
            del stitch_editor.node_ids[stitch_id]
    region_stitches.stitch_editors = [se for se in region_stitches.stitch_editors if len(se.node_ids) > 0]  # cleanup empty stitch groups
    print(f'  {region.get_name()}: {num_rem_stitches}')
    if num_rem_stitches > 0:
        region.terrain = None  # no need to re-save nodes.gas
        region.save()
    return num_rem_stitches


def unstitch(m: Map, regions: str, impassable_doors: bool):
    print(f'Unstitching {m.get_name()}...')
    num_rem_stitches = 0
    for region_name, region in m.get_regions().items():
        if regions and regions not in region_name:
            continue
        num_rem_stitches += unstitch_region(region, impassable_doors)
    print(f'Unstitching {m.get_name()} done: {num_rem_stitches} stitches removed.')


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description='GasPy Unstitch')
    parser.add_argument('map', help='name of the map to unstitch')
    parser.add_argument('--regions', help='unstitch regions matching arg')
    parser.add_argument('--impassable-doors', action='store_true', help='unstitch impassable doors (rock wall-ish)')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_name = args.map
    regions = args.regions
    impassable_doors = args.impassable_doors
    bits = Bits()
    m = bits.maps[map_name]
    unstitch(m, regions, impassable_doors)


if __name__ == '__main__':
    main(sys.argv[1:])
