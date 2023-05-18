import os
import sys

from bits.bits import Bits
from bits.maps.map import Map


def rename_region_folder(m: Map, old_region_name: str, new_region_name: str):
    region = m.get_region(old_region_name)
    src_path = region.gas_dir.path
    dst_path = os.path.join(os.path.dirname(src_path), new_region_name)
    print('src: '+src_path)
    print('dst: '+dst_path)
    os.rename(src_path, dst_path)
    m.gas_dir.clear_cache()


def rename_region_refs_stitches(m: Map, old_region_name: str, new_region_name: str):
    regions = m.get_regions()
    for region_name, r in regions.items():
        stitch_helper_file = r.gas_dir.get_subdir('editor').get_gas_file('stitch_helper')
        stitch_helper_data = stitch_helper_file.get_gas().get_section('stitch_helper_data')
        if region_name == new_region_name:
            print(region_name + ' - the new region!')
            stitch_helper_data.set_attr_value('source_region_name', new_region_name)
        else:
            print(region_name)
            for section in stitch_helper_data.get_sections():
                t, n = section.get_t_n_header()
                assert t == 'stitch_editor', t
                if n == old_region_name:
                    section.set_t_n_header(t, new_region_name)
                    section.set_attr_value('dest_region', new_region_name)
        stitch_helper_file.save()


# Renames a region.
# 1. The region folder is renamed (duh)
# 2. References in stitch helper files are adapted
# TODO 3. references in quest convos
def rename_region(map_name, old_region_name, new_region_name):
    bits = Bits()
    assert map_name in bits.maps, map_name
    m = bits.maps[map_name]
    regions = m.get_regions()
    assert old_region_name in regions, old_region_name
    assert new_region_name not in regions, new_region_name

    rename_region_folder(m, old_region_name, new_region_name)

    rename_region_refs_stitches(m, old_region_name, new_region_name)


def main(argv):
    assert len(argv) == 3
    map_name = argv[0]
    old_region_name = argv[1]
    new_region_name = argv[2]
    rename_region(map_name, old_region_name, new_region_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
