import argparse
import sys

from gas.gas import Hex, Attribute
from bits.bits import Bits
from bits.maps.region import Region
from .replace_hexes import replace_hexes_in_dir, replace_hexes_in_file


def edit_region_mesh_range(region: Region, new_mesh_range: Hex):
    new_mesh_range_str = str(new_mesh_range)
    assert new_mesh_range_str.startswith('0x00000')  # only last 3 digits may be used
    old_mesh_range: Hex = region.get_data().mesh_range
    if new_mesh_range == old_mesh_range:
        print('no change in mesh range')
        return
    # check that no region already uses the new mesh range
    other_regions: list[Region] = [r for r in region.map.get_regions().values() if r.get_name() != region.get_name()]
    other_regions_using_new_mesh_range = [r for r in other_regions if r.get_data().mesh_range == new_mesh_range]
    assert len(other_regions_using_new_mesh_range) == 0, f'new mesh range is already used by {[r.get_name() for r in other_regions_using_new_mesh_range]}'

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


def edit_region_scid_range(region: Region, new_scid_range: Hex, isolated=False):
    new_scid_range_str = str(new_scid_range)
    assert new_scid_range_str.startswith('0x00000')  # only last 3 digits may be used
    old_scid_range: Hex = region.get_data().scid_range
    if new_scid_range == old_scid_range:
        print('no change in scid range')
        return
    # check that no region already uses the new scid range
    other_regions: list[Region] = [r for r in region.map.get_regions().values() if r.get_name() != region.get_name()]
    other_regions_using_new_scid_range = [r for r in other_regions if r.get_data().scid_range == new_scid_range]
    assert len(other_regions_using_new_scid_range) == 0, f'new scid range is already used by {[r.get_name() for r in other_regions_using_new_scid_range]}'
    # check that target region is the only one with the old scid range
    if not isolated:
        other_regions_using_old_scid_range = [r for r in other_regions if r.get_data().scid_range == old_scid_range]
        assert len(other_regions_using_old_scid_range) == 0, f'old scid range is also used by {[r.get_name() for r in other_regions_using_old_scid_range]}'

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
    replace_in_dir = region.map.gas_dir if not isolated else region.gas_dir
    replace_hexes_in_dir(replace_in_dir.path, scid_replacements, 'elevator.gas')
    replace_hexes_in_dir(replace_in_dir.path, scid_replacements, 'interactive.gas')
    replace_hexes_in_dir(replace_in_dir.path, scid_replacements, 'special.gas')


def edit_region_guid(region: Region, new_guid: Hex, isolated=False):
    old_guid: Hex = region.get_data().id
    if new_guid == old_guid:
        print('no change in guid')
        return
    # check that no region already uses the new guid
    other_regions: list[Region] = [r for r in region.map.get_regions().values() if r.get_name() != region.get_name()]
    other_regions_using_new_guid = [r for r in other_regions if r.get_data().scid_range == new_guid]
    assert len(other_regions_using_new_guid) == 0, f'new guid is already used by {[r.get_name() for r in other_regions_using_new_guid]}'
    # check that target region is the only one with the old guid
    if not isolated:
        other_regions_using_old_guid = [r for r in other_regions if r.get_data().scid_range == old_guid]
        assert len(other_regions_using_old_guid) == 0, f'old guid is also used by {[r.get_name() for r in other_regions_using_old_guid]}'

    print('edit guid: ' + str(old_guid) + ' -> ' + str(new_guid))
    region.get_data().id = new_guid
    region.save()

    replace_hexes_in_file(region.gas_dir.get_subdir('editor').get_gas_file('stitch_helper').path, [(old_guid, new_guid)])

    # guid can be referenced across the map in node fades - in triggers and elevators
    guid_replacement = [(old_guid, new_guid)]
    replace_in_dir = region.map.gas_dir if not isolated else region.gas_dir
    replace_hexes_in_dir(replace_in_dir.path, guid_replacement, 'elevator.gas')
    replace_hexes_in_dir(replace_in_dir.path, guid_replacement, 'special.gas')


def edit_region_ids(map_name, region_name, mesh_range=None, scid_range=None, guid=None, isolated=False):
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
        edit_region_scid_range(region, Hex.parse(scid_range), isolated)
    region.gas_dir.clear_cache()
    region.load_data()
    if guid is not None:
        edit_region_guid(region, Hex.parse(guid), isolated)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit region ids')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--mesh-range', default=None)
    parser.add_argument('--scid-range', default=None)
    parser.add_argument('--guid', default=None)
    parser.add_argument('--all', default=None)
    parser.add_argument('--isolated', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    mesh_range = args.mesh_range or args.all
    scid_range = args.scid_range or args.all
    guid = args.guid or args.all
    edit_region_ids(args.map, args.region, mesh_range, scid_range, guid, args.isolated)


if __name__ == '__main__':
    main(sys.argv[1:])
