import argparse
import sys

from bits.bits import Bits
from bits.maps.terrain import Terrain, TerrainNode
from gas.molecules import Hex


class NodeMetaData:
    def __init__(self, node: TerrainNode):
        self.node = node


class TerrainMetaData:
    def __init__(self, nodes: dict[Hex, NodeMetaData]):
        self.nodes = nodes

    def print(self):
        for guid, nmd in self.nodes.items():
            print(f'{guid}: {nmd.node.mesh_name}')


def calculate_meta_data(terrain: Terrain) -> TerrainMetaData:
    meta_data = dict()
    for node in terrain.nodes:
        meta_data[node.guid] = NodeMetaData(node)
    return TerrainMetaData(meta_data)


def terrain_layout(map_name, region_name, bits_path):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    terrain = region.get_terrain()
    terrain.print()
    tmd = calculate_meta_data(terrain)
    tmd.print()


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy terrain_layout')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--bits', default=None)
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    terrain_layout(args.map, args.region, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
