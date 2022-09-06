import argparse
import random
import sys
import colorsys

from bits.bits import Bits
from bits.game_object import GameObject
from bits.light import PointLight, Color, Light
from bits.region import Region
from gas.molecules import Hex


# returns the ids of lights that are referenced by flickers = attached to lamps
def get_flicker_lights(region: Region) -> list[Hex]:
    region.load_objects()
    gos = region.objects_non_interactive
    region.objects_non_interactive = None
    region.gas_dir.clear_cache()
    flicker_lights = list()
    for go in gos:
        assert isinstance(go, GameObject)
        flicker_section = go.section.get_section('light_flicker_lightweight')
        if flicker_section is not None:
            light_id: Hex = flicker_section.get_attr_value('siege_light')
            flicker_lights.append(light_id)
    return flicker_lights


def invert_hues(lights: list[Light]):
    for light in lights:
        a, r, g, b = light.color.get_argb()
        r, g, b = [x / 255 for x in (r, g, b)]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h += 0.5
        if h > 1:
            h -= 1
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = [int(x * 255) for x in (r, g, b)]
        light.color = Color.from_argb(a, r, g, b)


# for mickeymouse lighting
def randomize_hues(lights: list[Light]):
    for light in lights:
        a, r, g, b = light.color.get_argb()
        r, g, b = [x / 255 for x in (r, g, b)]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h = random.random()  # random float between 0 and 1
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = [int(x * 255) for x in (r, g, b)]
        light.color = Color.from_argb(a, r, g, b)


# Brightens lights by doubling inner & outer radius
def brighten(lights: list[Light]):
    for light in lights:
        light.inner_radius *= 2
        light.outer_radius *= 2


# Makes lights blue by sorting r/g/b
def make_blue(lights: list[Light]):
    for light in lights:
        a, r, g, b = light.color.get_argb()
        r, g, b = sorted([r, g, b])
        light.color = Color.from_argb(a, r, g, b)


def edit_region_lights(region: Region, flickers: bool, edit: str):
    region.load_lights()
    lights = region.lights
    lights = [light for light in lights if isinstance(light, PointLight)]
    if not flickers:
        flicker_lights = get_flicker_lights(region)
        lights = [light for light in lights if light.id not in flicker_lights]
    if len(lights) == 0:
        print('No lights to edit')
        return

    if edit == 'invert-hues':
        invert_hues(lights)
    elif edit == 'brighten':
        brighten(lights)
    elif edit == 'make-blue':
        make_blue(lights)
    else:
        print('Invalid edit arg')
        return

    region.save()
    print('Region saved. Open in SE with "Full Region Recalculation".')


def edit_lights(bits: Bits, map_name: str, region_name: str, edit: str, flickers: bool):
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    edit_region_lights(region, flickers, edit)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy edit lights')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('edit', choices=['invert-hues', 'brighten', 'make-blue'])
    parser.add_argument('--flickers', required=False, action='store_true')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits = Bits(args.bits)
    edit_lights(bits, args.map, args.region, args.edit, args.flickers)


if __name__ == '__main__':
    main(sys.argv[1:])
