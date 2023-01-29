import argparse
import random
import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region


class Sizing:
    def __init__(self, sizing_str):
        self.sizes = [float(s) for s in sizing_str.split('-')]

    def __str__(self):
        return '-'.join([str(s) for s in self.sizes])

    def random(self) -> float:
        if len(self.sizes) == 0:
            return 1
        elif len(self.sizes) == 1:
            return self.sizes[0]
        else:
            part = random.randint(1, len(self.sizes) - 1)
            size_min = self.sizes[part - 1]
            size_max = self.sizes[part]
            return random.uniform(size_min, size_max)


def do_autosize_plants(objects_non_interactive: list[GameObject], template_prefix, overwrite, multiply, sizing: Sizing):
    print(f'autosizing {template_prefix} plants {sizing}')
    num_total = 0
    num_autosized = 0

    for i, go in enumerate(objects_non_interactive):
        if template_prefix is None:
            if not go.is_plant():
                continue
        else:
            if not go.template_name.startswith(template_prefix):
                continue
        num_total += 1
        aspect = go.section.get_or_create_section('aspect')
        has_scale_multiplier = aspect.get_attr('scale_multiplier')
        if not has_scale_multiplier or overwrite or multiply:
            scale_multiplier_value = sizing.random()
            # some templates actually set scale_multiplier wtf
            template_scale_multiplier = go.get_template().compute_value('aspect', 'scale_multiplier')
            if template_scale_multiplier is not None:
                scale_multiplier_value *= float(template_scale_multiplier)
            if multiply:
                scale_multiplier_value *= go.compute_value('aspect', 'scale_multiplier')
            aspect.set_attr_value('scale_multiplier', scale_multiplier_value)
            num_autosized += 1
    return num_autosized, num_total


def autosize_plants_in_region(region: Region, template_prefix, opts: dict):
    region.objects.load_objects()
    override = opts.get('override', False)
    multiply = opts.get('multiply', False)
    sizing = opts.get('sizing')
    num_autosized, num_total = do_autosize_plants(region.objects.objects_non_interactive, template_prefix, override, multiply, sizing)
    if num_autosized > 0:
        region.objects.store_objects()
        region.gas_dir.save()
    print(region.get_name() + ': ' + str(num_autosized) + ' / ' + str(num_total) + ' plants autosized')


def autosize_plants(map_name: str, region_names: list[str], plants: str, opts: dict, bits_dir: str = None):
    bits = Bits(bits_dir)
    m = bits.maps[map_name]
    print('autosize plants')
    if len(region_names) > 0:
        for region_name in region_names:
            region = m.get_region(region_name)
            autosize_plants_in_region(region, plants, opts)
    else:
        for region in m.get_regions().values():
            autosize_plants_in_region(region, plants, opts)
    print('autosize plants done')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy auto-size plants')
    parser.add_argument('map_name')
    parser.add_argument('region_names', nargs='*', help="region name; omit for all regions")
    parser.add_argument('--plants', default=None, help="non-interactive template prefix, e.g. 'tree_'. omit for all plants.")
    parser.add_argument('--bits', default='DSLOA')
    parser.add_argument('--override', action='store_true', help="override existing scale multipliers if present")
    parser.add_argument('--size', default='0.8-1.2', help="Fixed size, size range, or range with median")
    parser.add_argument('--multiply', action='store_true', help="apply as additional factor to existing size. implies --override.")
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    sizing = Sizing(args.size)
    opts = {'override': args.override, 'multiply': args.multiply, 'sizing': sizing}
    autosize_plants(args.map_name, args.region_names, args.plants, opts, args.bits)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
