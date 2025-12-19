import argparse
import math

import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from gas.gas import Attribute
from gas.molecules import Hex, Position, Quaternion


def turn(x, z, angle):
    """
    :param x: x
    :param z: z
    :param angle: radian
    """
    xt = math.cos(angle) * x + math.sin(angle) * z
    zt = math.cos(angle) * z - math.sin(angle) * x
    return xt, zt


# Turn a game-object counter-clockwise around the node center
def turn_go_in_node(go: GameObject, angle: float, center_offset: tuple):
    placement_section = go.section.get_section('placement')
    pos_attr = placement_section.get_attr('position')
    assert pos_attr
    pos = pos_attr.value
    assert isinstance(pos, Position)
    ori_attr = placement_section.get_attr('orientation')
    if not ori_attr:
        ori_attr = Attribute('orientation', Quaternion.rad_to_quat(0), 'q')
        placement_section.items.append(ori_attr)
    ori = ori_attr.value
    assert isinstance(ori, Quaternion)

    x_offset, z_offset = center_offset
    x, z = turn(pos.x - x_offset, pos.z - z_offset, angle)
    pos = Position(x + x_offset, pos.y, z + z_offset, pos.node_guid)
    rad_quat = Quaternion.rad_to_quat(angle)
    ori = Quaternion.multiply(ori, rad_quat)

    pos_attr.value = pos
    ori_attr.value = ori


# Turn a node clockwise n times 90°
# Assumptions: node has equal 4 doors and coord center is geometrical center
def flip_node(region: Region, node_guid: Hex, num_turns: int):
    node = region.terrain.find_node(node_guid)
    assert node, node_guid
    center_offset = (0, 0) if node.mesh_name != "t_sea01_water" else (-8, -2)

    gos: list[GameObject] = list()
    for go_list in region.objects.get_objects_dict().values():
        for go in go_list:
            assert isinstance(go, GameObject)
            pos = go.get_own_value('placement', 'position')
            assert isinstance(pos, Position)
            if pos.node_guid == node_guid:
                gos.append(go)
    for go in gos:
        turn_go_in_node(go, num_turns * math.tau/4, center_offset)

    node_doors = dict(node.doors)
    for i in range(4):
        node_door_id = i + 1
        new_node_door_id = (i + num_turns) % 4 + 1
        new_connection = node_doors.get(new_node_door_id)
        if new_connection is not None:
            (new_neighbor, new_neighbor_door_id) = new_connection
            node.doors[node_door_id] = (new_neighbor, new_neighbor_door_id)
            new_neighbor.doors[new_neighbor_door_id] = (node, node_door_id)
        else:
            del node.doors[node_door_id]


def flip_nodes(map_name: str, region_name: str, node_guids: list[str], num_turns: int, bits_path: str):
    node_guids = [Hex.parse(guid) for guid in node_guids]
    bits = Bits(bits_path)
    region = bits.maps[map_name].get_region(region_name)
    region.print(info=None)
    region.load_terrain()
    region.objects.load_objects()
    region.terrain.print()

    for node_guid in node_guids:
        flip_node(region, node_guid, num_turns)
    region.terrain.check_consistent_door_connections()

    region.save()
    region.delete_lnc()
    print('Done!')
    print('Open & save in SE.')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy flip_nodes')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('nodes', nargs='+')
    parser.add_argument('--num-turns', type=int, default=0)
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    flip_nodes(args.map, args.region, args.nodes, args.num_turns, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
