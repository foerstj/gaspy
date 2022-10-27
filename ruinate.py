import argparse
import sys
from argparse import Namespace

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from gas.molecules import Hex


def rem_objs(objs: list[GameObject], match) -> int:
    objs_to_delete = list()
    for obj in objs:
        if match(obj):
            objs_to_delete.append(obj)
    for obj in objs_to_delete:
        objs.remove(obj)
    return len(objs_to_delete)


def remove_signs(region: Region) -> int:
    num_signs = rem_objs(region.objects.objects_interactive, lambda x: x.template_name in ['sign_glb_01'])
    num_posts = rem_objs(region.objects.objects_non_interactive, lambda x: x.template_name in ['post_glb_01'])
    if num_signs + num_posts:
        print(f'Removed {num_signs} signs and {num_posts} posts')
    return num_signs + num_posts


def extinguish_torches(region: Region) -> int:
    objs: list[GameObject] = region.objects.objects_non_interactive
    torches = [obj for obj in objs if obj.template_name in ['torch_glb_stick']]
    light_ids: list[Hex] = list()
    for torch in torches:
        t, n = torch.section.get_t_n_header()
        t += '_unlit'
        torch.section.set_t_n_header(t, n)

        flicker = torch.section.get_section('light_flicker_lightweight')
        if flicker is not None:
            torch.section.items.remove(flicker)
            light_id = flicker.get_attr_value('siege_light')
            if light_id:
                light_ids.append(light_id)

    if len(light_ids) == 0:
        print(f'Replaced {len(torches)} torches')
    else:
        lights = region.get_lights()
        lights_to_delete = [light for light in lights if light.id in light_ids]
        assert len(lights_to_delete) == len(light_ids)
        for light in lights_to_delete:
            lights.remove(light)
        region.delete_lnc()
        print(f'Replaced {len(torches)} torches and removed {len(light_ids)} lights (lnc deleted)')

    return len(torches)


def ruin_region(region: Region, args: Namespace):
    region.objects.load_objects()
    changes = 0
    if args.remove_signs:
        changes += remove_signs(region)
    if args.extinguish_torches:
        changes += extinguish_torches(region)
    if changes:
        region.save()


def ruin(map_name: str, region_name: str, args: Namespace):
    bits = Bits()
    m = bits.maps[map_name]

    if region_name is not None:
        ruin_region(m.get_region(region_name), args)
    else:
        for region in m.get_regions().values():
            ruin_region(region, args)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Ruinate')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--remove-signs', action='store_true')
    parser.add_argument('--extinguish-torches', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    ruin(args.map, args.region, args)


if __name__ == '__main__':
    main(sys.argv[1:])
