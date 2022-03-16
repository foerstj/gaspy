import sys

from bits.bits import Bits
from bits.map import Map


def dupes_in_list(the_list):
    seen = set()
    dupes = set()

    for x in the_list:
        if x not in seen:
            seen.add(x)
        else:
            dupes.add(x)
    return dupes


def check_map(m: Map):
    node_ids = m.get_all_node_ids()
    dupes = dupes_in_list(node_ids)
    for node_id in dupes:
        print(node_id)
    assert len(dupes) == 0, f'{m.get_name()} contains duplicate node ids!'


def check_map_vs_map(m1: Map, m2: Map):
    node_ids1 = set(m1.get_all_node_ids())
    node_ids2 = set(m2.get_all_node_ids())
    common_node_ids = node_ids1.intersection(node_ids2)
    for node_id in common_node_ids:
        print(node_id)
    assert len(common_node_ids) == 0, f'{m1.get_name()} contains {len(common_node_ids)} common node ids with {m2.get_name()}!'


def check_dupe_node_ids(map_name: str, other_map_names: list[str] = None):  # None means all
    bits = Bits()
    m = bits.maps[map_name]

    # check for dupes within map itself
    check_map(m)

    # check for dupes with other maps
    if other_map_names is None:
        other_map_names = list(bits.maps.keys())
        other_map_names.remove(map_name)

    for other_map_name in other_map_names:
        check_map_vs_map(m, bits.maps[other_map_name])

    print('All good.')


def main(argv):
    map_name = argv[0]
    check_dupe_node_ids(map_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
