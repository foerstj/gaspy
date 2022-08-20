import sys

from bits.bits import Bits
from bits.region import Region


def brush_up_region(r: Region):
    print(r.get_name())


def brush_up(map_name: str):
    bits = Bits()
    m = bits.maps[map_name]
    for r in m.get_regions().values():
        brush_up_region(r)


def main(argv):
    map_name = argv[0]
    brush_up(map_name)


if __name__ == '__main__':
    main(sys.argv[1:])
