import sys

from bits.bits import Bits
from bits.maps.map import Map
from world_levels import add_map_world_levels


def check_add_map_world_levels(m: Map):
    assert m is not None
    map_worlds = m.get_data().worlds
    assert map_worlds is not None
    assert set(map_worlds.keys()) == {'regular', 'veteran', 'elite'}  # did you forget to add veteran and elite? did you forget renaming normal to regular?


def add_world_levels(map_bits: Bits, map_name: str, template_bits: Bits):
    _map = map_bits.maps[map_name]
    check_add_map_world_levels(_map)  # sanity checks
    add_map_world_levels(_map, template_bits)


def main(argv):
    map_name = argv[0]
    map_bits_path = argv[1] if len(argv) > 1 else None
    template_bits_path = argv[2] if len(argv) > 2 else None
    map_bits = Bits(map_bits_path)
    template_bits = Bits(template_bits_path) if template_bits_path is not None else map_bits
    add_world_levels(map_bits, map_name, template_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
