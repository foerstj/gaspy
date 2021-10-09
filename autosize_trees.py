import random
import sys

from bits import Bits
from region import GameObject, Region


def do_autosize_trees(objects_non_interactive: list[GameObject], overwrite, min_size, max_size, median_size=None):
    if median_size is None:
        median_size = (min_size + max_size) / 2
    assert min_size <= median_size <= max_size

    for i, go in enumerate(objects_non_interactive):
        if not go.template_name.startswith('tree_'):
            continue
        aspect = go.section.get_or_create_section('aspect')
        has_scale_multiplier = aspect.get_attr('scale_multiplier')
        if not has_scale_multiplier or overwrite:
            if random.getrandbits(1):
                scale_multiplier_value = random.uniform(min_size, median_size)
            else:
                scale_multiplier_value = random.uniform(median_size, max_size)
            aspect.set_attr_value('scale_multiplier', scale_multiplier_value)


def autosize_trees_in_region(region: Region):
    region.load_objects()
    do_autosize_trees(region.objects_non_interactive, False, 0.8, 1.3, 1.0)
    region.store_objects()
    region.gas_dir.save()


def autosize_trees(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    autosize_trees_in_region(region)
    print('autosize trees done')


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    autosize_trees(map_name, region_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
