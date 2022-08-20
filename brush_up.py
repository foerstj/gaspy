import sys

from bits.bits import Bits
from bits.game_object import GameObject
from bits.region import Region


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


def brush_up_plant(plant: GameObject):
    is_directional = startswith(plant.template_name, directional_plant_prefixes)
    is_directional_str = ' (directional)' if is_directional else ''
    print(f'  - {plant.object_id} {plant.template_name}{is_directional_str}')


def brush_up_region(r: Region):
    print(r.get_name())
    r.load_objects()
    for obj in r.objects_non_interactive:
        assert isinstance(obj, GameObject)
        if is_plant(obj):
            brush_up_plant(obj)


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
