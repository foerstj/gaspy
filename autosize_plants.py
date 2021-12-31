import random
import sys

from bits import Bits
from region import GameObject, Region


def do_autosize_plants(objects_non_interactive: list[GameObject], overwrite, min_size, max_size, median_size=None):
    if median_size is None:
        median_size = (min_size + max_size) / 2
    assert min_size <= median_size <= max_size
    num_total = 0
    num_autosized = 0

    for i, go in enumerate(objects_non_interactive):
        if not go.template_name.startswith('tree_'):
            continue
        num_total += 1
        aspect = go.section.get_or_create_section('aspect')
        has_scale_multiplier = aspect.get_attr('scale_multiplier')
        if not has_scale_multiplier or overwrite:
            if random.getrandbits(1):
                scale_multiplier_value = random.uniform(min_size, median_size)
            else:
                scale_multiplier_value = random.uniform(median_size, max_size)
            # some templates actually set scale_multiplier wtf
            template_scale_multiplier = go.get_template().compute_value('aspect', 'scale_multiplier')
            if template_scale_multiplier is not None:
                scale_multiplier_value *= float(template_scale_multiplier)
            aspect.set_attr_value('scale_multiplier', scale_multiplier_value)
            num_autosized += 1
    return num_autosized, num_total


def autosize_plants_in_region(region: Region):
    region.load_objects()
    num_autosized, num_total = do_autosize_plants(region.objects_non_interactive, False, 0.8, 1.3, 1.0)
    if num_autosized > 0:
        region.store_objects()
        region.gas_dir.save()
    print(region.get_name() + ': ' + str(num_autosized) + ' / ' + str(num_total) + ' plants autosized')


def autosize_plants(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]
    print('autosize plants')
    if region_name:
        region = m.get_region(region_name)
        autosize_plants_in_region(region)
    else:
        for region_name, region in m.get_regions().items():
            autosize_plants_in_region(region)
    print('autosize plants done')


def main(argv):
    map_name = argv[0]
    region_name = argv[1] if len(argv) > 1 else None
    autosize_plants(map_name, region_name)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
