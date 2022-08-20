import math
import sys
import random

from bits.bits import Bits
from bits.game_object import GameObject
from bits.region import Region
from gas.molecules import Quaternion


def is_plant(obj: GameObject):
    category_name = obj.compute_value(None, 'category_name')
    if category_name is None:
        return False
    category_name = category_name.strip('"')
    return category_name in ['foliage', 'bushes', 'trees', 'logs', 'grass', 'flowers']


directional_plant_prefixes = ['roots', 'tree_swp_dead', 'log_jng_mossy', 'bush_sea_cliff', 'ivy_grs', 'vine_jng']


def startswith(string: str, prefixes: list[str]):
    for prefix in prefixes:
        if string.startswith(prefix):
            return True
    return False


def brush_up_obj_scale(obj: GameObject) -> bool:
    if obj.get_own_value('aspect', 'scale_multiplier') is not None:
        return False
    new_scale_multiplier = random.uniform(0.8, 1.2)
    template_scale_multiplier = obj.compute_value('aspect', 'scale_multiplier')
    if template_scale_multiplier is not None:
        new_scale_multiplier *= float(template_scale_multiplier)
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
    is_directional = startswith(plant.template_name, directional_plant_prefixes)
    if not is_directional:
        changed |= brush_up_obj_orientation(plant)
    return changed


def brush_up_region(r: Region):
    r.load_objects()
    changed = 0
    for obj in r.objects_non_interactive:
        assert isinstance(obj, GameObject)
        if is_plant(obj):
            changed += brush_up_plant(obj)
    print(f'{r.get_name()}: {changed} plants changed')
    if changed:
        r.save()


def brush_up(map_name: str):
    bits = Bits()
    m = bits.maps[map_name]
    for r in m.get_regions().values():
        brush_up_region(r)


def main(argv):
    map_name = argv[0]
    brush_up(map_name)


if __name__ == '__main__':
    main(sys.argv[1:])
