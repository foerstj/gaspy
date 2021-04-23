import sys

from bits import Bits


def dupes_in_list(the_list):
    seen = set()
    dupes = set()

    for x in the_list:
        if x not in seen:
            seen.add(x)
        else:
            dupes.add(x)
    return dupes


def check_dupe_node_ids(map_name):
    bits = Bits()
    m = bits.maps[map_name]
    node_ids_list = m.get_all_node_ids()
    node_ids = set(node_ids_list)
    dupes = dupes_in_list(node_ids_list)
    if len(dupes) > 0:
        for node_id in dupes:
            print(node_id)
        assert False, map_name + ' contains duplicate node ids!'
    for other_map_name, other_map in bits.maps.items():
        if other_map_name == map_name:
            continue
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
