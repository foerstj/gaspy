from typing import Optional

from gas.gas import Hex


class AmbientLight:
    def __init__(self, color: Hex = 0xffffffff, intensity: float = 1, object_color: Hex = 0xffffffff, object_intensity: float = 1, actor_color: Hex = 0xffffffff, actor_intensity: float = 1):
        self.terrain_color = color
        self.terrain_intensity = intensity
        self.object_color = object_color
        self.object_intensity = object_intensity
        self.actor_color = actor_color
        self.actor_intensity = actor_intensity


class TerrainNode:
    def __init__(self, guid: Hex, mesh_name: str, texture_set=None):
        self.guid = guid
        self.mesh_name = mesh_name
        self.texture_set = texture_set if texture_set is not None else 'grs01'
        self.doors: dict[int, (TerrainNode, int)] = dict()  # dict: door-id -> tuple(far-node, far-door-id)
        self.section = 1
        self.level = -1
        self.object = -1
        self.bounds_camera = True
        self.camera_fade = False
        self.occludes_camera = False
        self.occludes_light = True

    def connect_doors(self, my_door: int, far_node, far_door: int):
        if my_door is None or far_door is None:
            assert my_door is None and far_door is None
        elif my_door in self.doors:
            assert self.doors[my_door] == (far_node, far_door)
            assert far_node.doors[far_door] == (self, my_door)
        else:
            self.doors[my_door] = (far_node, far_door)
            far_node.doors[far_door] = (self, my_door)

    def get_neighbors(self) -> set['TerrainNode']:
        door_cons = self.doors.values()
        neighbors = [door_con[0] for door_con in door_cons if door_con]
        neighbors = {n for n in neighbors if n}
        return neighbors


class Terrain:
    def __init__(self, target_node: TerrainNode = None, nodes: list[TerrainNode] = None):
        self.target_node = target_node
        if nodes is None:
            nodes = []
            if target_node is not None:
                nodes.append(target_node)
        if target_node is not None:
            assert target_node in nodes
        self.nodes: list[TerrainNode] = nodes
        self.ambient_light = AmbientLight()
        self.all_map_node_ids: list[Hex] = []
        for node in nodes:
            if node.guid is None:
                node.guid = self.new_node_guid()
        self.node_mesh_index: dict[Hex, str] = None

    def new_node_guid(self) -> Hex:
        for _ in range(8):  # 0x100000000 possible guids -> expect collisions to occur regularly at 0x10000 = 65536 nodes in map
            try:
                guid = Hex.random()
                assert guid not in [n.guid for n in self.nodes], f'new guid {guid} already in existing {len(self.nodes)} nodes'
                assert guid not in self.all_map_node_ids, f'new guid {guid} already in existing {len(self.all_map_node_ids)} map nodes'
                return guid
            except AssertionError:
                pass

    def reverse_node_mesh_index(self):
        return {v: k for k, v in self.node_mesh_index.items()}

    def create_node_mesh_index(self, mesh_range: Hex):
        if self.node_mesh_index is None:
            self.node_mesh_index = dict()
        reverse_nmi: dict[str, Hex] = self.reverse_node_mesh_index()
        nmi: dict[Hex, str] = dict()
        mesh_guid_inc = mesh_range * 0x00100000
        for node in self.nodes:
            if node.mesh_name not in reverse_nmi:
                while mesh_guid_inc in self.node_mesh_index or mesh_guid_inc in nmi:
                    mesh_guid_inc += 1
                mesh_guid = mesh_guid_inc
                reverse_nmi[node.mesh_name] = Hex(mesh_guid)
            else:
                mesh_guid = reverse_nmi[node.mesh_name]
            nmi[Hex(mesh_guid)] = node.mesh_name
        self.node_mesh_index = nmi
        return nmi

    def find_node(self, node_guid: Hex) -> Optional[TerrainNode]:
        for node in self.nodes:
            if node.guid == node_guid:
                return node
        return None

    def check_consistent_door_connections(self):
        for node in self.nodes:
            for node_door_id, (neighbor, neighbor_door_id) in node.doors.items():
                assert isinstance(neighbor, TerrainNode)
                assert neighbor.doors[neighbor_door_id] == (node, node_door_id)

    def print(self):
        print('Terrain (' + str(len(self.nodes)) + ' nodes)')
