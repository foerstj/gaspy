import argparse
import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.light import PointLight, PosDir
from gas.color import Color
from gas.molecules import Position, Hex


class LightFlickerTask:
    def __init__(self, template_names: list[str], color: Color, radius: (int, int)):
        self.template_names = template_names
        self.color = color
        self.radius = radius


def do_light_flickers(bits: Bits, map_name: str, region_name: str, tasks: list[LightFlickerTask], override: bool):
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
            assert oni.get_template().has_component('light_flicker_lightweight')
            if oni.compute_value('light_flicker_lightweight', 'siege_light'):
                if not override:
                    continue
                else:
                    old_light_id = oni.compute_value('light_flicker_lightweight', 'siege_light')
                    region.get_lights()
                    old_lights = [l for l in region.get_lights() if l.id == old_light_id]
                    assert len(old_lights) < 2
                    if len(old_lights) == 0:
                        print(f'Note: override: old light with id {old_light_id} of object {oni.template_name} {oni.object_id} does not exist')
                    else:
                        old_light = old_lights[0]
                        region.get_lights().remove(old_light)
            pos: Position = oni.get_own_value('placement', 'position')
            light = PointLight(Hex.random(), position=PosDir(pos.x, pos.y + 2, pos.z, pos.node_guid))
            light.color = task.color
            light.inner_radius = task.radius[0]
            light.outer_radius = task.radius[1]
            light.occlude_geometry = True
            light.draw_shadow = True
            region.get_lights().append(light)
            num_lights_added += 1
            oni.section.get_or_create_section('light_flicker_lightweight').set_attr_value('siege_light', light.id)
    print(f'Flicker lights added: {num_lights_added}')
    if num_lights_added:
        region.save()
        region.delete_lnc()


def light_flickers(bits_dir: str, map_name: str, region_name: str, task_args: list[str], override: bool):
    bits = Bits(bits_dir)
    tasks = list()
    for task_arg in task_args:
        templates, light_def = task_arg.split('=')
        templates = templates.split(',')
        light_def_parts = light_def.split(':')
        color = Color(Hex.parse(light_def_parts[0]))
        i_rad, o_rad = [float(x) for x in light_def_parts[1].split('-')] if len(light_def_parts) > 1 else (1, 4)
        tasks.append(LightFlickerTask(templates, color, (i_rad, o_rad)))
    do_light_flickers(bits, map_name, region_name, tasks, override)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy light_flickers')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--override', action='store_true')
    parser.add_argument('--add', nargs='+', help='--add crystals_cav_05,crystals_cav_09=0xff20ffff crystals_cav_06,crystals_cav_10=0xffff20ff')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    light_flickers(args.bits, args.map, args.region, args.add, args.override)


if __name__ == '__main__':
    main(sys.argv[1:])
