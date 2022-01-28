from __future__ import annotations

import argparse
import math
import random
import sys

from perlin_noise import PerlinNoise

from bits.bits import Bits
from bits.game_object_data import GameObjectData, Placement, Common, TriggerInstance, Aspect
from gas.gas import Hex, Position, Quaternion
from mapgen.mapgen_plants import load_plants_profile
from mapgen.mapgen_terrain import MapgenTerrain
from plant_gen import Plant
from bits.region import DirectionalLight, Region
from bits.start_positions import StartPos, StartGroup, Camera
from bits.stitch_helper_gas import StitchHelperGas, StitchEditor
from bits.terrain import TerrainNode, Terrain

from matplotlib import pyplot as plt

NODES = {
    # mesh: TR, TL, BL, BR
    't_xxx_flr_04x04-v0': (0, 0, 0, 0),
    't_xxx_wal_04-thin': (0, 0, 4, 4),
    't_xxx_wal_08-thin': (0, 0, 8, 8),
    't_xxx_wal_12-thin': (0, 0, 12, 12),
    't_xxx_cnr_04-ccav': (0, 4, 4, 4),
    't_xxx_cnr_04-cnvx': (0, 0, 4, 0),
    't_xxx_cnr_08-ccav': (0, 8, 8, 8),
    't_xxx_cnr_08-cnvx': (0, 0, 8, 0),
    't_xxx_cnr_12-ccav': (0, 12, 12, 12),
    't_xxx_cnr_12-cnvx': (0, 0, 12, 0),
    't_xxx_cnr_tee-04-04-08-l': (0, 0, 8, 4),
    't_xxx_cnr_tee-04-04-08-r': (0, 0, 4, 8),
    't_xxx_cnr_tee-04-08-12-l': (0, 0, 12, 4),
    't_xxx_cnr_tee-04-08-12-r': (0, 0, 4, 12),
    't_xxx_cnr_tee-08-04-12-l': (0, 0, 12, 8),
    't_xxx_cnr_tee-08-04-12-r': (0, 0, 8, 12),
}


def turn_node(points, turn):  # turn: #times turned 90° counter-clockwise
    return points[(0 - turn) % 4], points[(1 - turn) % 4], points[(2 - turn) % 4], points[(3 - turn) % 4]


def avg(*args) -> float:
    return sum(args) / len(args)


class Point:
    def __init__(self, x: int, z: int, height: float, heightmap: list[list[Point]] = None):
        self.x = x
        self.z = z
        self.input_height = height
        self.height = height
        self.heightmap = heightmap
        self.tile_tl = None
        self.tile_tr = None
        self.tile_bl = None
        self.tile_br = None
        self.pre_fixed = False

    def set_height(self, height: float):
        if self.pre_fixed:
            assert height == self.height, f'tried to set height from {self.height} to {height} on fixed point ({self.x}|{self.z})'
        else:
            self.height = height

    def tiles(self) -> list[Tile]:
        tiles: list[Tile] = [self.tile_tl, self.tile_tr, self.tile_bl, self.tile_br]
        tiles = [t for t in tiles if t is not None]
        return tiles

    def num_assigned_nodes(self) -> int:
        return sum([1 if tile.node_mesh is not None else 0 for tile in self.tiles()])

    def clear(self):
        assert not self.pre_fixed
        for t in self.tiles():
            t.node_mesh = None
        self.height = self.input_height

    def is_fixed(self) -> bool:
        return self.pre_fixed or self.num_assigned_nodes() > 0

    def neighbor_points(self) -> list[Point]:
        nps = []
        if self.x > 0:
            nps.append(self.heightmap[self.x-1][self.z])
        if self.z > 0:
            nps.append(self.heightmap[self.x][self.z-1])
        if self.x < len(self.heightmap)-1:
            nps.append(self.heightmap[self.x+1][self.z])
        if self.z < len(self.heightmap[self.x])-1:
            nps.append(self.heightmap[self.x][self.z+1])
        return nps


class Tile:
    def __init__(self, x, z, heightmap: list[list[Point]], tiles: list[list[Tile]] = None):
        self.x = x
        self.z = z
        self.point_tl: Point = heightmap[x][z]
        self.point_tr: Point = heightmap[x+1][z]
        self.point_bl: Point = heightmap[x][z+1]
        self.point_br: Point = heightmap[x+1][z+1]
        self.point_tl.tile_br = self
        self.point_tr.tile_bl = self
        self.point_bl.tile_tr = self
        self.point_br.tile_tl = self
        self.tiles = tiles
        self.height = self.avg_height()  # used to determine tile generation order
        self.dist2center = None
        self.node_mesh = None
        self.node_turn = None  # number of times the node is turned counter-clockwise (0-3)
        self.node_base_height = None
        self.fail_count = 0
        self.node = None
        self.doors = None  # doors of turned node in order top-left-bottom-right
        self.connected_to_target = False

    def __str__(self):
        return f'({self.x}|{self.z}): {self.node_mesh}'

    def points(self) -> list[Point]:
        return [self.point_tl, self.point_tr, self.point_bl, self.point_br]

    def avg_height(self):
        return avg(*[p.height for p in self.points()])

    def min_height(self):
        return min(*[p.height for p in self.points()])

    def max_height(self):
        return max(*[p.height for p in self.points()])

    def get_clearable_points(self) -> list[Point]:
        return [p for p in self.points() if p.num_assigned_nodes() > 0 and not p.pre_fixed]

    def assign_node(self, node_mesh, node_turn, node_base_height):
        self.node_mesh = node_mesh
        self.node_turn = node_turn
        self.node_base_height = node_base_height
        tr, tl, bl, br = [point_height+node_base_height for point_height in turn_node(NODES[node_mesh], node_turn)]
        self.point_tl.set_height(tl)
        self.point_tr.set_height(tr)
        self.point_bl.set_height(bl)
        self.point_br.set_height(br)

    def turn_angle(self):
        return self.node_turn * math.tau / 4

    def neighbor_tiles(self) -> list[Tile]:
        nts = []
        if self.x > 0:
            nts.append(self.tiles[self.x-1][self.z])
        if self.z > 0:
            nts.append(self.tiles[self.x][self.z-1])
        if self.x < len(self.tiles)-1:
            nts.append(self.tiles[self.x+1][self.z])
        if self.z < len(self.tiles[self.x])-1:
            nts.append(self.tiles[self.x][self.z+1])
        return nts

    def has_pre_fixed_point(self):
        return len([p for p in self.points() if p.pre_fixed]) > 0

    def crosses_middle(self):
        above = False
        below = False
        for point in self.points():
            if point.input_height <= 0:
                below = True
            if point.input_height >= 0:
                above = True
        return above and below


