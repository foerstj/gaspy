import argparse

import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode
from gas.molecules import Hex, Position


def split_node(region: Region, node_guid: Hex):
    node = region.terrain.find_node(node_guid)
    assert node, node_guid
    assert node.mesh_name == 't_xxx_flr_08x08-v0', node.mesh_name
    node_xnzn = TerrainNode(region.terrain.new_node_guid(), 't_xxx_flr_04x04-v0', node.texture_set)
    node_xpzn = TerrainNode(region.terrain.new_node_guid(), 't_xxx_flr_04x04-v0', node.texture_set)
    node_xnzp = TerrainNode(region.terrain.new_node_guid(), 't_xxx_flr_04x04-v0', node.texture_set)
    node_xpzp = TerrainNode(region.terrain.new_node_guid(), 't_xxx_flr_04x04-v0', node.texture_set)

    gos: list[GameObject] = list()
    for go_list in region.objects.get_objects_dict().values():
        for go in go_list:
            assert isinstance(go, GameObject)
            pos = go.get_own_value('placement', 'position')
            assert isinstance(pos, Position)
            if pos.node_guid == node_guid:
                gos.append(go)
    for go in gos:
        pos_attr = go.section.get_section('placement').get_attr('position')
        assert pos_attr
        pos = pos_attr.value
        assert isinstance(pos, Position)
        if pos.x > 0:
            if pos.z > 0:
                pos.x -= 2
                pos.z -= 2
                pos.node_guid = node_xpzp.guid
            else:
                pos.x -= 2
                pos.z += 2
                pos.node_guid = node_xpzn.guid
        else:
            if pos.z > 0:
                pos.x += 2
                pos.z -= 2
                pos.node_guid = node_xnzp.guid
            else:
                pos.x += 2
                pos.z += 2
                pos.node_guid = node_xnzn.guid

    door_replace = {
        1: (node_xpzn, 1),
        2: (node_xnzn, 1),
        3: (node_xnzn, 2),
        4: (node_xnzp, 2),
        5: (node_xnzp, 3),
        6: (node_xpzp, 3),
        7: (node_xpzp, 4),
        8: (node_xpzn, 4)
    }
    for node_door_id, (new_node, new_node_door_id) in door_replace.items():
        (neighbor, neighbor_door_id) = node.doors[node_door_id]
        neighbor.doors[neighbor_door_id] = (new_node, new_node_door_id)
        new_node.doors[new_node_door_id] = (neighbor, neighbor_door_id)
    door_connect = [
        (node_xnzn, 4, node_xpzn, 2),
        (node_xnzn, 3, node_xnzp, 1),
        (node_xpzn, 3, node_xpzp, 1),
        (node_xnzp, 4, node_xpzp, 2)
    ]
    for node_a, door_a, node_b, door_b in door_connect:
        node_a.doors[door_a] = (node_b, door_b)
        node_b.doors[door_b] = (node_a, door_a)
    region.terrain.nodes.remove(node)
    region.terrain.nodes.extend([node_xnzn, node_xnzp, node_xpzn, node_xpzp])


def split_nodes(map_name: str, region_name: str, node_guids: list[str], bits_path: str):
    node_guids = [Hex.parse(guid) for guid in node_guids]
    bits = Bits(bits_path)
    region = bits.maps[map_name].get_region(region_name)
    region.print(info=None)
    region.load_terrain()
    region.objects.load_objects()
    region.terrain.print()

    for node_guid in node_guids:
        split_node(region, node_guid)

    region.save()
    region.delete_lnc()
    print('Done!')
    print('Open & save in SE.')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy split_nodes')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('nodes', nargs='+')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    split_nodes(args.map, args.region, args.nodes, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
