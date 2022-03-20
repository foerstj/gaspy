import sys

from bits.bits import Bits
from bits.light import Light
from bits.region import Region


def do_edit_region_lights(lights: list[Light]):
    pass


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
