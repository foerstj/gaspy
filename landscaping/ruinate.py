import argparse
import sys
from argparse import Namespace

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from gas.gas import Section
from gas.molecules import Hex


def rem_objs(objs: list[GameObject], match) -> int:
    objs_to_delete = list()
    for obj in objs:
        if match(obj):
            objs_to_delete.append(obj)
    for obj in objs_to_delete:
        objs.remove(obj)
    return len(objs_to_delete)


def ruinate_signs(region: Region, action: str) -> int:
    assert action in ['remove']
    num_signs = rem_objs(region.objects.objects_interactive, lambda x: x.template_name in ['sign_glb_01', 'sign_ice_01', 'sign_swp_01', 'sign_glb_dungeon_left', 'sign_glb_dungeon_right'])
    num_posts = rem_objs(region.objects.objects_non_interactive, lambda x: x.template_name in ['post_glb_01', 'post_ice_01', 'post_swp_01'])
    if num_signs + num_posts:
        print(f'  Removed {num_signs} signs and {num_posts} posts')
    return num_signs + num_posts


def ruinate_lightings(region: Region, lighting_type: str, action: str) -> int:
    templates = {
        'torches': ['torch_glb_stick'],
        'lamp posts': ['lamp_glb_post_03'],
        'candles': ['candle_glb_02']
    }
    assert lighting_type in templates
    assert action in ['remove', 'unlit', 'lightable']

    objs: list[GameObject] = region.objects.objects_non_interactive
    lightings = [obj for obj in objs if obj.template_name in templates[lighting_type]]
    light_ids: list[Hex] = list()
    for lighting in lightings:
        if action == 'remove':
            objs.remove(lighting)
        elif action == 'unlit':
            t, n = lighting.section.get_t_n_header()
            t += '_unlit'
            lighting.section.set_t_n_header(t, n)
        elif action == 'lightable':
            t, n = lighting.section.get_t_n_header()
            t += '_lightable'
            lighting.section.set_t_n_header(t, n)

        flicker = lighting.section.get_section('light_flicker_lightweight')
        if flicker is not None:
            if action != 'lightable':
                lighting.section.items.remove(flicker)
                light_id = flicker.get_attr_value('siege_light')
                if light_id:
                    light_ids.append(light_id)
            else:
                flicker.header = 'light_flicker'
                lighting.section.insert_item(Section('light_enable', [flicker.get_attr('siege_light').copy()]))

    what_done = 'Removed' if action == 'remove' else 'Replaced'
    if len(light_ids) == 0:
        if len(lightings) > 0:
            print(f'  {what_done} {len(lightings)} {lighting_type}')
    else:
        lights = region.get_lights()
        lights_to_delete = [light for light in lights if light.id in light_ids]
        if len(lights_to_delete) != len(light_ids):
            found_ids = set([light.id for light in lights_to_delete])
            not_found_ids = set(light_ids).difference(found_ids)
            not_found_ids = ', '.join([str(x) for x in not_found_ids])
            print(f'  Warning: Light IDs not found: {not_found_ids}')
        for light in lights_to_delete:
            lights.remove(light)
        region.delete_lnc()
        print(f'  {what_done} {len(lightings)} {lighting_type} and removed {len(lights_to_delete)} lights (lnc deleted)')

    return len(lightings)


def ruinate_region(region: Region, args: Namespace):
    print(region.get_name())
    region.objects.load_objects()
    changes = 0
    if args.signs:
        changes += ruinate_signs(region, args.signs)
    if args.torches:
        changes += ruinate_lightings(region, 'torches', args.torches)
    if args.lamp_posts:
        changes += ruinate_lightings(region, 'lamp posts', args.lamp_posts)
    if args.candles:
        changes += ruinate_lightings(region, 'candles', args.candles)
    if changes:
        region.save()


def ruinate(bits_path: str, map_name: str, region_names: list[str], args: Namespace):
    bits = Bits(bits_path)
    m = bits.maps[map_name]

    if len(region_names) > 0:
        for region_name in region_names:
            ruinate_region(m.get_region(region_name), args)
    else:
        for region in m.get_regions().values():
            ruinate_region(region, args)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Ruinate')
    parser.add_argument('map')
    parser.add_argument('region', nargs='*')
    parser.add_argument('--signs', choices=['remove'])
    parser.add_argument('--torches', choices=['remove', 'unlit', 'lightable'])
    parser.add_argument('--lamp-posts', choices=['remove', 'unlit'])
    parser.add_argument('--candles', choices=['remove'])
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    ruinate(args.bits, args.map, args.region, args)


if __name__ == '__main__':
    main(sys.argv[1:])
