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
    def __init__(self, guid, mesh_name, texture_set='grs01'):
        self.guid = guid
        self.mesh_name = mesh_name
        self.texture_set = texture_set
        self.doors: dict[int, (TerrainNode, int)] = dict()  # dict: door-id -> tuple(far-node, far-door-id)

    def connect_doors(self, my_door: int, far_node, far_door: int):
        if my_door is None or far_door is None:
            assert my_door is None and far_door is None
        elif my_door in self.doors:
            assert self.doors[my_door] == (far_node, far_door)
            assert far_node.doors[far_door] == (self, my_door)
        else:
            self.doors[my_door] = (far_node, far_door)
            far_node.doors[far_door] = (self, my_door)


class Terrain:
    mesh_index_lookup = {
        # xxx
        't_xxx_cnr_04-ccav': 0x53f,
        't_xxx_cnr_04-cnvx': 0x540,
        't_xxx_cnr_08-ccav': 0x541,
        't_xxx_cnr_08-cnvx': 0x542,
        't_xxx_cnr_12-ccav': 0x543,
        't_xxx_cnr_12-cnvx': 0x544,
        't_xxx_cnr_tee-04-04-08-l': 0x55b,
        't_xxx_cnr_tee-04-04-08-r': 0x55c,
        't_xxx_cnr_tee-04-08-12-l': 0x55d,
        't_xxx_cnr_tee-04-08-12-r': 0x55e,
        't_xxx_cnr_tee-08-04-12-l': 0x55f,
        't_xxx_cnr_tee-08-04-12-r': 0x560,

        't_xxx_flr_04x04-v0': 0x6a5,
        't_xxx_flr_04x08-v0': 0x6a9,
        't_xxx_flr_08x08-v0': 0x6aa,

        't_xxx_wal_04-thin': 0x9fb,
        't_xxx_wal_08-thin': 0xa10,
        't_xxx_wal_12-thin': 0xa26,

        # dc01
        't_dc01_dunes-32x32-a': 0x17f,
        't_dc01_dunes-32x32-b': 0x180,
        't_dc01_dunes-32x32-crest-a': 0x181,
        't_dc01_dunes-32x32-dip-a': 0x182,
        't_dc01_dunes-64x64-a': 0x18d,
    }

    @classmethod
    def reverse_mesh_index_lookup(cls):
        return {v: k for k, v in cls.mesh_index_lookup.items()}

    def __init__(self, target_node: TerrainNode = None):
        self.nodes: list[TerrainNode] = []
        self.target_node = target_node
        self.ambient_light = AmbientLight()

    def new_node_guid(self):
        guid = Hex.parse(random_hex())
        assert guid not in [n.guid for n in self.nodes]
        return guid

    def get_mesh_index(self):
        return {self.mesh_index_lookup[n.mesh_name]: n.mesh_name for n in self.nodes}

    def print(self):
        print('Terrain (' + str(len(self.nodes)) + ' nodes)')
