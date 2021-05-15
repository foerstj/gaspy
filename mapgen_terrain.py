import math
import random

from gas import Position, Quaternion
from terrain import TerrainNode, Terrain


# A plant, or whatever object for that matter
class Plant:
    def __init__(self, template_name=None, map_pos=None, orientation=None):
        self.template_name = template_name
        self.map_pos = map_pos
        self.orientation = orientation
        self.node_pos = None


class MapgenTerrain:
    TILE_SIZE = 0  # override me

    class NodeTile:  # virtual map square
        def __init__(self, turned=0, node=None):
            assert 0 <= turned <= 3
            self.node: TerrainNode = node
            self.turned = turned  # number of times the node is turned 90° counter-clockwise
            self.is_target_node = False
            self.offset = (0, 0)  # XZ tuple. This tile-center's offset in node-space
            self.doors = None  # NWSE tuple. Node's doors on tile's edges

        def turn_angle(self):
            return self.turned * math.tau / 4

    def __init__(self, size_x=0, size_z=0):
        assert size_x % self.TILE_SIZE == 0
        assert size_z % self.TILE_SIZE == 0
        self.size_x = size_x
        self.size_z = size_z
        node_size_x = int(size_x / self.TILE_SIZE)
        node_size_z = int(size_z / self.TILE_SIZE)
        self.node_size_x = node_size_x
        self.node_size_z = node_size_z
        nodes_2d = [[self.NodeTile(random.randint(0, 3)) for _ in range(node_size_z)] for _ in range(node_size_x)]
        target_node_tile = nodes_2d[int(node_size_x/2)][int(node_size_z/2)]
        target_node_tile.turned = 0  # keep default orientation of target node
        target_node_tile.doors = (1, 2, 3, 4)
        target_node_tile.is_target_node = True
        self.nodes_2d = nodes_2d
        self.plants: list[Plant] = []  # plants or whatever objects

    @staticmethod
    def add_offsets(a, b):
        return a[0]+b[0], a[1]+b[1]

    def make_terrain(self) -> Terrain:
        raise NotImplementedError()  # override me

    @staticmethod
    def turn(x, z, angle):
        xt = math.cos(angle)*x + math.sin(angle)*z
        zt = math.cos(angle)*z - math.sin(angle)*x
        return xt, zt

    def map_pos_to_node_pos(self, map_pos_x, map_pos_z) -> Position:
        raise NotImplementedError()  # override me

    @staticmethod
    def rad_to_quat(rad):
        y = math.sin(rad / 2)
        w = math.cos(rad / 2)
        return Quaternion(0, y, 0, w)

    def make_non_interactive_objects(self):
        for plant in self.plants:
            (map_pos_x, map_pos_z) = plant.map_pos
            node_pos = self.map_pos_to_node_pos(map_pos_x, map_pos_z)
            plant.node_pos = node_pos
            xnt = int(map_pos_x / self.TILE_SIZE)
            znt = int(map_pos_z / self.TILE_SIZE)
            node_tile = self.nodes_2d[xnt][znt]
            plant.orientation -= node_tile.turn_angle()
        objects_non_interactive = [(plant.template_name, plant.node_pos, self.rad_to_quat(plant.orientation)) for plant in self.plants]
        return objects_non_interactive


