import sys

from bits import Bits


def check_dupe_node_ids(map_name):
    bits = Bits()
    m = bits.maps[map_name]
    node_ids_list = m.get_all_node_ids()
    node_ids = set(node_ids_list)
    assert len(node_ids) == len(node_ids_list), map_name + ' contains duplicate node ids!'
    # TODO other maps
    print('All good.')


def main(argv):
    map_name = argv[0]
    check_dupe_node_ids(map_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
