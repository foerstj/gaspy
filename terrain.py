import string
import random

from gas import Hex


def random_hex(length=8):
    return '0x' + ''.join([random.choice(string.digits + 'abcdef') for _ in range(length)])


class TerrainNode:
    def __init__(self, guid, mesh_name, texture_set):
        self.guid = guid
        self.mesh_name = mesh_name
        self.texture_set = texture_set
        self.doors: dict[int, (TerrainNode, int)] = dict()

    def connect_doors(self, my_door: int, far_node, far_door: int):
        self.doors[my_door] = (far_node, far_door)
        far_node.doors[far_door] = (self, my_door)


class Terrain:
    mesh_index_lookup = {
        't_xxx_flr_04x04-v0': 0x6a5
    }

    def __init__(self):
        self.nodes: list[TerrainNode] = []
        self.target_node = None

    def new_node_guid(self):
        guid = Hex.parse(random_hex())
        assert guid not in [n.guid for n in self.nodes]
        return guid

    def get_mesh_index(self):
        return {self.mesh_index_lookup[n.mesh_name]: n.mesh_name for n in self.nodes}
