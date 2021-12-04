import argparse
import sys

from bits import Bits
from file_helper import replace_hexes_in_dir
from gas import Hex
from region import Region


def edit_region_mesh_range(region: Region, new_mesh_range: Hex):
    old_mesh_range: Hex = region.get_data().mesh_range
    print('edit mesh range: ' + str(old_mesh_range) + ' -> ' + str(new_mesh_range))
    raise NotImplementedError  # TODO


def edit_region_scid_range(region: Region, new_scid_range: Hex):
    old_scid_range: Hex = region.get_data().scid_range
    print('edit scid range: ' + str(old_scid_range) + ' -> ' + str(new_scid_range))
    raise NotImplementedError  # TODO


def edit_region_guid(region: Region, new_guid: Hex):
    old_guid: Hex = region.get_data().id
    print('edit guid: ' + str(old_guid) + ' -> ' + str(new_guid))
    region.get_data().mesh_range = new_guid
    region.save()

    # guid can be referenced across the map in node fades - in triggers and elevators
    replace_hexes_in_dir(region.map.gas_dir.path, [(old_guid, new_guid)], 'special.gas')
    replace_hexes_in_dir(region.map.gas_dir.path, [(old_guid, new_guid)], 'elevator.gas')


def edit_region_ids(map_name, region_name, mesh_range=None, scid_range=None, guid=None):
    bits = Bits()
    assert map_name in bits.maps, map_name
    _map = bits.maps[map_name]
    regions = _map.get_regions()
    assert region_name in regions, region_name
    region = regions[region_name]
    if mesh_range is not None:
        edit_region_mesh_range(region, Hex.parse(mesh_range))
    if scid_range is not None:
        edit_region_scid_range(region, Hex.parse(scid_range))
    if guid is not None:
        edit_region_guid(region, Hex.parse(guid))


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit region ids')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--mesh-range', default=None)
    parser.add_argument('--scid-range', default=None)
    parser.add_argument('--guid', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    edit_region_ids(args.map, args.region, args.mesh_range, args.scid_range, args.guid)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
