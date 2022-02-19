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


def check_dupe_node_ids(map_name, other_map_names: list[str] = None):  # None means all
    bits = Bits()
    m = bits.maps[map_name]
    node_ids_list = m.get_all_node_ids()
    node_ids = set(node_ids_list)

    # check for dupes within map itself
    dupes = dupes_in_list(node_ids_list)
    if len(dupes) > 0:
        for node_id in dupes:
            print(node_id)
        assert False, map_name + ' contains duplicate node ids!'

    # check for dupes with other maps
    if other_map_names is None:
        other_map_names = list(bits.maps.keys())
        other_map_names.remove(map_name)
    for other_map_name in other_map_names:
        other_map = bits.maps[other_map_name]
        other_node_ids = set(other_map.get_all_node_ids())
        common_node_ids = node_ids.intersection(other_node_ids)
        if len(common_node_ids) > 0:
            for node_id in common_node_ids:
                print(node_id)
            assert False, map_name + ' contains ' + str(len(common_node_ids)) + ' common node ids with ' + other_map_name + '!'
    print('All good.')


def main(argv):
    map_name = argv[0]
    check_dupe_node_ids(map_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