class MapgenTerrainFloor(MapgenTerrain):
    TILE_SIZE = 4

    def tessellate(self):
        # try to randomly find tiles that can be joined into a larger node
        if self.node_size_x > 1 and self.node_size_z > 1:
            num_fails = 0
            while num_fails < self.node_size_x * self.node_size_z:
                num_fails += 1
                x = random.randint(0, self.node_size_x-2)
                z = random.randint(0, self.node_size_z-2)
                neighbors = [[self.nodes_2d[x+xx][z+zz] for zz in range(0, 2)] for xx in range(0, 2)]
                if neighbors[0][0].is_target_node:
                    continue
                if neighbors[0][0].node.mesh_name == 't_xxx_flr_04x04-v0':
                    # try 8x8
                    if neighbors[0][1].node.mesh_name == 't_xxx_flr_04x04-v0' and neighbors[1][0].node.mesh_name == 't_xxx_flr_04x04-v0' and neighbors[1][1].node.mesh_name == 't_xxx_flr_04x04-v0':
                        if neighbors[0][1].is_target_node or neighbors[1][0].is_target_node or neighbors[1][1].is_target_node:
                            continue
                        node = TerrainNode(None, 't_xxx_flr_08x08-v0')
                        doors = ((2, 3, None, None), (None, 4, 5, None), (None, None, 6, 7), (1, None, None, 8))
                        turned = random.randint(0, 3)
                        n = (-turned) % 4
                        doors = doors[n:] + doors[:n]
                        doors = [d[n:] + d[:n] for d in doors]
                        neighbors[0][0].node = node
                        neighbors[0][0].turned = turned
                        turn_angle = neighbors[0][0].turn_angle()
                        neighbors[0][0].offset = self.turn(-2, -2, -turn_angle)
                        neighbors[0][0].doors = doors[0]
                        turn_angle += math.tau/4
                        neighbors[1][0].node = node
                        neighbors[1][0].turned = turned
                        neighbors[1][0].offset = self.turn(-2, -2, -turn_angle)
                        neighbors[1][0].doors = doors[3]
                        turn_angle += math.tau/4
                        neighbors[1][1].node = node
                        neighbors[1][1].turned = turned
                        neighbors[1][1].offset = self.turn(-2, -2, -turn_angle)
                        neighbors[1][1].doors = doors[2]
                        turn_angle += math.tau/4
                        neighbors[0][1].node = node
                        neighbors[0][1].turned = turned
                        neighbors[0][1].offset = self.turn(-2, -2, -turn_angle)
                        neighbors[0][1].doors = doors[1]
                        num_fails = 0
                    else:  # try 4x8
                        node = TerrainNode(None, 't_xxx_flr_04x08-v0')
                        doors = ((2, 3, 4, None), (1, None, 5, 6))
                        if random.getrandbits(1):
                            # vertical
                            if neighbors[0][1].node.mesh_name == 't_xxx_flr_04x04-v0':
                                if neighbors[0][1].is_target_node:
                                    continue
                                turned = 1 if random.getrandbits(1) else 3
                                n = (-turned) % 4
                                if turned == 1:
                                    doors = doors[1:] + doors[:1]
                                doors = [d[n:] + d[:n] for d in doors]
                                neighbors[0][0].node = node
                                neighbors[0][0].turned = turned
                                turn_angle = neighbors[0][0].turn_angle()
                                turn_angle += math.tau / 4
                                neighbors[0][0].offset = self.turn(-2, 0, -turn_angle)
                                neighbors[0][0].doors = doors[0]
                                turn_angle += math.tau / 2
                                neighbors[0][1].node = node
                                neighbors[0][1].turned = turned
                                neighbors[0][1].offset = self.turn(-2, 0, -turn_angle)
                                neighbors[0][1].doors = doors[1]
                                num_fails = 0
                        else:
                            # horizontal
                            if neighbors[1][0].node.mesh_name == 't_xxx_flr_04x04-v0':
                                if neighbors[1][0].is_target_node:
                                    continue
                                turned = 0 if random.getrandbits(1) else 2
                                n = (-turned) % 4
                                if turned == 2:
                                    doors = doors[1:] + doors[:1]
                                doors = [d[n:] + d[:n] for d in doors]
                                neighbors[0][0].node = node
                                neighbors[0][0].turned = turned
                                turn_angle = neighbors[0][0].turn_angle()
                                neighbors[0][0].offset = self.turn(-2, 0, -turn_angle)
                                neighbors[0][0].doors = doors[0]
                                turn_angle += math.tau / 2
                                neighbors[1][0].node = node
                                neighbors[1][0].turned = turned
                                neighbors[1][0].offset = self.turn(-2, 0, -turn_angle)
                                neighbors[1][0].doors = doors[1]
                                num_fails = 0

    def make_terrain(self):
        terrain = Terrain()
        # nodes
        for x in range(self.node_size_x):
            for z in range(self.node_size_z):
                node_tile = self.nodes_2d[x][z]
                node = TerrainNode(None, 't_xxx_flr_04x04-v0')
                node_tile.node = node
                doors = (1, 2, 3, 4)
                n = (-node_tile.turned) % 4
                doors = doors[n:] + doors[:n]
                node_tile.doors = doors
        # tessellate
        self.tessellate()
        terrain_nodes = set()
        for row in self.nodes_2d:
            for nt in row:
                terrain_nodes.add(nt.node)
        for n in terrain_nodes:
            n.guid = terrain.new_node_guid()
        terrain.nodes = list(terrain_nodes)
        # connect
        for x in range(self.node_size_x):
            for z in range(self.node_size_z):
                nt = self.nodes_2d[x][z]
                node = nt.node
                if x > 0:
                    nnt = self.nodes_2d[x-1][z]
                    node.connect_doors(nt.doors[1], nnt.node, nnt.doors[3])
                if x < self.node_size_x-1:
                    nnt = self.nodes_2d[x+1][z]
                    node.connect_doors(nt.doors[3], nnt.node, nnt.doors[1])
                if z > 0:
                    nnt = self.nodes_2d[x][z-1]
                    node.connect_doors(nt.doors[0], nnt.node, nnt.doors[2])
                if z < self.node_size_z-1:
                    nnt = self.nodes_2d[x][z+1]
                    node.connect_doors(nt.doors[2], nnt.node, nnt.doors[0])
        i_tn_x = int(self.node_size_x / 2)
        i_tn_z = int(self.node_size_z / 2)
        target_nt = self.nodes_2d[i_tn_x][i_tn_z]
        assert target_nt.node.mesh_name == 't_xxx_flr_04x04-v0'
        assert target_nt.is_target_node
        assert target_nt.turned == 0
        assert target_nt.doors == (1, 2, 3, 4)
        terrain.target_node = target_nt.node
        # ambient light
        terrain.ambient_light.intensity = 0.2
        terrain.ambient_light.object_intensity = 0.2
        terrain.ambient_light.actor_intensity = 0.25
        return terrain

    def map_pos_to_node_pos(self, map_pos_x, map_pos_z):
        xnt = int(map_pos_x / 4)
        znt = int(map_pos_z / 4)
        node_tile = self.nodes_2d[xnt][znt]
        ntx = map_pos_x % 4 - 2
        ntz = map_pos_z % 4 - 2
        na = node_tile.turn_angle()
        ntxt, ntzt = self.turn(ntx, ntz, -na)
        nx = node_tile.offset[0] + ntxt
        nz = node_tile.offset[1] + ntzt
        node_pos = Position(nx, 0, nz, node_tile.node.guid)
        return node_pos


