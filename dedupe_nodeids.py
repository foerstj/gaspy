import os
import sys
from pathlib import Path

from bits import Bits
from gas import Hex


def dedupe_nodeids(map_name, region_name, dupes_filepath):
    bits = Bits()
    region = bits.maps[map_name].get_region(region_name)
    region_dir = region.gas_dir.path
    with open(dupes_filepath) as dupes_file:
        dupes = [Hex.parse(dupe_line[:-1]) for dupe_line in dupes_file]
    pathlist = Path(region_dir).rglob('*.gas')
    for path in pathlist:
        with open(path) as region_file:
            text = region_file.read()
        for dupe in dupes:
            print(str(dupe))
            new_guid = Hex(dupe + 1)
            text = text.replace(dupe.to_str_lower(), new_guid.to_str_lower())
            text = text.replace(dupe.to_str_upper(), new_guid.to_str_upper())
        with open(path, 'w') as region_file:
            region_file.write(text)


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    dupes_filepath = argv[2]
    dedupe_nodeids(map_name, region_name, dupes_filepath)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
