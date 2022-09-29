import math
import sys
import random

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from gas.molecules import Quaternion


directional_plants = ['roots', 'tree_swp_dead', 'log_jng_mossy', 'cliff', 'ivy', 'vine', 'leaning', 'tree_grs_sequoia_03', 'uproot', 'tree_jng_willow_01']


def contains(string: str, substrings: list[str]):
    for substring in substrings:
        if substring in string:
            return True
    return False


def brush_up_obj_scale(obj: GameObject) -> bool:
    if obj.get_own_value('aspect', 'scale_multiplier') is not None:
        return False
    new_scale_multiplier = random.uniform(0.8, 1.2)
    template_scale_multiplier = obj.compute_value('aspect', 'scale_multiplier')
    if template_scale_multiplier is not None:
        new_scale_multiplier *= float(template_scale_multiplier)
    new_scale_multiplier = float(f'{new_scale_multiplier:.5f}')  # limit to 5 decimals to generate less diff on saving with SE
    obj.section.get_or_create_section('aspect').set_attr_value('scale_multiplier', new_scale_multiplier)
    return True


def is_square_orientation(orientation: Quaternion) -> bool:
    for turns in range(4):
        rad = turns*math.tau/4
        rad_ori = Quaternion.rad_to_quat(rad)
        if orientation.equals(rad_ori):
            # print('square orientation found!')
            return True
    return False


def brush_up_obj_orientation(obj: GameObject) -> bool:
    obj_orientation = obj.get_own_value('placement', 'orientation')
    if obj_orientation is not None:
        obj_orientation = Quaternion.parse(obj_orientation)
        if not is_square_orientation(obj_orientation):
            return False
    new_orientation = random.uniform(0, math.tau)
    obj.section.get_section('placement').set_attr_value('orientation', Quaternion.rad_to_quat(new_orientation))
    return True


def brush_up_plant(plant: GameObject) -> bool:
    changed = False
    changed |= brush_up_obj_scale(plant)
    is_directional = contains(plant.template_name, directional_plants)
    if not is_directional:
        changed |= brush_up_obj_orientation(plant)
    return changed


def brush_up_region(r: Region):
    r.objects.load_objects()
    changed = 0
    for obj in r.objects.objects_non_interactive:
        assert isinstance(obj, GameObject)
        if obj.is_plant():
            changed += brush_up_plant(obj)
    print(f'{r.get_name()}: {changed} plants changed')
    if changed:
        r.save()


def brush_up(map_name: str, region_name: str):
    bits = Bits()
    m = bits.maps[map_name]
    if region_name is not None:
        r = m.get_region(region_name)
        brush_up_region(r)
    else:
        for r in m.get_regions().values():
            brush_up_region(r)


def main(argv):
    map_name = argv[0]
    region_name = argv[1] if len(argv) > 1 else None
    brush_up(map_name, region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
