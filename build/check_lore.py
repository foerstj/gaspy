import sys

from bits.bits import Bits
from bits.maps.region import Region


def check_lore_in_region(region: Region, lore_keys: list[str]) -> set[str]:
    invalid_lore_keys = set()
    inventory_objects = region.objects.do_load_objects_inventory() or list()
    for obj in inventory_objects:
        lore_key = obj.compute_value('gui', 'lore_key')
        if lore_key and lore_key not in lore_keys:
            print(f'Invalid lore key in {region.get_name()} {obj.object_id}: {lore_key}')
            invalid_lore_keys.add(lore_key)
    return invalid_lore_keys


def check_lore(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    _map.load_lore()
    lore_keys = list(_map.lore.lore.keys())
    invalid_lore_keys = set()
    print(f'Checking lore keys in {map_name}...')
    for region in _map.get_regions().values():
        region_invalid_lore_keys = check_lore_in_region(region, lore_keys)
        invalid_lore_keys.update(region_invalid_lore_keys)
    print(f'Checking lore keys in {map_name}: {len(invalid_lore_keys)} distinct invalid lore keys')
    return len(invalid_lore_keys) == 0


def main(argv) -> int:
    map_name = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    valid = check_lore(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
