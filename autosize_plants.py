import argparse
import random
import sys

from bits.bits import Bits
from bits.game_object import GameObject
from bits.region import Region


def do_autosize_plants(objects_non_interactive: list[GameObject], template_prefix, overwrite, min_size, max_size, median_size=None):
    if median_size is None:
        median_size = (min_size + max_size) / 2
    assert min_size <= median_size <= max_size
    num_total = 0
    num_autosized = 0

    for i, go in enumerate(objects_non_interactive):
        if not go.template_name.startswith(template_prefix + '_'):
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


def autosize_plants_in_region(region: Region, template_prefix, opts: dict):
    region.load_objects()
    override = opts.get('override', False)
    min_size = opts.get('min_size', 0.8)
    max_size = opts.get('max_size', 1.3)
    med_size = opts.get('med_size', 1.0)
    assert min_size < max_size
    if med_size is not None:
        assert min_size < med_size < max_size
    num_autosized, num_total = do_autosize_plants(region.objects_non_interactive, template_prefix, override, min_size, max_size, med_size)
    if num_autosized > 0:
        region.store_objects()
        region.gas_dir.save()
    print(region.get_name() + ': ' + str(num_autosized) + ' / ' + str(num_total) + ' plants autosized')


def autosize_plants(map_name, region_name, plants, opts, bits_dir=None):
    bits = Bits(bits_dir)
    m = bits.maps[map_name]
    print('autosize plants')
    if region_name:
        region = m.get_region(region_name)
        autosize_plants_in_region(region, plants, opts)
    else:
        for region_name, region in m.get_regions().items():
            autosize_plants_in_region(region, plants, opts)
    print('autosize plants done')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy auto-size plants')
    parser.add_argument('map_name')
    parser.add_argument('region_name', nargs='?', default=None, help="region name; omit for all regions")
    parser.add_argument('--plants', choices=['tree', 'bush', 'mushroom', 'mushrooms'], default='tree', help="template prefix")
    parser.add_argument('--bits', default='DSLOA')
    parser.add_argument('--override', action='store_true', help="override existing scale multipliers if present")
    parser.add_argument('--min-size', default=0.8)
    parser.add_argument('--max-size', default=1.3)
    parser.add_argument('--med-size', default=1.0, help="median size; half of plants will be between min & med, other half between med & max")
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    opts = {'override': args.override, 'min_size': args.min_size, 'max_size': args.max_size, 'med_size': args.med_size}
    autosize_plants(args.map_name, args.region_name, args.plants, opts, args.bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
