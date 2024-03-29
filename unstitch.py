import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from gas.molecules import Hex


MESH_INFO = {
    # better read from file at some point
    't_dm01_mine-entry-a': [True, True, True, True, False, True, True, True, False, True, True],
    't_dm01_mine-entry-front-base': [True, True, True, True, False, False, True, True, None, None],
    't_xxx_brdg_rck-04': [True, True],
    't_xxx_brdg_rck-08': [True, True],
    't_xxx_brdg_rck-16-c': [True, True],
    't_xxx_brdg_rck-16-l': [True, True],
    't_xxx_brdg_rck-16-r': [True, True],
    't_xxx_brdg_rck-24-c': [True, True],
    't_xxx_brdg_rck-24-l': [True, True],
    't_xxx_brdg_rck-24-r': [True, True],
    't_xxx_brdg_rck-32-c': [True, True],
    't_xxx_brdg_rck-32-l': [True, True],
    't_xxx_brdg_rck-32-r': [True, True],
    't_xxx_brdg_tx-rck-ramp': [True, True, False, True, True, False, True],
    't_xxx_brdg_tx-rck-wal-08': [True, True, False, True, True, False, True],
    't_xxx_brdg_tx-rck-wal-12': [True, True, False, True, True, False, True],
    't_xxx_brdg_tx-rop-wal-08': [True, True, False, True, True, False, True],
    't_xxx_brdg_tx-rop-wal-12': [True, True, False, True, True, False, True],
    't_xxx_brdg_tx-stg-wal-08': [True, True, False, True, True, False, True],
    't_xxx_brdg_tx-stg-wal-12': [True, True, False, True, True, False, True],
    't_xxx_cnr_04-ccav': [False, True, True, False],
    't_xxx_cnr_04-cnvx': [True, False, False, True],
    't_xxx_cnr_08-ccav': [False, True, True, False],
    't_xxx_cnr_08-cnvx': [True, False, False, True],
    't_xxx_cnr_12-ccav': [False, True, True, False],
    't_xxx_cnr_12-cnvx': [True, False, False, True],
    't_xxx_cnr_tee-04-04-08-l': [True, False, False, False],
    't_xxx_cnr_tee-04-04-08-r': [True, False, False, False],
    't_xxx_cnr_tee-04-08-12-l': [True, False, False, False],
    't_xxx_cnr_tee-04-08-12-r': [True, False, False, False],
    't_xxx_cnr_tee-08-04-12-l': [True, False, False, False],
    't_xxx_cnr_tee-08-04-12-r': [True, False, False, False],
    't_xxx_flr_04x04-v0': [True, True, True, True],
    't_xxx_flr_04x08-v0': [True, True, True, True, True, True],
    't_xxx_flr_08x08-v0': [True, True, True, True, True, True, True, True],
    't_xxx_scaff_tx-topwall-a': [True, True, True, True, True],
    't_xxx_wal_04-diag-thin-l': [True, False, True, True, False, True],
    't_xxx_wal_04-diag-thin-r': [True, True, False, True, True, False],
    't_xxx_wal_04-pth-l': [True, True, False, True, True, True, True, False],
    't_xxx_wal_04-pth-r': [True, True, False, True, True, True, True, False],
    't_xxx_wal_04-thck': [True, True, False, True, True, False],
    't_xxx_wal_04-thin': [True, False, True, False],
    't_xxx_wal_08-thck': [True, True, False, True, True, False],
    't_xxx_wal_08-thin': [True, False, True, False],
    't_xxx_wal_12-thck': [True, True, False, True, True, False],
    't_xxx_wal_12-thin': [True, False, True, False],
    't_xxx_wal_24-diag-thick-l': [True, True, False, True, True, True, False, True],
    't_xxx_wal_24-diag-thick-r': [True, True, True, False, True, True, True, False],
    't_xxx_wal_cave-24-base': [True, True, False, False, True, True, False, False, False, False],
}


