import sys
import colorsys

from bits.bits import Bits
from bits.light import Light, PointLight, Color
from bits.region import Region


def do_edit_region_lights(lights: list[Light]):
    for light in lights:
        if isinstance(light, PointLight):
            a, r, g, b = light.color.get_argb()
            r, g, b = [x/255 for x in (r, g, b)]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            h += 0.5
            if h > 1:
                h -= 1
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = [int(x*255) for x in (r, g, b)]
            light.color = Color.from_argb(a, r, g, b)


def edit_region_lights(region: Region):
    region.load_lights()
    lights = region.lights
    do_edit_region_lights(lights)
    region.save()


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
