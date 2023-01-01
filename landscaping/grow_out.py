import argparse
import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode
from gas.molecules import Position
from landscaping.plant_gen import load_mesh_info, PlantableArea


def place_randomly(plant: GameObject, plantable_area: PlantableArea, node: TerrainNode, bits: Bits):
    sno = bits.snos.get_sno_by_name(node.mesh_name)
    x = y = z = None
    pos_found = False
    for n in range(16):
        x, y, z = plantable_area.random_position()
        assert sno.is_in_bounds(x, z), f'{x}|{y}|{z} not in {sno.bb_str(sno.sno.bounding_box)} bounds of {node.mesh_name}'
        pos_found = sno.is_in_floor(x, z)
        if pos_found:
            break
    if not pos_found:
        print(f'no pos found for {node.mesh_name}')
        return
    pos = Position(x, y, z, node.guid)
    plant.section.get_section('placement').set_attr_value('position', pos)


# plants that are placed on or in water
def is_water_plant(plant: GameObject) -> bool:
    water_plants = ['cattail', 'cress', 'lilypad', 'reed']
    # seaweed is technically also a "water plant" but it is placed lying on shores
    # if you used bush_swp_03 as a water plant, redefine a template starting with "cress" :P
    return plant.template_name.split('_')[0] in water_plants


def grow_out_region(region: Region, no_water_plants=False) -> int:
    print(region.get_name())
    region.objects.load_objects()
    plantable_areas = load_mesh_info()
    region.load_terrain()
    objs: list[GameObject] = region.objects.objects_non_interactive
    plants = [obj for obj in objs if obj.is_plant()]
    if no_water_plants:
        plants = [p for p in plants if not is_water_plant(p)]
    nodes = {n.guid: n for n in region.terrain.nodes}
    region.terrain = None  # don't try to save
    missing_meshes = set()
    changes = 0
    for plant in plants:
        pos: Position = plant.get_own_value('placement', 'position')
        node_id = pos.node_guid
        node: TerrainNode = nodes[node_id]
        if node.mesh_name not in plantable_areas:
            missing_meshes.add(node.mesh_name)
            continue
        plantable_area = plantable_areas[node.mesh_name]
        if not plantable_area:
            continue
        changes += 1
        place_randomly(plant, plantable_area, node, region.map.bits)
    print(f'Repositioned {changes} of {len(plants)} plants')
    #if changes:
    #    region.save()
    if len(missing_meshes) > 0:
        print('Warning: missing node meshes:')
        for missing_mesh in sorted(list(missing_meshes)):
            print(missing_mesh)
    return changes


def grow_out(bits_path: str, map_name: str, region_names: list[str], no_water_plants=False):
    bits = Bits(bits_path)
    m = bits.maps[map_name]

    if len(region_names) > 0:
        for region_name in region_names:
            grow_out_region(m.get_region(region_name), no_water_plants)
    else:
        for region in m.get_regions().values():
            grow_out_region(region, no_water_plants)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Grow Out')
    parser.add_argument('map')
    parser.add_argument('region', nargs='*')
    parser.add_argument('--no-water-plants', action='store_true')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    grow_out(args.bits, args.map, args.region, args.no_water_plants)


if __name__ == '__main__':
    main(sys.argv[1:])
