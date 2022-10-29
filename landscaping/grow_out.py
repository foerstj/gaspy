import argparse
import random
import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode
from gas.molecules import Position, Hex
from landscaping.plant_gen import load_mesh_info, PlantableArea


def place_randomly(plant: GameObject, plantable_area: PlantableArea, node_id: Hex):
    x = random.uniform(plantable_area.x_min, plantable_area.x_max)
    z = random.uniform(plantable_area.z_min, plantable_area.z_max)
    y = plantable_area.y
    pos = Position(x, y, z, node_id)
    plant.section.get_section('placement').set_attr_value('position', pos)


def grow_out_region(region: Region):
    print(region.get_name())
    region.objects.load_objects()
    plantable_areas = load_mesh_info()
    region.load_terrain()
    objs: list[GameObject] = region.objects.objects_non_interactive
    plants = [obj for obj in objs if obj.is_plant()]
    nodes = {n.guid: n for n in region.terrain.nodes}
    for plant in plants:
        pos: Position = plant.get_own_value('placement', 'position')
        node_id = pos.node_guid
        node: TerrainNode = nodes[node_id]
        if node.mesh_name not in plantable_areas:
            print(f'Warning: missing node mesh {node.mesh_name}')
            continue
        plantable_area = plantable_areas[node.mesh_name]
        if not plantable_area:
            continue
        place_randomly(plant, plantable_area, node_id)


def grow_out(bits_path: str, map_name: str, region_name: str):
    bits = Bits(bits_path)
    m = bits.maps[map_name]

    if region_name is not None:
        grow_out_region(m.get_region(region_name))
    else:
        for region in m.get_regions().values():
            grow_out_region(region)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Ruinate')
    parser.add_argument('map')
    parser.add_argument('region', nargs='?')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    grow_out(args.bits, args.map, args.region)


if __name__ == '__main__':
    main(sys.argv[1:])
