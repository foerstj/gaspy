import argparse
import sys

from bits.bits import Bits
from bits.maps.terrain import Terrain, TerrainNode
from gas.molecules import Hex


class NodeMetaData:
    def __init__(self, node: TerrainNode):
        self.node = node
        self.doors_to_target = None

    def get_str(self, what):
        if what == 'mesh_name':
            return self.node.mesh_name
        elif what == 'doors_to_target':
            return self.doors_to_target
        else:
            assert False, 'what'


class TerrainMetaData:
    def __init__(self, terrain: Terrain):
        self.terrain = terrain
        self.nodes: dict[Hex, NodeMetaData] = {node.guid: NodeMetaData(node) for node in terrain.nodes}
        self._calc_doors_to_target()

    def _calc_doors_to_target(self):
        seen_nodes = {self.terrain.target_node.guid}
        self.nodes[self.terrain.target_node.guid].doors_to_target = 0
        num_doors = 0
        x = True
        while x:
            x = False
            num_doors += 1
            nodes_at_curr_num_doors = set()
            for node in self.terrain.nodes:
                if node.guid in seen_nodes:
                    continue
                for neighbor in node.get_neighbors():
                    if neighbor.guid in seen_nodes:
                        nodes_at_curr_num_doors.add(node)
                        self.nodes[node.guid].doors_to_target = num_doors
                        x = True
                        break
            seen_nodes.update({n.guid for n in nodes_at_curr_num_doors})

    def print(self, what):
        self.terrain.print()
        print(f'Target Node: {self.terrain.target_node.guid}')
        for guid, nmd in self.nodes.items():
            print(f'{guid}: {nmd.get_str(what)}')


def terrain_layout(map_name, region_name, bits_path):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    terrain = region.get_terrain()
    tmd = TerrainMetaData(terrain)
    tmd.print('doors_to_target')


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
