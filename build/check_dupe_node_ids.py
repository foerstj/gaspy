import sys

from bits.bits import Bits
from region_import.check_dupe_node_ids import check_map


def check_dupe_node_ids(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    print(f'Checking dupe node ids in {map_name}...')
    num_dupes = check_map(_map, False)
    print(f'Checking dupe node ids in {map_name}: {num_dupes} duplicate node ids')
    return num_dupes == 0


def main(argv) -> int:
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    valid = check_dupe_node_ids(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
