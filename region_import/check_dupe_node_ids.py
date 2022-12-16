import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region


def dupes_in_list(the_list):
    seen = set()
    dupes = set()

    for x in the_list:
        if x not in seen:
            seen.add(x)
        else:
            dupes.add(x)
    return dupes


def check_map(m: Map, do_assert=True) -> int:
    node_ids = m.get_all_node_ids()
    dupes = dupes_in_list(node_ids)
    for node_id in dupes:
        print(node_id)
    if do_assert:
        assert len(dupes) == 0, f'{m.get_name()} contains duplicate node ids!'
    return len(dupes)


def check_map_vs_map(m1: Map, m2: Map):
    node_ids1 = set(m1.get_all_node_ids())
    node_ids2 = set(m2.get_all_node_ids())
    common_node_ids = node_ids1.intersection(node_ids2)
    for node_id in common_node_ids:
        print(node_id)
    assert len(common_node_ids) == 0, f'{m1.get_name()} contains {len(common_node_ids)} common node ids with {m2.get_name()}!'


def check_map_vs_region(m1: Map, r2: Region):
    node_ids1 = set(m1.get_all_node_ids())
    node_ids2 = set(r2.get_node_ids())
    common_node_ids = node_ids1.intersection(node_ids2)
    for node_id in common_node_ids:
        print(node_id)
    assert len(common_node_ids) == 0, f'{m1.get_name()} contains {len(common_node_ids)} common node ids with {r2.map.get_name()}.{r2.get_name()}!'


def check_dupe_node_ids(map_name: str):
    bits = Bits()
    m = bits.maps[map_name]

    # check for dupes within map itself
    check_map(m)

    # check for dupes with other maps
    for m2 in bits.maps.values():
        if m2 == m:
            continue
        check_map_vs_map(m, m2)

    print('All good.')


def main(argv):
    map_name = argv[0]
    check_dupe_node_ids(map_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
