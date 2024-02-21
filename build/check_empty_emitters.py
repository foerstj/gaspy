import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region


GENERIC_EFFECTS = [
    'geyser',
    'geyser_red',
    'geyser_white',
    'geyser_green',
    'geyser_orange',
    'geyser_dorange',
    'geyser_yellow',
    'geyser_purple',
    'geyser_drizzle',
    'geyser_drizzle_red',
    'geyser_drizzle_white',
    'geyser_drizzle_green',
    'geyser_drizzle_orange',
    'geyser_drizzle_dorange',
    'geyser_drizzle_yellow',
    'geyser_drizzle_purple',
    'water_splash',
    'water_wave',
    'ice_explosion',
    'dust_explosion',
    'dust_explosion_small',
    'generic_explosion',
    'coil_explosion',
    'barrel_explosion',
    'pebbles',
    'pebbles_directional',
    'swamp_gas_puff',
]


def check_empty_emitters_in_region(region: Region):
    num_empty_emitters = 0
    emitters = region.objects.do_load_objects_emitter()
    if emitters is None:
        return num_empty_emitters
    for emitter in emitters:
        if emitter.get_template().has_component('generic_emitter'):
            has_effect = emitter.compute_value('generic_emitter', 'other_effect') is not None
            for generic_effect_name in GENERIC_EFFECTS:
                has_effect |= emitter.compute_value('generic_emitter', generic_effect_name) is not None
            if not has_effect:
                print(f'  Empty emitter in region {region.get_name()}: {emitter.template_name} {emitter.object_id}')
                num_empty_emitters += 1
    return num_empty_emitters


def check_empty_emitters(bits: Bits, map_name: str):
    m = bits.maps[map_name]
    num_empty_emitters = 0
    print(f'Checking empty emitters in {map_name}...')
    for region in m.get_regions().values():
        num_empty_emitters += check_empty_emitters_in_region(region)
    print(f'Checking empty emitters in {map_name}: {num_empty_emitters} empty emitters')
    return num_empty_emitters == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_empty_emitters')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    map_name = args.map
    bits_path = args.bits
    bits = Bits(bits_path)
    valid = check_empty_emitters(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
