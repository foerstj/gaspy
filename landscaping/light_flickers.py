import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.light import PointLight, PosDir
from gas.color import Color
from gas.molecules import Position, Hex


class LightFlickerTask:
    def __init__(self, template_names: list[str], color: Color):
        self.template_names = template_names
        self.color = color


def light_flickers(map_name: str, region_name: str, tasks: list[LightFlickerTask]):
    bits = Bits()
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    region.objects.load_objects()
    onis = region.objects.objects_non_interactive
    num_lights_added = 0
    for task in tasks:
        for oni in onis:
            assert isinstance(oni, GameObject)
            if oni.template_name not in task.template_names:
                continue
            if not oni.get_template().has_component('light_flicker_lightweight'):
                continue
            if oni.compute_value('light_flicker_lightweight', 'siege_light'):
                continue
            pos: Position = oni.get_own_value('placement', 'position')
            light = PointLight(Hex.random(), position=PosDir(pos.x, pos.y + 2, pos.z, pos.node_guid))
            light.color = task.color
            light.inner_radius = 1
            light.outer_radius = 3
            light.occlude_geometry = True
            light.draw_shadow = True
            region.get_lights().append(light)
            num_lights_added += 1
            oni.section.get_or_create_section('light_flicker_lightweight').set_attr_value('siege_light', light.id)
    if num_lights_added:
        region.save()
        region.delete_lnc()


def main(argv):
    tasks = [
        LightFlickerTask(['crystals_cav_01_x2', 'crystals_cav_05_x2', 'crystals_cav_09_x2', 'crystals_cav_13_x2'], Color.from_argb(255, 32, 255, 255)),  # teal
        LightFlickerTask(['crystals_cav_02_x2', 'crystals_cav_06_x2', 'crystals_cav_10_x2', 'crystals_cav_14_x2'], Color.from_argb(255, 255, 32, 255)),  # purple
        LightFlickerTask(['crystals_cav_03_x2', 'crystals_cav_07_x2', 'crystals_cav_11_x2', 'crystals_cav_15_x2'], Color.from_argb(255, 32, 255, 32)),  # green
        LightFlickerTask(['crystals_cav_04_x2', 'crystals_cav_08_x2', 'crystals_cav_12_x2', 'crystals_cav_16_x2'], Color.from_argb(255, 32, 32, 255)),  # blue
    ]
    light_flickers('collab24', '3_2_crystlayer', tasks)


if __name__ == '__main__':
    main(sys.argv[1:])
