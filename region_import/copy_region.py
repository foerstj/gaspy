import sys

from bits.bits import Bits


def copy_region(map_name, old_region_name, new_region_name):
    bits = Bits()
    m = bits.maps[map_name]
    regions = m.get_regions()
    region = regions.get(old_region_name)
    assert region is not None, f'Region {old_region_name} does not exist'
    assert regions.get(new_region_name) is None, f'Region {new_region_name} already exists'
    print(f'Copying region in map {map_name}: {old_region_name} -> {new_region_name}')


def main(argv):
    map_name = argv[0]
    old_region_name = argv[1]
    new_region_name = argv[2]
    copy_region(map_name, old_region_name, new_region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
