import os
import sys
from pathlib import Path

from bits import Bits
from gas import Hex


def inc_node_ids(map_name, region_name, inc=1):
    bits = Bits()
    m = bits.maps[map_name]

    # step 1: collect node ids and delete the terrain lnc file(s)
    if region_name is not None:
        region = m.get_region(region_name)
        node_ids = region.get_node_ids()
        lnc_file = os.path.join(region.gas_dir.get_subdir('terrain_nodes').path, 'siege_nodes.lnc')
        if os.path.isfile(lnc_file):
            os.remove(lnc_file)
    else:
        node_ids = m.get_all_node_ids()
        for region in m.get_regions().values():
            lnc_file = os.path.join(region.gas_dir.get_subdir('terrain_nodes').path, 'siege_nodes.lnc')
            if os.path.isfile(lnc_file):
                os.remove(lnc_file)

    # step 2: textually replace all node ids in all map files
    path_list = Path(m.gas_dir.path).rglob('*.gas')
    for path in path_list:
        print(path)
        with open(path) as map_gas_file:
            text = map_gas_file.read()
        text_pre = text
        for node_id in node_ids:
            new_node_id = Hex(node_id + inc)
            text = text.replace(node_id.to_str_lower(), new_node_id.to_str_lower())
            text = text.replace(node_id.to_str_upper(), new_node_id.to_str_upper())
        if text != text_pre:
            with open(path, 'w') as map_gas_file:
                map_gas_file.write(text)

    print('Done.')
    print('You have to open & save the converted region(s) in Siege Editor to complete the process.')


def main(argv):
    map_name = argv[0]
    region_name = argv[1] if len(argv) > 1 else None
    inc = int(argv[2]) if len(argv) > 2 else 1
    inc_node_ids(map_name, region_name, inc)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
