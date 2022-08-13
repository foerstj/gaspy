import sys

from bits.bits import Bits
from world_levels import add_map_world_levels


def add_world_levels(bits: Bits, map_name: str):
    _map = bits.maps[map_name]
    add_map_world_levels(_map, bits)


def main(argv):
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    add_world_levels(bits, map_name)


if __name__ == '__main__':
    main(sys.argv[1:])
