import argparse
import math
import sys

from bits.bits import Bits
from bits.maps.game_object_data import GameObjectData, Common, Placement
from bits.maps.region import Region
from bits.maps.terrain import Terrain, TerrainNode
from bits.snos import SNOs
from gas.molecules import Hex, Position, Quaternion
from sno.sno import Sno
from sno.sno_handler import SnoHandler


def compare_v3(v3: Sno.V3, x, y, z):
    return v3.x == x and v3.y == y and v3.z == z


def get_xyz_angle(x, y, z):
    assert y == 0
    return math.atan2(-z, x) / math.tau


def get_door_angle(door: Sno.Door):
    assert compare_v3(door.y_axis, 0, 1, 0)
    if compare_v3(door.x_axis, 1, 0, 0) and compare_v3(door.z_axis, 0, 0, 1):
        angle = 0
    elif compare_v3(door.x_axis, -1, 0, 0) and compare_v3(door.z_axis, 0, 0, -1):
        angle = 0.5
    elif compare_v3(door.x_axis, 0, 0, -1) and compare_v3(door.z_axis, 1, 0, 0):
        angle = 0.25
    elif compare_v3(door.x_axis, 0, 0, 1) and compare_v3(door.z_axis, -1, 0, 0):
        angle = 0.75
    else:
        assert False, 'Unexpected Angle'
    return angle


def door_str(door: Sno.Door):
    return f'{door.id} {SnoHandler.v3_str(door.center)} {SnoHandler.v3_str(door.x_axis)} {SnoHandler.v3_str(door.y_axis)} {SnoHandler.v3_str(door.z_axis)}'


class NodeMetaData:
    def __init__(self, node: TerrainNode, sno: SnoHandler):
        self.node = node
        self.sno = sno

        self.parent: NodeMetaData or None = None
        self.children: list[NodeMetaData] = list()

    def get_num_doors_to_target(self):
        if self.parent is None:
            return 0
        return self.parent.get_num_doors_to_target() + 1

    def get_door(self, door_id):
        for door in self.sno.sno.door_array:
            if door.id == door_id:
                return door

    def get_door_to_neighbor(self, neighbor: 'NodeMetaData'):
        for my_door_id, (neighbor_node, neighbor_door_id) in self.node.doors.items():
            if neighbor_node == neighbor.node:
                return self.get_door(my_door_id), neighbor.get_door(neighbor_door_id)

    def get_absolute_orientation(self) -> float:
        if self.parent is None:
            return 0
        pao = self.parent.get_absolute_orientation()
        my_door, parent_door = self.get_door_to_neighbor(self.parent)
        my_door_angle = get_door_angle(my_door)
        parent_door_angle = get_door_angle(parent_door)
        ao = pao + parent_door_angle + 0.5 - my_door_angle
        return ao % 1

    def get_str(self, what):
        if what == 'mesh_name':
            return self.node.mesh_name
        elif what == 'num_doors_to_target':
            return self.get_num_doors_to_target()
        elif what == 'sno':
            return ', '.join([door_str(d) for d in self.sno.sno.door_array])
        elif what == 'absolute_orientation':
            return self.get_absolute_orientation()
        else:
            assert False, 'what'

    def print_tree(self, what, indent: int = 0):
        indentation = '  ' * indent
        print(f'{indentation}{self.node.guid} {self.get_str(what)}')
        for child in self.children:
            child.print_tree(what, indent + 1)


class TerrainMetaData:
    def __init__(self, terrain: Terrain, snos: SNOs):
        self.terrain = terrain
        self.nodes: dict[Hex, NodeMetaData] = {node.guid: NodeMetaData(node, snos.get_sno_by_name(node.mesh_name)) for node in terrain.nodes}
        self._build_target_tree()

    def _build_target_tree(self):
        seen_nodes = {self.terrain.target_node.guid}
        self.nodes[self.terrain.target_node.guid].parent = None
        x = True
        while x:
            x = False
            nodes_at_curr_num_doors = set()
            for node in self.terrain.nodes:
                if node.guid in seen_nodes:
                    continue
                for neighbor in node.get_neighbors():
                    if neighbor.guid in seen_nodes:
                        nodes_at_curr_num_doors.add(node)
                        self.nodes[node.guid].parent = self.nodes[neighbor.guid]
                        self.nodes[neighbor.guid].children.append(self.nodes[node.guid])
                        x = True
                        break
            seen_nodes.update({n.guid for n in nodes_at_curr_num_doors})

    def print_nodes(self, what):
        self.terrain.print()
        print(f'Target Node: {self.terrain.target_node.guid}')
        for guid, nmd in self.nodes.items():
            print(f'{guid}: {nmd.get_str(what)}')

    def print_tree(self, what):
        target = self.nodes[self.terrain.target_node.guid]
        target.print_tree(what)


def add_signs_pointing_north(tmd: TerrainMetaData, region: Region):
    region.objects.generated_objects = list()
    x, y, z = region.get_north_vector()
    north_angle = get_xyz_angle(x, y, z) % 1
    for node in tmd.nodes.values():
        obj = GameObjectData('sign_glb_01')
        obj.placement = Placement(Position(0, 0, 0, node.node.guid))
        abs_ori = node.get_absolute_orientation()
        obj.placement.orientation = Quaternion.rad_to_quat((-abs_ori + 0.25 + north_angle) * math.tau)  # 0.25 is specific for sign_glb_01
        region.objects.generated_objects.append(obj)
    region.save()


def terrain_layout(map_name, region_name, bits_path, node_bits_path):
    bits = Bits(bits_path)
    node_bits = bits if node_bits_path is None else Bits(node_bits_path)
    m = bits.maps[map_name]
    region = m.get_region(region_name)
    terrain = region.get_terrain()
    tmd = TerrainMetaData(terrain, node_bits.snos)
    tmd.print_tree('absolute_orientation')
    add_signs_pointing_north(tmd, region)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy terrain_layout')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--node-bits', default=None)
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    terrain_layout(args.map, args.region, args.bits, args.node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
