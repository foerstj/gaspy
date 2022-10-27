import argparse
import sys
from argparse import Namespace

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from gas.molecules import Hex


def rem_objs(objs: list[GameObject], match) -> bool:
    objs_to_delete = list()
    for obj in objs:
        if match(obj):
            objs_to_delete.append(obj)
    for obj in objs_to_delete:
        objs.remove(obj)
    return len(objs_to_delete) > 0


def remove_signs(region: Region) -> bool:
    changed = False
    changed |= rem_objs(region.objects.objects_interactive, lambda x: x.template_name in ['sign_glb_01'])
    changed |= rem_objs(region.objects.objects_non_interactive, lambda x: x.template_name in ['post_glb_01'])
    return changed


def extinguish_torches(region: Region) -> bool:
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

    if len(light_ids) > 0:
        lights = region.get_lights()
        lights_to_delete = [light for light in lights if light.id in light_ids]
        for light in lights_to_delete:
            lights.remove(light)
        if len(lights_to_delete) > 0:
            region.delete_lnc()

    return len(torches) > 0


def ruin_region(region: Region, args: Namespace):
    region.objects.load_objects()
    changed = False
    if args.remove_signs:
        changed |= remove_signs(region)
    if args.extinguish_torches:
        changed |= extinguish_torches(region)
    if changed:
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
