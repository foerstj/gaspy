import sys

from bits import Bits


def autosize_trees(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    m.print(False)
    region.print('', 'trees')
    print('AUTOSIZE TREES TODO')


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    autosize_trees(map_name, region_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