def make_perlin(seed, max_size_xz, octaves_per_km):
    waves_per_km = 2**octaves_per_km
    waves = max_size_xz * 4 / 1000 * waves_per_km
    perlin = PerlinNoise(waves, seed)
    return perlin


def gen_perlin_heightmap_flat(tile_size_x: int, tile_size_z: int) -> list[list[float]]:
    # completely flat, for testing purposes (plant distributions better visible)
    heightmap = [[0 for _ in range(tile_size_z+1)] for _ in range(tile_size_x+1)]
    return heightmap


def gen_perlin_heightmap_smooth(tile_size_x: int, tile_size_z: int, args: Args, rt: RegionTiling, octaves_per_km=3.5, height=4*8) -> list[list[float]]:
    # default shape, a simple smooth perlin heightmap
    max_size_xz = max(tile_size_x*rt.num_x, tile_size_z*rt.num_z)
    perlin = make_perlin(args.seed, max_size_xz, octaves_per_km)
    heightmap = [[perlin([(rt.cur_x*tile_size_x + x)/max_size_xz, (rt.cur_z*tile_size_z + z)/max_size_xz]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]  # -0.5 .. +0.5
    heightmap = [[point*2 for point in col] for col in heightmap]  # -1 .. +1
    heightmap = [[point*height for point in col] for col in heightmap]  # -32 .. +32  # max 8 levels up and down from mid-level
    return heightmap


def gen_perlin_heightmap_demo(tile_size_x: int, tile_size_z: int, args: Args, rt: RegionTiling, sampling=1) -> list[list[float]]:
    # this shape is for me to play around with
    # sampling param is for generating overview image
    map_size_x = tile_size_x*rt.num_x + 1
    map_size_z = tile_size_z*rt.num_z + 1
    max_size_xz = max(map_size_x, map_size_z)
    perlin = make_perlin(args.seed, max_size_xz*sampling, 2)

    heightmap = [[0.0 for _ in range(tile_size_z+1)] for _ in range(tile_size_x+1)]  # create array
    for x in range(tile_size_x+1):
        map_x = rt.cur_x * tile_size_x + x
        for z in range(tile_size_z+1):
            map_z = rt.cur_z*tile_size_z + z
            coord_shift = 0.0000001  # mitigate current float epsilon bug in lib (wtf)
            perlin_value = perlin([map_x/max_size_xz+coord_shift, map_z/max_size_xz+coord_shift])
            height = perlin_value  # -0.5 .. 0.5
            height *= 2  # -1 .. 1
            height *= 4  # -4 .. +4  # small node wall height
            height *= 42  # basic steepness of the map that gives a good relation of playable area and cutoffs
            if -12 < height < 12:
                height /= 3  # flatten play-area
            if -3 < height < 3:
                height /= 3  # flatten middle even more
            if height < -16:
                height *= 2  # steeper drop-offs to reach cutoff more quickly
            if -6 < height < 6:
                height /= 3  # temporary: flatten playable area for testing

            # map cutoffs
            cutoff_curve = perlin_value / 5  # -0.1 .. 0.1
            steepness = 2
            mrx = map_x/map_size_x
            mrz = map_z/map_size_z
            v = mrz + 2*mrx
            if v < 1-cutoff_curve:
                w = int((v-(1-cutoff_curve))*max_size_xz*sampling*steepness)
                height = min(height, max(-120, min(0, w-(w % 12)+4)))
            v = 2*mrz + mrx
            if v < 1-cutoff_curve:
                w = int((v-(1-cutoff_curve))*max_size_xz*sampling*steepness)
                height = min(height, max(-120, min(0, w-(w % 12)+4)))
            mrx = 1-mrx
            mrz = 1-mrz
            v = mrz + 2*mrx
            if v < 1-cutoff_curve:
                w = int((v-(1-cutoff_curve))*max_size_xz*sampling*steepness)
                height = min(height, max(-120, min(0, w-(w % 12)+4)))
            v = 2*mrz + mrx
            if v < 1-cutoff_curve:
                w = int((v-(1-cutoff_curve))*max_size_xz*sampling*steepness)
                height = min(height, max(-120, min(0, w-(w % 12)+4)))

            heightmap[x][z] = height

    return heightmap


def gen_perlin_heightmap(tile_size_x: int, tile_size_z: int, args: Args, rt: RegionTiling, sampling=1) -> list[list[Point]]:
    shape = args.shape
    if shape == 'demo':
        heightmap_values = gen_perlin_heightmap_demo(tile_size_x, tile_size_z, args, rt, sampling)
    elif shape == 'flat':
        heightmap_values = gen_perlin_heightmap_flat(tile_size_x, tile_size_z)
    else:
        assert shape == 'smooth'
        heightmap_values = gen_perlin_heightmap_smooth(tile_size_x, tile_size_z, args, rt)

    # culled anyway -> flatten to relieve the algo
    if args.cull_below is not None:
        heightmap_values = [[max(pv, args.cull_below-4) for pv in col] for col in heightmap_values]
    if args.cull_above is not None:
        heightmap_values = [[min(pv, args.cull_above+4) for pv in col] for col in heightmap_values]

    heightmap_points = [[Point(x, z, heightmap_values[x][z]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]
    for x in range(tile_size_x+1):
        for z in range(tile_size_z+1):
            heightmap_points[x][z].heightmap = heightmap_points
    return heightmap_points


def fit_nodes(tl, tl_fixed, tr, tr_fixed, bl, bl_fixed, br, br_fixed):
    if tl_fixed or tr_fixed or bl_fixed or br_fixed:
        fixed_heights = [
            tl if tl_fixed else None,
            tr if tr_fixed else None,
            bl if bl_fixed else None,
            br if br_fixed else None,
        ]
        fixed_heights = [p for p in fixed_heights if p is not None]
        fixed_base_height = min(fixed_heights)
    else:
        avg_height = avg(tl, tr, bl, br)
        fixed_base_height = round(avg_height / 4) * 4

    # find best-fitting node
    node_fits = list()
    nodes = list(NODES.items())
    random.shuffle(nodes)
    for mesh, points in nodes:
        point_heights = set(points)
        turns = list(range(0, 4))
        random.shuffle(turns)
        for turn in turns:
            turned_points = turn_node(points, turn)
            for base_height in [fixed_base_height - point_height for point_height in point_heights]:
                tn_tl = turned_points[1] + base_height
                tn_tr = turned_points[0] + base_height
                tn_bl = turned_points[2] + base_height
                tn_br = turned_points[3] + base_height
                if tl_fixed and tn_tl != tl:
                    continue
                if tr_fixed and tn_tr != tr:
                    continue
                if bl_fixed and tn_bl != bl:
                    continue
                if br_fixed and tn_br != br:
                    continue
                fit = abs(tl - tn_tl) + abs(tr - tn_tr) + abs(bl - tn_bl) + abs(br - tn_br)
                node_fits.append((mesh, turn, base_height, fit, (tn_tl, tn_tr, tn_bl, tn_br)))
    node_fits.sort(key=lambda x: x[3])  # sort by fit
    return node_fits[0] if len(node_fits) > 0 else None


def generate_tile(tile: Tile, tiles: list[list[Tile]], tile_size_x: int, tile_size_z: int):
    assert tile.node_mesh is None

    tl = tile.point_tl.height
    tr = tile.point_tr.height
    bl = tile.point_bl.height
    br = tile.point_br.height

    tl_fixed = tile.point_tl.is_fixed()
    tr_fixed = tile.point_tr.is_fixed()
    bl_fixed = tile.point_bl.is_fixed()
    br_fixed = tile.point_br.is_fixed()

    # find best-fitting node
    best_fit = fit_nodes(tl, tl_fixed, tr, tr_fixed, bl, bl_fixed, br, br_fixed)

    if best_fit is not None:
        mesh, turn, height, fit, points = best_fit

        # assign found node
        tile.assign_node(mesh, turn, height)
        return False  # all good
    else:
        # print(f'{(tile.x, tile.z)}: no fit found for TR-TL-BL-BR {((tr, tr_fixed), (tl, tl_fixed), (bl, bl_fixed), (br, br_fixed))}')
        # pick a fixed point and clear it by deleting the surrounding nodes
        fixed_points = tile.get_clearable_points()
        if len(fixed_points) > 0:
            point: Point = random.choice(fixed_points)
            # print(f'clearing point {(point.x, point.z)}')
            point.clear()

            generate_tile(tile, tiles, tile_size_x, tile_size_z)  # try again with fewer constraints
            tile.fail_count += 1
            return True  # restart to re-generate all deleted tiles
        else:
            print(f'{(tile.x, tile.z)}: no fit possible for TR-TL-BL-BR {((tr, tr_fixed), (tl, tl_fixed), (bl, bl_fixed), (br, br_fixed))}')
            # give up
            tile.node_mesh = 'EMPTY'
            tile.fail_count += 23
            return False


def max_apart(value, other_value, max_diff):
    if value - other_value > max_diff:
        return other_value + max_diff
    if value - other_value < -max_diff:
        return other_value - max_diff
    return value


def pre_fix_border_point(point: Point, border: list[Point], i_point: int):
    height = point.height
    i = i_point
    while i > 0:
        i -= 1
        if border[i].pre_fixed:
            height = max_apart(height, border[i].height, 12*abs(i-i_point))
    i = i_point
    while i < len(border)-1:
        i += 1
        if border[i].pre_fixed:
            height = max_apart(height, border[i].height, 12*abs(i-i_point))
    point.set_height(height)
    point.pre_fixed = True


def pre_fix_border_sub(border: list[Point]):
    for point in border:
        point.set_height(round(point.height / 4) * 4)

    border[0].pre_fixed = True
    border[-1].pre_fixed = True
    border[1].set_height(border[0].height)
    border[1].pre_fixed = True
    border[-2].set_height(border[-1].height)
    border[-2].pre_fixed = True

    for i, point in sorted(enumerate(border), key=lambda x: abs(x[1].height)):
        pre_fix_border_point(point, border, i)


def pre_fix_border(heightmap: list[list[Point]], tile_size_x, tile_size_z):
    # pre-fix outer points to make region tiling possible (generating multiple regions that are stitchable)
    top = [heightmap[x][0] for x in range(tile_size_x+1)]
    bottom = [heightmap[x][tile_size_z] for x in range(tile_size_x+1)]
    left = [heightmap[0][z] for z in range(tile_size_z+1)]
    right = [heightmap[tile_size_x][z] for z in range(tile_size_z+1)]
    pre_fix_border_sub(top)
    pre_fix_border_sub(bottom)
    pre_fix_border_sub(left)
    pre_fix_border_sub(right)


def generate_tiles(tile_size_x: int, tile_size_z: int, heightmap: list[list[Point]], args: Args, rt: RegionTiling):
    tiles = [[Tile(x, z, heightmap) for z in range(tile_size_z)] for x in range(tile_size_x)]
    for x in range(tile_size_x):
        for z in range(tile_size_z):
            tiles[x][z].tiles = tiles

    pre_fix_border(heightmap, tile_size_x, tile_size_z)

    all_tiles = []
    for tiles_col in tiles:
        all_tiles.extend(tiles_col)
    for tile in all_tiles:
        dx = abs((tile_size_x/2) - (tile.x + 0.5))
        dz = abs((tile_size_z/2) - (tile.z + 0.5))
        tile.dist2center = math.sqrt(dx*dx + dz*dz)
    # sort from mid-level to lowest/highest. map is generated from the mid-level out since mid-level is probably where the player would walk around
    all_tiles.sort(key=lambda x: abs(x.height))

    i = 0
    while True:
        if i >= len(all_tiles):
            break
        tile = all_tiles[i]
        i += 1
        if tile.node_mesh is not None:
            continue
        if tile.fail_count >= 69 or (tile.fail_count >= 23 and not tile.has_pre_fixed_point()):
            tile.node_mesh = 'EMPTY'  # give up
            continue
        need_backtrack = generate_tile(tile, tiles, tile_size_x, tile_size_z)
        if need_backtrack:
            i = 0
    num_empty = sum([1 if tile.node_mesh == 'EMPTY' else 0 for tile in all_tiles])
    print(f'tiles generated ({num_empty} empty)')

    # culling
    if args.cull_above is not None or args.cull_below is not None:
        for x in range(1, tile_size_x-1):
            for z in range(1, tile_size_z-1):
                tile = tiles[x][z]
                if args.cull_above is not None and tile.min_height() >= args.cull_above:
                    tile.node_mesh = 'EMPTY'
                if args.cull_below is not None and tile.max_height() <= args.cull_below:
                    tile.node_mesh = 'EMPTY'
        node_count = sum([1 if tile.node_mesh != 'EMPTY' else 0 for tile in all_tiles])
        num_tiles = tile_size_x * tile_size_z
        print(f'after culling: {node_count} nodes remaining ({100 * (num_tiles - node_count) / num_tiles}% culled)')

    save_image_tiles(tiles, f'{args.map_name}-{rt.cur_region_name()}')

    # erase lonely tiles
    for tile in all_tiles:
        if tile.node_mesh != 'EMPTY':
            if len([t for t in tile.neighbor_tiles() if t.node_mesh != 'EMPTY']) == 0:
                print(f'erasing lonely tile ({tile.x}|{tile.z})')
                tile.node_mesh = 'EMPTY'

    # find a suitable target tile
    all_tiles.sort(key=lambda x: x.dist2center)
    target_candidates = [t for t in all_tiles if t.node_mesh == 't_xxx_flr_04x04-v0']
    target_candidates.sort(key=lambda x: abs(x.node_base_height))
    target_tile = target_candidates[0]
    target_tile.node_turn = 0
    print(f'target tile: ({target_tile.x} | {target_tile.z})')

    # erase unconnected tiles
    compute_connection_to_target(target_tile)
    unconnected_tiles = [tile for tile in all_tiles if tile.node_mesh != 'EMPTY' and not tile.connected_to_target]
    if len(unconnected_tiles) > 0:
        print(f'erasing {len(unconnected_tiles)} unconnected tiles')
        node_count = sum([1 if tile.node_mesh != 'EMPTY' else 0 for tile in all_tiles])
        assert len(unconnected_tiles) < node_count / 10
        for tile in unconnected_tiles:
            tile.node_mesh = 'EMPTY'

    print('generate tiles successful')
    return tiles, target_tile


def make_terrain(tiles, target_tile, tile_size_x, tile_size_z):
    terrain = Terrain()
    for x in range(0, tile_size_x):
        for z in range(0, tile_size_z):
            tile = tiles[x][z]
            if tile.node_mesh == 'EMPTY':
                continue
            node = TerrainNode(terrain.new_node_guid(), tile.node_mesh)
            tile.node = node
            doors = (1, 2, 3, 4)
            n = (-tile.node_turn) % 4
            doors = doors[n:] + doors[:n]
            tile.doors = doors
            terrain.nodes.append(node)
    terrain.target_node = target_tile.node

    # connect
    for x in range(tile_size_x):
        for z in range(tile_size_z):
            nt = tiles[x][z]
            node = nt.node
            if node is None:
                continue
            if x > 0:
                nnt = tiles[x-1][z]
                if nnt.node is not None:
                    node.connect_doors(nt.doors[1], nnt.node, nnt.doors[3])
            if x < tile_size_x-1:
                nnt = tiles[x+1][z]
                if nnt.node is not None:
                    node.connect_doors(nt.doors[3], nnt.node, nnt.doors[1])
            if z > 0:
                nnt = tiles[x][z-1]
                if nnt.node is not None:
                    node.connect_doors(nt.doors[0], nnt.node, nnt.doors[2])
            if z < tile_size_z-1:
                nnt = tiles[x][z+1]
                if nnt.node is not None:
                    node.connect_doors(nt.doors[2], nnt.node, nnt.doors[0])

    print('make terrain successful')
    return terrain


def compute_connection_to_target(target_tile: Tile):
    target_tile.connected_to_target = True
    tiles_list = [target_tile]
    while len(tiles_list) > 0:
        tile = tiles_list.pop(0)
        new_neighbor_tiles = [t for t in tile.neighbor_tiles() if t.node_mesh != 'EMPTY' and not t.connected_to_target]
        for nt in new_neighbor_tiles:
            nt.connected_to_target = True
        tiles_list.extend(new_neighbor_tiles)


def verify(tiles: list[list[Tile]], target_tile: Tile, heightmap: list[list[Point]]):
    for tile_row in tiles:
        for tile in tile_row:
            assert tile.node_mesh is not None
            if tile.node_mesh == 'EMPTY':
                continue
            assert tile.connected_to_target
            x = tile.x
            z = tile.z
            h_tl = heightmap[x+0][z+0].height
            h_tr = heightmap[x+1][z+0].height
            h_bl = heightmap[x+0][z+1].height
            h_br = heightmap[x+1][z+1].height
            turn = tile.node_turn
            points = NODES[tile.node_mesh]
            turned_points = (points[(0 - turn) % 4], points[(1 - turn) % 4], points[(2 - turn) % 4], points[(3 - turn) % 4])
            base_height = tile.node_base_height
            t_tl = turned_points[1] + base_height
            t_tr = turned_points[0] + base_height
            t_bl = turned_points[2] + base_height
            t_br = turned_points[3] + base_height
            assert h_tl == t_tl, 'tile ' + repr((x, z)) + ', TL: ' + str(t_tl) + ' != ' + str(h_tl)
            assert h_tr == t_tr, 'tile ' + repr((x, z)) + ', TR: ' + str(t_tr) + ' != ' + str(h_tr)
            assert h_bl == t_bl, 'tile ' + repr((x, z)) + ', BL: ' + str(t_bl) + ' != ' + str(h_bl)
            assert h_br == t_br, 'tile ' + repr((x, z)) + ', BR: ' + str(t_br) + ' != ' + str(h_br)
    assert target_tile.node_mesh == 't_xxx_flr_04x04-v0'
    assert target_tile.node_turn == 0
    print('verify successful')


def save_pic(pic: list[list[float]], file_name):
    pic = [[pic[z][x] for z in range(len(pic[x]))] for x in range(len(pic))]  # flip x/z
    plt.imshow(pic, cmap='gray')
    plt.savefig(f'output/{file_name}.png', bbox_inches='tight')


def save_image_heightmap(heightmap: list[list[Point]], file_name_prefix):
    pic = [[pt.height for pt in col] for col in heightmap]
    save_pic(pic, f'{file_name_prefix} heightmap')


def save_image_tiles(tiles: list[list[Tile]], file_name_prefix):
    pic = [[0 if tile.node_mesh == 'EMPTY' else 1 if tile.node_mesh.startswith('t_xxx_flr') else 0.5 for tile in col] for col in tiles]
    save_pic(pic, f'{file_name_prefix} tiles')


class SingleProfile:
    def __init__(self, profile_name):
        self.profile = load_plants_profile(profile_name)

    def max_sum_seed_factor(self):  # end of recursion
        return self.profile.sum_seed_factor()

    def choose_profile(self, _, __):  # end of recursion
        return self.profile


class ProfileVariants:
    def __init__(self, a: SingleProfile | ProfileVariants | None, b: SingleProfile | ProfileVariants | None, perlin, tx='sharp'):
        assert tx in ['sharp', 'blur', 'gap']
        self.a = a
        self.b = b
        self.perlin = perlin
        self.tx = tx

    def max_sum_seed_factor(self):
        profiles = [p for p in [self.a, self.b] if p is not None]
        if len(profiles) == 0:
            return 0
        return max([p.max_sum_seed_factor() for p in profiles])

    def choose_profile(self, map_norm_x, map_norm_z):
        variant_perlin_value = self.perlin([map_norm_x, map_norm_z])
        variant_a_probability = variant_perlin_value * 16 + 0.5
        if variant_a_probability < 0:
            p = self.b
        elif variant_a_probability > 1:
            p = self.a
        else:
            if self.tx == 'blur':
                choose_a = random.uniform(0, 1) < variant_a_probability
                p = self.a if choose_a else self.b
            elif self.tx == 'sharp':
                p = self.a if variant_a_probability > 0.5 else self.b
            else:  # tx == gap
                p = None
        if p is None:
            return None
        return p.choose_profile(map_norm_x, map_norm_z)  # recurse into sub-variants


class ProgressionStep:
    def __init__(self, plants_profile: SingleProfile | ProfileVariants | None, enemies_profile: SingleProfile | ProfileVariants = None):
        self.plants_profile = plants_profile
        self.enemies_profile = enemies_profile

    def get_profile(self, plants=True):
        return self.plants_profile if plants else self.enemies_profile

    def max_sum_seed_factor(self, plants=True):
        profile = self.get_profile(plants)
        if profile is None:
            return 0
        return profile.max_sum_seed_factor()


class Progression:
    def __init__(self, steps: list[tuple[float, ProgressionStep | Progression]], direction, perlin_curve, perlin_curve_factor, tx_factor):
        self.steps = steps
        assert direction in ['sw2ne', 'nw2se']
        self.direction = direction
        self.perlin_curve = perlin_curve
        self.perlin_curve_factor = perlin_curve_factor
        self.tx_factor = tx_factor

    def max_sum_seed_factor(self, plants=True) -> float:
        return max([step.max_sum_seed_factor(plants) for _, step in self.steps])

    def choose_progression_step(self, map_norm_x, map_norm_z, tx='sharp') -> ProgressionStep:
        assert tx in ['blur', 'sharp', 'gap']
        curve_perlin_value = self.perlin_curve([map_norm_x, map_norm_z])
        assert self.direction in ['sw2ne', 'nw2se']
        if self.direction == 'sw2ne':
            progression_value = (map_norm_x + (1 - map_norm_z)) / 2  # southwest=0 -> northeast=1
        else:
            progression_value = (map_norm_x + map_norm_z) / 2  # northwest=0 -> southeast=1
        progression_value += curve_perlin_value / self.perlin_curve_factor  # curve the border
        if tx == 'blur':
            # blur the border by random fuzziness - used for plants
            tx_random_value = random.uniform(-0.5, 0.5) * self.tx_factor
            progression_value += tx_random_value  # blur the border
        chosen_step = None
        for step_value, step in self.steps:
            chosen_step = step
            if tx == 'gap':
                # leave a gap between steps - used for enemies
                if step_value != 1 and abs(step_value - progression_value) < self.tx_factor/2:
                    chosen_step = None
                    break
            if step_value > progression_value:
                break
        if isinstance(chosen_step, Progression):
            chosen_step = chosen_step.choose_progression_step(map_norm_x, map_norm_z, tx)  # recurse into nested progression
        return chosen_step


def generate_game_objects(tile_size_x, tile_size_z, tiles: list[list[Tile]], args: Args, rt: RegionTiling) -> list[Plant]:
    max_size_xz = max(tile_size_x*rt.num_x, tile_size_z*rt.num_z)
    perlin_plants_main = make_perlin(args.seed, max_size_xz, 6)  # main plant growth
    perlin_prog_tx = make_perlin(args.seed, max_size_xz, 5)  # curving progression tx lines
    perlin_plants_underlay = make_perlin(args.seed, max_size_xz, 4)  # wider plant growth underlay
    perlin_variants = make_perlin(args.seed, max_size_xz, 3)  # for main a/b variants
    perlin_subvar_a = make_perlin(args.seed+1, max_size_xz, 5)
    perlin_subvar_b = make_perlin(args.seed+2, max_size_xz, 5)

    floor_tiles = []
    for tcol in tiles:
        floor_tiles.extend([tile for tile in tcol if tile.node_mesh == 't_xxx_flr_04x04-v0'])
    game_objects: list[Plant] = list()
    step1 = ProgressionStep(
        ProfileVariants(SingleProfile('gr-1a'), SingleProfile('gr-1b'), perlin_variants, tx='blur'),
        ProfileVariants(
            ProfileVariants(
                ProfileVariants(SingleProfile('gr-1a-enemies-main'), None, perlin_subvar_b, tx='gap'),
                ProfileVariants(SingleProfile('gr-1a-enemies-a'), SingleProfile('gr-1a-enemies-b'), perlin_subvar_b, tx='gap'),
                perlin_subvar_a, tx='gap'
            ),
            ProfileVariants(
                ProfileVariants(SingleProfile('gr-1b-enemies-a'), SingleProfile('gr-1b-enemies-b'), perlin_subvar_b, tx='gap'),
                ProfileVariants(SingleProfile('gr-1b-enemies-main'), None, perlin_subvar_b, tx='gap'),
                perlin_subvar_a, tx='gap'
            ),
            perlin_variants, tx='gap'
        )
    )
    step2 = ProgressionStep(
        ProfileVariants(SingleProfile('gr-2a'), SingleProfile('gr-2b'), perlin_variants, tx='blur'),
        ProfileVariants(
            ProfileVariants(
                ProfileVariants(SingleProfile('gr-2a-enemies-main'), None, perlin_subvar_b, tx='gap'),
                ProfileVariants(SingleProfile('gr-2a-enemies-a'), SingleProfile('gr-2a-enemies-b'), perlin_subvar_b, tx='gap'),
                perlin_subvar_a, tx='gap'
            ),
            ProfileVariants(
                ProfileVariants(SingleProfile('gr-2b-enemies-a'), SingleProfile('gr-2b-enemies-b'), perlin_subvar_b, tx='gap'),
                ProfileVariants(SingleProfile('gr-2b-enemies-main'), None, perlin_subvar_b, tx='gap'),
                perlin_subvar_a, tx='gap'
            ),
            perlin_variants, tx='gap'
        )
    )
    step3 = ProgressionStep(SingleProfile('green'))
    step4 = ProgressionStep(SingleProfile('flowers'))
    step5 = ProgressionStep(SingleProfile('green'))
    step6 = ProgressionStep(SingleProfile('flowers'))
    step7 = ProgressionStep(SingleProfile('green'))
    stepl = ProgressionStep(SingleProfile('gr-d'))
    stepr = ProgressionStep(SingleProfile('gr-w'))
    main_progression = Progression([
        (1/7, step1),
        (2/7, step2),
        (3/7, step3),
        (4/7, step4),
        (5/7, step5),
        (6/7, step6),
        (7/7, step7),
    ], 'sw2ne', perlin_prog_tx, 5, 0.1)
    progression = Progression([
        (0.3, stepl),
        (0.7, main_progression),
        (1.0, stepr)
    ], 'nw2se', perlin_prog_tx, 5, 0.1)
    plantable_area = len(floor_tiles) * 4*4
    for pe in ['plants', 'enemies']:
        is_plants = pe == 'plants'
        generated_pes = list()
        num_seeds = int(plantable_area * progression.max_sum_seed_factor(is_plants))
        print(f'generate {pe} - {num_seeds} seeds')
        for i_seed in range(num_seeds):
            distribution_seed_index = i_seed / plantable_area

            tile = random.choice(floor_tiles)
            if is_plants and tile.crosses_middle() and i_seed % 2 == 0:
                continue  # place less plants across pathable middle
            if not is_plants and tile.min_height() != 0:
                continue  # place enemies only on reachable area
            x = random.uniform(0, 4)
            z = random.uniform(0, 4)
            map_norm_x = (rt.cur_x*tile_size_x + tile.x + x/4) / max_size_xz  # x on whole map, normalized (0-1)
            map_norm_z = (rt.cur_z*tile_size_z + tile.z + z/4) / max_size_xz  # z on whole map, normalized (0-1)

            progression_step = progression.choose_progression_step(map_norm_x, map_norm_z, 'blur' if is_plants else 'gap')
            if progression_step is None:
                continue  # progression tx gap
            profile = progression_step.get_profile(is_plants)
            if profile is None:
                continue  # no enemy profiles defined
            profile = profile.choose_profile(map_norm_x, map_norm_z)
            if profile is None:
                continue  # variant tx gap
            distribution = profile.select_plant_distribution(distribution_seed_index)
            if distribution is None:
                continue  # this profile is already finished

            template: str = random.choice(distribution.plant_templates)
            if template.startswith('tree_') and tile.crosses_middle():
                continue  # place no trees on pathable middle
            perlin_value = perlin_plants_main([map_norm_x, map_norm_z]) + 0.5*perlin_plants_underlay([map_norm_x, map_norm_z])
            probability = perlin_value*distribution.perlin_spread + 0.5+distribution.perlin_offset
            grows = random.uniform(0, 1) < probability
            if grows:
                orientation = random.uniform(0, math.tau)
                x -= 2
                z -= 2
                node_turn_angle = tile.turn_angle()
                x, z = MapgenTerrain.turn(x, z, -node_turn_angle)
                orientation -= node_turn_angle
                size = random.uniform(distribution.size_from, distribution.size_to) + distribution.size_perlin*perlin_value
                generated_pes.append(Plant(template, Position(x, 0, z, tile.node.guid), orientation, size))
        print(f'generate {pe} successful ({len(generated_pes)} {pe} generated)')
        game_objects.extend(generated_pes)
    return game_objects


def generate_region_data(size_x: int, size_z: int, args: Args, region_name, rt: RegionTiling):
    assert size_x % 4 == 0
    assert size_z % 4 == 0
    tile_size_x = int(size_x / 4)
    tile_size_z = int(size_z / 4)

    heightmap = gen_perlin_heightmap(tile_size_x, tile_size_z, args, rt)
    save_image_heightmap(heightmap, f'{args.map_name}-{region_name}')

    tiles, target_tile = generate_tiles(tile_size_x, tile_size_z, heightmap, args, rt)

    verify(tiles, target_tile, heightmap)

    terrain = make_terrain(tiles, target_tile, tile_size_x, tile_size_z)

    plants = generate_game_objects(tile_size_x, tile_size_z, tiles, args, rt)

    stitches = make_region_tile_stitches(tiles, tile_size_x, tile_size_z, rt)

    print('generate region data successful')
    return terrain, plants, stitches


def get_stitch_id(rx: int, rz: int, hv: bool, xz: int):
    assert 0 <= rx < 100
    assert 0 <= rz < 100
    assert 0 <= xz < 0x1000
    rx = str(rx).zfill(2)
    rz = str(rz).zfill(2)
    hv = '0' if hv else '1'
    stitch_range = f'0x{rx}{rz}{hv}000'
    return Hex.parse(stitch_range) + xz


def make_region_tile_stitches(tiles: list[list[Tile]], tile_size_x, tile_size_z, rt: RegionTiling):
    top = left = bottom = right = None
    if rt.cur_z > 0:  # top border
        top_tiles = [tiles[x][0] for x in range(tile_size_x)]
        node_ids = dict()
        for x, tile in enumerate(top_tiles):
            if tile.node is None:
                continue
            stitch_id = get_stitch_id(rt.cur_x, rt.cur_z-1, False, x)
            node_ids[stitch_id] = (tile.node.guid, tile.doors[0])
        top = node_ids
    if rt.cur_x > 0:  # left border
        left_tiles = [tiles[0][z] for z in range(tile_size_z)]
        node_ids = dict()
        for z, tile in enumerate(left_tiles):
            if tile.node is None:
                continue
            stitch_id = get_stitch_id(rt.cur_x-1, rt.cur_z, True, z)
            node_ids[stitch_id] = (tile.node.guid, tile.doors[1])
        left = node_ids
    if rt.cur_z+1 < rt.num_z:  # bottom border
        bottom_tiles = [tiles[x][tile_size_z-1] for x in range(tile_size_x)]
        node_ids = dict()
        for x, tile in enumerate(bottom_tiles):
            if tile.node is None:
                continue
            stitch_id = get_stitch_id(rt.cur_x, rt.cur_z, False, x)
            node_ids[stitch_id] = (tile.node.guid, tile.doors[2])
        bottom = node_ids
    if rt.cur_x+1 < rt.num_x:  # right border
        right_tiles = [tiles[tile_size_x-1][z] for z in range(tile_size_z)]
        node_ids = dict()
        for z, tile in enumerate(right_tiles):
            if tile.node is None:
                continue
            stitch_id = get_stitch_id(rt.cur_x, rt.cur_z, True, z)
            node_ids[stitch_id] = (tile.node.guid, tile.doors[3])
        right = node_ids
    return top, left, bottom, right


def generate_region(_map, region_name, size_x, size_z, args: Args, rt: RegionTiling):
    print(f'generate region {region_name} {size_x}x{size_z} ({args})')

    # generate the region!
    terrain, plants, stitches = generate_region_data(size_x, size_z, args, region_name, rt)

    # add lighting
    ambient_color = Hex(0xff8080ff)
    ambient_intensity = 0.2
    terrain.ambient_light.terrain_intensity = ambient_intensity
    terrain.ambient_light.terrain_color = ambient_color
    terrain.ambient_light.object_intensity = ambient_intensity
    terrain.ambient_light.object_color = ambient_color
    terrain.ambient_light.actor_intensity = ambient_intensity
    terrain.ambient_light.actor_color = ambient_color
    dir_lights = [
        DirectionalLight(None, Hex(0xffffffff), True, 1, True, True, DirectionalLight.direction_from_orbit_and_azimuth(225, 45)),  # daylight from south-east
        DirectionalLight(None, Hex(0xffffffff), False, 0.5, False, True, DirectionalLight.direction_from_orbit_and_azimuth(45, 45))  # counter-light from north-west
    ]

    # save
    if region_name in _map.get_regions():
        print(f'deleting existing region {region_name}')
        _map.delete_region(region_name)
        _map.gas_dir.clear_cache()
    region: Region = _map.create_region(region_name, None)
    region.terrain = terrain
    region.lights = dir_lights
    region.generated_objects_non_interactive = []

    if args.start_pos is not None:
        pos = Position(0, 0, 0, terrain.target_node.guid)
        start_group_name = args.start_pos
        _map.load_start_positions()
        if start_group_name in _map.start_positions.start_groups:
            _map.start_positions.start_groups[start_group_name].start_positions = [StartPos(1, pos, Camera(0.5, 20, 0, pos))]
        else:
            sg_id = _map.start_positions.new_start_group_id()
            _map.start_positions.start_groups[start_group_name] = StartGroup('Heightmap generated start pos', False, sg_id, 'Heightmap', [StartPos(1, pos, Camera(0.5, 20, 0, pos))])
            _map.start_positions.default = start_group_name
        region.generated_objects_non_interactive.append(
            GameObjectData('trigger_change_mood_box', placement=Placement(position=pos), common=Common([
                TriggerInstance('party_member_within_bounding_box(2,1,2,"on_every_enter")', 'mood_change("map_world_df_r0_2")')
            ]))
        )
        _map.save()

    if plants is not None:
        region.generated_objects_non_interactive.extend([
            GameObjectData(
                plant.template_name,
                placement=Placement(position=plant.position, orientation=Quaternion.rad_to_quat(plant.orientation)),
                aspect=Aspect(scale_multiplier=plant.size)
            ) for plant in plants
        ])

    if rt and (rt.num_x > 1 or rt.num_z > 1):
        top_stitches, left_stitches, bottom_stitches, right_stitches = stitches
        shg = StitchHelperGas(region.data.id, region_name)
        if top_stitches is not None:
            shg.stitch_editors.append(StitchEditor(rt.region_name(rt.cur_x, rt.cur_z-1), top_stitches))
        if left_stitches is not None:
            shg.stitch_editors.append(StitchEditor(rt.region_name(rt.cur_x-1, rt.cur_z), left_stitches))
        if bottom_stitches is not None:
            shg.stitch_editors.append(StitchEditor(rt.region_name(rt.cur_x, rt.cur_z+1), bottom_stitches))
        if right_stitches is not None:
            shg.stitch_editors.append(StitchEditor(rt.region_name(rt.cur_x+1, rt.cur_z), right_stitches))
        region.stitch_helper = shg

    region.save()
    print(f'new region {region_name} saved')


class RegionTilingArg:
    def __init__(self, num_x: int, num_z: int, gen_x_from: int, gen_x_to: int, gen_z_from: int, gen_z_to: int):
        self.num_x = num_x
        self.num_z = num_z
        self.gen_x_from = gen_x_from
        self.gen_x_to = gen_x_to
        self.gen_z_from = gen_z_from
        self.gen_z_to = gen_z_to


class RegionTiling:
    def __init__(self, num_x: int, num_z: int, cur_x: int, cur_z: int, region_basename: str):
        self.num_x = num_x
        self.num_z = num_z
        self.cur_x = cur_x
        self.cur_z = cur_z
        self.region_basename = region_basename

    def region_name(self, x, z):
        if self.num_x == 1 and self.num_z == 1:
            return self.region_basename
        return f'{self.region_basename}-x{x}z{z}'

    def cur_region_name(self):
        return self.region_name(self.cur_x, self.cur_z)


def save_image_whole_world_tile_estimation(size_x, size_z, args: Args, rt_base: RegionTilingArg):
    sampling = 4
    map_size_x = int(size_x/4*rt_base.num_x / sampling)
    map_size_z = int(size_z/4*rt_base.num_z / sampling)
    print(f'generating whole world heightmap ({map_size_x}x{map_size_z})')
    whole_world_heightmap = gen_perlin_heightmap(map_size_x, map_size_z, args, RegionTiling(1, 1, 0, 0, args.map_name), sampling)
    print(f'saving image... ({len(whole_world_heightmap)}x{len(whole_world_heightmap[0])})')
    pic = [[pt.height for pt in col] for col in whole_world_heightmap]
    for x in range(len(pic)):
        for z in range(len(pic[x])):
            px = pic[x][z]
            if args.cull_below and px <= args.cull_below:
                px = 2
            elif args.cull_above and px >= args.cull_above:
                px = 1.8
            elif -6 <= px <= 6:
                px = 0
            else:
                px = 1
            pic[x][z] = px
    save_pic(pic, f'{args.map_name} estimation {args.seed}')
    print('done')


def mapgen_heightmap(map_name, region_name, size_x, size_z, args: Args, rt_base: RegionTilingArg, print_world=False):
    print(f'mapgen heightmap {map_name}.{region_name} {size_x}x{size_z} ({args})')
    # check inputs
    assert size_x % 4 == 0
    assert size_z % 4 == 0
    if size_x * size_z > 256*256:
        # above a certain number of nodes, making terrain takes quite long
        # and actually loading it in SE takes forever (initial region recalc), maybe combinatorial issue in lighting calculation?
        print(f'warning: that\'s {int((size_x/4) * (size_z/4))} tiles in a region, I hope you are culling')

    if args.seed is None:
        args.seed = random.randint(1, 10**5)
        print(f'perlin seed: {args.seed}')

    if print_world:
        save_image_whole_world_tile_estimation(size_x, size_z, args, rt_base)

    # check map exists
    bits = Bits()
    _map = bits.maps[map_name]

    start_pos_arg = args.start_pos
    for rtx in range(rt_base.gen_x_from, rt_base.gen_x_to):
        for rtz in range(rt_base.gen_z_from, rt_base.gen_z_to):
            args.start_pos = None
            if rtx == int(rt_base.num_x/2) and rtz == int(rt_base.num_z/2):
                args.start_pos = start_pos_arg  # put start-pos in middle region
            rt = RegionTiling(rt_base.num_x, rt_base.num_z, rtx, rtz, region_name)
            generate_region(_map, rt.cur_region_name(), size_x, size_z, args, rt)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen Heightmap')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--size')
    parser.add_argument('--seed', nargs='?', type=int)
    parser.add_argument('--cull-above', nargs='?', type=float)
    parser.add_argument('--cull-below', nargs='?', type=float)
    parser.add_argument('--shape', nargs='?', choices=['smooth', 'demo', 'flat'], default='smooth')
    parser.add_argument('--start-pos', nargs='?')
    parser.add_argument('--region-tiling', nargs='?')
    parser.add_argument('--print-world', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


class Args:
    def __init__(self, args=None):
        self.map_name = args.map if args is not None else None
        self.region_name = args.region if args is not None else None
        self.seed: int = args.seed if args is not None else None
        self.cull_above: float = args.cull_above if args is not None else None
        self.cull_below: float = args.cull_below if args is not None else None
        self.shape = args.shape if args is not None else None
        self.start_pos = args.start_pos if args is not None else None

    def __str__(self):
        d = {
            'seed': self.seed,
            'cull_above': self.cull_above,
            'cull_below': self.cull_below,
            'shape': self.shape,
            'start_pos': self.start_pos,
        }
        dl = [f'{name} {value}' for name, value in d.items() if value is not None]
        return ', '.join(dl)


def parse_region_tiling(region_tiling_arg: str) -> RegionTilingArg:
    if not region_tiling_arg:
        return RegionTilingArg(1, 1, 0, 1, 0, 1)  # empty arg -> single tile
    parts = region_tiling_arg.split(':')
    nums_xz = parts[0]
    num_x, num_z = [int(x) for x in nums_xz.split('x')]
    if len(parts) == 1:
        return RegionTilingArg(num_x, num_z, 0, num_x, 0, num_z)  # "5x5" -> all 25 tiles
    gen_x, gen_z = parts[1].split(',')  # "5x5:2,2" -> generate middle tile of 5x5
    gen_x = gen_x.split('-')  # "5x5:1-4,1-4" -> generate middle 9 tiles of 5x5
    gen_x_from = int(gen_x[0])
    gen_x_to = int(gen_x[-1]) if len(gen_x) > 1 else gen_x_from+1
    gen_z = gen_z.split('-')
    gen_z_from = int(gen_z[0])
    gen_z_to = int(gen_z[-1]) if len(gen_z) > 1 else gen_z_from+1
    return RegionTilingArg(num_x, num_z, gen_x_from, gen_x_to, gen_z_from, gen_z_to)


def main(argv):
    args = parse_args(argv)
    size_x, size_z = [int(x) for x in args.size.split('x')]
    rt = parse_region_tiling(args.region_tiling)
    mapgen_heightmap(args.map, args.region, size_x, size_z, Args(args), rt, args.print_world)


if __name__ == '__main__':
    main(sys.argv[1:])
