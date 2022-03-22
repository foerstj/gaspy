import random
import sys
import colorsys

from bits.bits import Bits
from bits.game_object import GameObject
from bits.light import PointLight, Color, Light
from bits.region import Region


# returns the ids of lights that are referenced by flickers = attached to lamps
def get_flicker_lights(region: Region) -> list[Light]:
    region.load_objects()
    gos = region.objects_non_interactive
    region.objects_non_interactive = None
    region.gas_dir.clear_cache()
    flicker_lights = list()
    for go in gos:
        assert isinstance(go, GameObject)
        flicker_section = go.section.get_section('light_flicker_lightweight')
        if flicker_section is not None:
            light_id = flicker_section.get_attr_value('siege_light')
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


def brighten(lights: list[Light]):
    for light in lights:
        light.inner_radius *= 2
        light.outer_radius *= 2


def make_blue(lights: list[Light]):
    for light in lights:
        a, r, g, b = light.color.get_argb()
        r, g, b = sorted([r, g, b])
        light.color = Color.from_argb(a, r, g, b)


# Inverts hue of all point lights that are not attached to a lamp.
def edit_region_lights_invert_hues(region: Region):
    flicker_lights = get_flicker_lights(region)

    region.load_lights()
    lights = region.lights
    point_lights_no_flicker = [light for light in lights if isinstance(light, PointLight) and light.id not in flicker_lights]
    invert_hues(point_lights_no_flicker)
    return len(point_lights_no_flicker)


# brightens lights by doubling inner & outer radius
def edit_region_lights_brighten(region: Region):
    region.load_lights()
    lights = region.lights
    point_lights = [light for light in lights if isinstance(light, PointLight)]
    brighten(point_lights)
    return len(point_lights)


# brightens lights by doubling inner & outer radius
def edit_region_lights_make_blue(region: Region):
    flicker_lights = get_flicker_lights(region)

    region.load_lights()
    lights = region.lights
    point_lights_no_flicker = [light for light in lights if isinstance(light, PointLight) and light.id not in flicker_lights]
    make_blue(point_lights_no_flicker)
    return len(point_lights_no_flicker)


def edit_region_lights(region: Region):
    # num_edited_lights = edit_region_lights_invert_hues(region)
    # num_edited_lights = edit_region_lights_brighten(region)
    num_edited_lights = edit_region_lights_make_blue(region)
    print(f'Num edited lights: {num_edited_lights}')
    region.save()
    print('Region saved. Open in SE with "Full Region Recalculation".')


def edit_lights(map_name, region_name):
    bits = Bits()
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    edit_region_lights(region)


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    edit_lights(map_name, region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
