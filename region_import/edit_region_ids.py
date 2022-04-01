import argparse
import sys

from gas.gas import Hex, Attribute
from bits.bits import Bits
from bits.region import Region
from .replace_hexes import replace_hexes_in_dir, replace_hexes_in_file


def edit_region_mesh_range(region: Region, new_mesh_range: Hex):
    new_mesh_range_str = str(new_mesh_range)
    assert new_mesh_range_str.startswith('0x00000')  # only last 3 digits may be used
    old_mesh_range: Hex = region.get_data().mesh_range
    if new_mesh_range == old_mesh_range:
        print('no change in mesh range')
        return

    print('edit mesh range: ' + str(old_mesh_range) + ' -> ' + str(new_mesh_range))
    region.get_data().mesh_range = new_mesh_range
    region.save()

    new_mesh_prefix = new_mesh_range_str[7:]
    assert len(new_mesh_prefix) == 3, new_mesh_prefix
    # replace & collect in node_mesh_index
    node_mesh_index_file = region.gas_dir.get_subdir('index').get_gas_file('node_mesh_index')
    mesh_replacements = list()
    for node_mesh_attr in node_mesh_index_file.get_gas().get_section('node_mesh_index').items:
        assert isinstance(node_mesh_attr, Attribute)
        old_hex = Hex.parse(node_mesh_attr.name)
        new_hex = Hex.parse('0x'+new_mesh_prefix+node_mesh_attr.name[5:])
        mesh_replacements.append((old_hex, new_hex))
        node_mesh_attr.name = new_hex.to_str_lower()
    node_mesh_index_file.save()
    # replace mesh references in terrain nodes
    replace_hexes_in_file(region.gas_dir.get_subdir('terrain_nodes').get_gas_file('nodes').path, mesh_replacements)


def edit_region_scid_range(region: Region, new_scid_range: Hex):
    new_scid_range_str = str(new_scid_range)
    assert new_scid_range_str.startswith('0x00000')  # only last 3 digits may be used
    old_scid_range: Hex = region.get_data().scid_range
    if new_scid_range == old_scid_range:
        print('no change in scid range')
        return
    # check that no region already uses the new scid range
    regions_data = [r.get_data() for r in region.map.get_regions().values()]
    scid_ranges = [d.scid_range for d in regions_data]
    assert new_scid_range not in scid_ranges, 'new scid range is already used'
    # check that target region is the only one with the old scid range
    assert scid_ranges.count(old_scid_range) == 1, 'target region is not the only one with the old scid range'

    print('edit scid range: ' + str(old_scid_range) + ' -> ' + new_scid_range_str)
    region.get_data().scid_range = new_scid_range
    region.save()

    new_scid_prefix = new_scid_range_str[7:]
    assert len(new_scid_prefix) == 3, new_scid_prefix
    old_scids = region.get_scids()
    scid_replacements = [(old_scid, Hex.parse('0x'+new_scid_prefix+str(old_scid)[5:])) for old_scid in old_scids]
    # replace in all files of target region
    replace_hexes_in_dir(region.gas_dir.path, scid_replacements)
    # replace in referencing files of all regions
    replace_hexes_in_dir(region.map.gas_dir.path, scid_replacements, 'elevator.gas')
    replace_hexes_in_dir(region.map.gas_dir.path, scid_replacements, 'interactive.gas')
    replace_hexes_in_dir(region.map.gas_dir.path, scid_replacements, 'special.gas')


def edit_region_guid(region: Region, new_guid: Hex):
    old_guid: Hex = region.get_data().id
    if new_guid == old_guid:
        print('no change in guid')
        return
    # check that no region already uses the new guid
    regions_data = [r.get_data() for r in region.map.get_regions().values()]
    guids = [d.id for d in regions_data]
    assert new_guid not in guids, 'new region guid is already used'
    # check that target region is the only one with the old guid
    assert guids.count(old_guid) == 1, 'target region is not the only one with the old guid'

    print('edit guid: ' + str(old_guid) + ' -> ' + str(new_guid))
    region.get_data().id = new_guid
    region.save()

    replace_hexes_in_file(region.gas_dir.get_subdir('editor').get_gas_file('stitch_helper').path, [(old_guid, new_guid)])

    # guid can be referenced across the map in node fades - in triggers and elevators
    replace_hexes_in_dir(region.map.gas_dir.path, [(old_guid, new_guid)], 'elevator.gas')
    replace_hexes_in_dir(region.map.gas_dir.path, [(old_guid, new_guid)], 'special.gas')


def edit_region_ids(map_name, region_name, mesh_range=None, scid_range=None, guid=None):
    bits = Bits()
    assert map_name in bits.maps, map_name
    _map = bits.maps[map_name]
    regions = _map.get_regions()
    assert region_name in regions, region_name
    region = regions[region_name]
    if mesh_range is not None:
        edit_region_mesh_range(region, Hex.parse(mesh_range))
    region.gas_dir.clear_cache()
    region.load_data()
    if scid_range is not None:
        edit_region_scid_range(region, Hex.parse(scid_range))
    region.gas_dir.clear_cache()
    region.load_data()
    if guid is not None:
        edit_region_guid(region, Hex.parse(guid))


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit region ids')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--mesh-range', default=None)
    parser.add_argument('--scid-range', default=None)
    parser.add_argument('--guid', default=None)
    parser.add_argument('--all', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    mesh_range = args.mesh_range or args.all
    scid_range = args.scid_range or args.all
    guid = args.guid or args.all
    edit_region_ids(args.map, args.region, mesh_range, scid_range, guid)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