class MapgenTerrainDunes(MapgenTerrain):
    TILE_SIZE = 32

    def tessellate(self):
        if self.node_size_x > 1 and self.node_size_z > 1:
            num_fails = 0
            while num_fails < self.node_size_x * self.node_size_z:
                num_fails += 1
                x = random.randint(0, self.node_size_x-2)
                z = random.randint(0, self.node_size_z-2)
                neighbors = [[self.nodes_2d[x+xx][z+zz] for zz in range(0, 2)] for xx in range(0, 2)]
                if neighbors[0][0].is_target_node:
                    continue
                if neighbors[0][0].node.mesh_name == 't_dc01_dunes-32x32-a':
                    # try 8x8
                    if neighbors[0][1].node.mesh_name == 't_dc01_dunes-32x32-a' and neighbors[1][0].node.mesh_name == 't_dc01_dunes-32x32-a' and neighbors[1][1].node.mesh_name == 't_dc01_dunes-32x32-a':
                        if neighbors[0][1].is_target_node or neighbors[1][0].is_target_node or neighbors[1][1].is_target_node:
                            continue
                        node = TerrainNode(None, 't_dc01_dunes-64x64-a')
                        doors = ((2, 3, None, None), (None, 4, 5, None), (None, None, 6, 7), (1, None, None, 8))
                        turned = random.randint(0, 3)
                        n = (-turned) % 4
                        doors = doors[n:] + doors[:n]
                        doors = [d[n:] + d[:n] for d in doors]
                        neighbors[0][0].node = node
                        neighbors[0][0].turned = turned
                        turn_angle = neighbors[0][0].turn_angle()
                        neighbors[0][0].offset = self.add_offsets((-14, -22), self.turn(-16, -16, -turn_angle))
                        neighbors[0][0].doors = doors[0]
                        turn_angle += math.tau/4
                        neighbors[1][0].node = node
                        neighbors[1][0].turned = turned
                        neighbors[1][0].offset = self.add_offsets((-14, -22), self.turn(-16, -16, -turn_angle))
                        neighbors[1][0].doors = doors[3]
                        turn_angle += math.tau/4
                        neighbors[1][1].node = node
                        neighbors[1][1].turned = turned
                        neighbors[1][1].offset = self.add_offsets((-14, -22), self.turn(-16, -16, -turn_angle))
                        neighbors[1][1].doors = doors[2]
                        turn_angle += math.tau/4
                        neighbors[0][1].node = node
                        neighbors[0][1].turned = turned
                        neighbors[0][1].offset = self.add_offsets((-14, -22), self.turn(-16, -16, -turn_angle))
                        neighbors[0][1].doors = doors[1]
                        num_fails = 0
                    #else:  # try 4x8  # there are no 32x64 hills lol

    def make_terrain(self):
        terrain = Terrain()
        # nodes
        for x in range(self.node_size_x):
            for z in range(self.node_size_z):
                node_tile = self.nodes_2d[x][z]
                node = TerrainNode(None, 't_dc01_dunes-32x32-a')
                node_tile.node = node
                node_tile.offset = (2, -38)
                doors = (1, 2, 3, 4)
                n = (-node_tile.turned) % 4
                doors = doors[n:] + doors[:n]
                node_tile.doors = doors
        # tessellate
        self.tessellate()
        terrain_nodes = set()
        for row in self.nodes_2d:
            for nt in row:
                terrain_nodes.add(nt.node)
        for n in terrain_nodes:
            n.guid = terrain.new_node_guid()
        terrain.nodes = list(terrain_nodes)
        # connect
        for x in range(self.node_size_x):
            for z in range(self.node_size_z):
                nt = self.nodes_2d[x][z]
                node = nt.node
                if x > 0:
                    nnt = self.nodes_2d[x-1][z]
                    node.connect_doors(nt.doors[1], nnt.node, nnt.doors[3])
                if x < self.node_size_x-1:
                    nnt = self.nodes_2d[x+1][z]
                    node.connect_doors(nt.doors[3], nnt.node, nnt.doors[1])
                if z > 0:
                    nnt = self.nodes_2d[x][z-1]
                    node.connect_doors(nt.doors[0], nnt.node, nnt.doors[2])
                if z < self.node_size_z-1:
                    nnt = self.nodes_2d[x][z+1]
                    node.connect_doors(nt.doors[2], nnt.node, nnt.doors[0])
        i_tn_x = int(self.node_size_x / 2)
        i_tn_z = int(self.node_size_z / 2)
        target_nt = self.nodes_2d[i_tn_x][i_tn_z]
        assert target_nt.node.mesh_name == 't_dc01_dunes-32x32-a'
        assert target_nt.is_target_node
        assert target_nt.turned == 0
        assert target_nt.doors == (1, 2, 3, 4)
        terrain.target_node = target_nt.node
        # ambient light
        terrain.ambient_light.intensity = 0.25
        terrain.ambient_light.object_intensity = 0.3
        terrain.ambient_light.actor_intensity = 0.35
        return terrain

    def map_pos_to_node_pos(self, map_pos_x, map_pos_z):
        xnt = int(map_pos_x / 32)
        znt = int(map_pos_z / 32)
        node_tile = self.nodes_2d[xnt][znt]
        ntx = map_pos_x % 32 - 16
        ntz = map_pos_z % 32 - 16
        na = node_tile.turn_angle()
        ntxt, ntzt = self.turn(ntx, ntz, -na)
        nx = node_tile.offset[0] + ntxt
        nz = node_tile.offset[1] + ntzt
        node_pos = Position(nx, 10, nz, node_tile.node.guid)
        return node_pos
