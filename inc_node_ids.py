import sys
from pathlib import Path

from bits import Bits
from gas import Hex


def inc_node_ids(map_name, region_name):
    bits = Bits()
    region = bits.maps[map_name].get_region(region_name)
    region_dir = region.gas_dir.path
    node_ids = region.get_node_ids()
    pathlist = Path(region_dir).rglob('*.gas')
    for path in pathlist:
        print(path)
        with open(path) as region_file:
            text = region_file.read()
        for node_id in node_ids:
            new_node_id = Hex(node_id + 1)
            text = text.replace(node_id.to_str_lower(), new_node_id.to_str_lower())
            text = text.replace(node_id.to_str_upper(), new_node_id.to_str_upper())
        with open(path, 'w') as region_file:
            region_file.write(text)


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    inc_node_ids(map_name, region_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