class StitchFilter:
    def __init__(self, impassable_doors: bool, one_sided: bool):
        self.impassable_doors = impassable_doors
        self.one_sided = one_sided

    @staticmethod
    def is_impassable_door(stitch_id: Hex, node_id: Hex, node_door: int, region: Region):
        node = region.get_terrain().find_node(node_id)
        assert node, f'Stitch {stitch_id}: node {node_id} not found'
        assert node.mesh_name in MESH_INFO, f'Stitch {stitch_id}: unknown mesh {node.mesh_name} in {region.get_name()}'
        door_is_passable = MESH_INFO[node.mesh_name][node_door - 1]
        return door_is_passable is False  # unstitch if door is not passable

    @staticmethod
    def is_one_sided(stitch_id: Hex, region: Region, dest_region: Region):
        if not dest_region:
            return True  # dest region does not exist - deleting stitch, hope you weren't planning to add the region later
        dest_se = None
        for se in dest_region.get_stitch_helper().stitch_editors:
            if se.dest_region == region.get_name():
                dest_se = se
        if not dest_se:
            return True  # dest region does not even have a stitch_editor group -> unstitch
        dest_stitch_ids = dest_se.node_ids.keys()
        return stitch_id not in dest_stitch_ids  # unstitch if this stitch does not occur in dest region

    def matches(self, stitch_id: Hex, node_id: Hex, node_door: int, region: Region, dest_region: Region):
        if self.impassable_doors is None and self.one_sided is None:
            return True  # no filters set -> unstitch all

        if self.impassable_doors:
            if self.is_impassable_door(stitch_id, node_id, node_door, region):
                return True  # unstitch if door is not passable

        if self.one_sided:
            if self.is_one_sided(stitch_id, region, dest_region):
                return True  # unstitch if stitch is one-sided

        return False


def unstitch_region(region: Region, stitches: StitchFilter) -> int:
    region_stitches = region.get_stitch_helper()
    num_rem_stitches = 0
    for stitch_editor in region_stitches.stitch_editors:
        stitch_ids_to_remove = list()
        dest_region = region.map.get_region(stitch_editor.dest_region)
        for stitch_id, (node_id, door) in stitch_editor.node_ids.items():
            if stitches.matches(stitch_id, node_id, door, region, dest_region):
                stitch_ids_to_remove.append(stitch_id)
        num_rem_stitches += len(stitch_ids_to_remove)
        for stitch_id in stitch_ids_to_remove:
            del stitch_editor.node_ids[stitch_id]
    empty_stitch_editors = [se for se in region_stitches.stitch_editors if len(se.node_ids) == 0]
    num_ses_before = len(region_stitches.stitch_editors)
    region_stitches.stitch_editors = [se for se in region_stitches.stitch_editors if len(se.node_ids) > 0]  # cleanup empty stitch groups
    print(f'  {region.get_name()}: {num_rem_stitches}')
    for ese in empty_stitch_editors:
        # print warnings about completely removed region connections
        print(f'    empty: {ese.dest_region}')
    if num_ses_before > 0 and len(region_stitches.stitch_editors) == 0:
        print(f'    region now completely isolated!')
    if num_rem_stitches > 0:
        region.terrain = None  # no need to re-save nodes.gas
        region.save()
    return num_rem_stitches


class RegionFilter:
    def __init__(self, includes: list[str], excludes: list[str]):
        self.includes = includes if includes is not None else list()
        self.excludes = excludes if excludes is not None else list()

    @staticmethod
    def matches_any(region_name: str, filters: list[str]):
        for s in filters:
            if s in region_name:
                return True
        return False

    def matches(self, region_name) -> bool:
        if len(self.includes) > 0:
            if not self.matches_any(region_name, self.includes):
                return False
        if self.matches_any(region_name, self.excludes):
            return False
        return True


def unstitch(m: Map, regions: RegionFilter, stitches: StitchFilter):
    print(f'Unstitching {m.get_name()}...')
    num_total_stitches = 0
    num_rem_stitches = 0
    for region_name, region in m.get_regions().items():
        if not regions.matches(region_name):
            continue
        num_total_stitches += sum([len(se.node_ids) for se in region.get_stitch_helper().stitch_editors])
        num_rem_stitches += unstitch_region(region, stitches)
    print(f'Unstitching {m.get_name()} done: {num_rem_stitches} / {num_total_stitches} stitches removed.')


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description='GasPy Unstitch')
    parser.add_argument('map', help='name of the map to unstitch')
    parser.add_argument('--regions', nargs='*', help='unstitch regions matching arg')
    parser.add_argument('--exclude-regions', nargs='*', help='do not unstitch regions matching arg')
    parser.add_argument('--impassable-doors', action='store_true', help='unstitch impassable doors (rock wall-ish)')
    parser.add_argument('--one-sided', action='store_true', help='remove one-sided stitches')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_name = args.map
    include_regions = args.regions
    exclude_regions = args.exclude_regions
    impassable_doors = args.impassable_doors
    one_sided = args.one_sided
    bits = Bits()
    m = bits.maps[map_name]
    unstitch(m, RegionFilter(include_regions, exclude_regions), StitchFilter(impassable_doors, one_sided))


if __name__ == '__main__':
    main(sys.argv[1:])
