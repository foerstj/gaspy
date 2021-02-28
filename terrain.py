import string
import random

from gas import Hex


def random_hex(length=8):
    return '0x' + ''.join([random.choice(string.digits + 'abcdef') for _ in range(length)])


class AmbientLight:
    def __init__(self, color: Hex = 0xffffffff, intensity: float = 1, object_color: Hex = 0xffffffff, object_intensity: float = 1, actor_color: Hex = 0xffffffff, actor_intensity: float = 1):
        self.color = color
        self.intensity = intensity
        self.object_color = object_color
        self.object_intensity = object_intensity
        self.actor_color = actor_color
        self.actor_intensity = actor_intensity


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
        self.ambient_light = AmbientLight()

    def new_node_guid(self):
        guid = Hex.parse(random_hex())
        assert guid not in [n.guid for n in self.nodes]
        return guid

    def get_mesh_index(self):
        return {self.mesh_index_lookup[n.mesh_name]: n.mesh_name for n in self.nodes}
