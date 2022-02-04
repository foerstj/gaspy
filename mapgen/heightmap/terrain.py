from __future__ import annotations

import math
import random

from bits.terrain import Terrain, TerrainNode
from mapgen.heightmap.args import Args, RegionTiling
from mapgen.heightmap.perlin import make_perlin
from mapgen.heightmap.save_image import save_image


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
    def __init__(self, x: int, z: int, main_height: float, base_height: float, height=None, pre_fixed=False, heightmap: list[list[Point]] = None):
        self.x = x
        self.z = z
        self.input_main_height = main_height
        self.base_height = base_height
        self.main_height = main_height
        if height is None:
            height = main_height + base_height
        self.height = height
        self.heightmap = heightmap
        self.tile_tl = None
        self.tile_tr = None
        self.tile_bl = None
        self.tile_br = None
        self.pre_fixed = pre_fixed

    def set_height(self, height: float):
        if self.pre_fixed:
            assert height == self.height, f'tried to set height from {self.height} to {height} on fixed point ({self.x}|{self.z})'
        else:
            self.height = height
            self.main_height = self.height - self.base_height

    def tiles(self) -> list[NodeTile]:
        tiles: list[NodeTile] = [self.tile_tl, self.tile_tr, self.tile_bl, self.tile_br]
        tiles = [t for t in tiles if t is not None]
        return tiles

    def num_assigned_nodes(self) -> int:
        return sum([1 if tile.node_mesh is not None else 0 for tile in self.tiles()])

    def clear(self):
        assert not self.pre_fixed
        for t in self.tiles():
            t.node_mesh = None
        self.main_height = self.input_main_height
        self.height = self.main_height + self.base_height

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

    def flatten_the_curve(self, max_dist=7, max_diff=12):
        for x in range(max(0, self.x - max_dist), min(len(self.heightmap), self.x + max_dist)):
            for z in range(max(0, self.z - max_dist), min(len(self.heightmap[x]), self.z + max_dist)):
                point = self.heightmap[x][z]
                dist = max(abs(x - self.x), abs(z - self.z))
                point.set_height(max_apart(point.height, self.height, max_diff * dist))


class NodeTile:
    def __init__(self, x, z, heightmap: list[list[Point]], tiles: list[list[NodeTile]] = None):
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
        self.avg_main_height = self.avg_main_height()  # used to determine tile generation order
        self.dist2center = None
        self.node_mesh = None
        self.node_turn = None  # number of times the node is turned counter-clockwise (0-3)
        self.node_base_height = None
        self.fail_count = 0
        self.node = None
        self.doors = None  # doors of turned node in order top-left-bottom-right
        self.connected_to_target = False
        self.is_culled = False

    def __str__(self):
        return f'({self.x}|{self.z}): {self.node_mesh}'

    def points(self) -> list[Point]:
        return [self.point_tl, self.point_tr, self.point_bl, self.point_br]

    def avg_main_height(self):
        return avg(*[p.main_height for p in self.points()])

    def min_height(self):
        return min(*[p.height for p in self.points()])

    def max_height(self):
        return max(*[p.height for p in self.points()])

    def min_main_height(self):
        return min(*[p.main_height for p in self.points()])

    def max_main_height(self):
        return max(*[p.main_height for p in self.points()])

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

    def neighbor_tiles(self) -> list[NodeTile]:
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
            if point.input_main_height <= 0:
                below = True
            if point.input_main_height >= 0:
                above = True
        return above and below

    def set_culled(self):
        self.is_culled = True
        if not self.has_pre_fixed_point():
            self.node_mesh = 'EMPTY'  # don't actually cull nodes on region border. greatly reduces risk of separated nodes


def gen_perlin_heightmap_flat(tile_size_x: int, tile_size_z: int) -> list[list[float]]:
    # completely flat, for testing purposes (plant distributions better visible)
    heightmap = [[0 for _ in range(tile_size_z+1)] for _ in range(tile_size_x+1)]
    return heightmap


def gen_perlin_values(tile_size_x: int, tile_size_z: int, args: Args, rt: RegionTiling, octaves_per_km: float) -> list[list[float]]:
    max_size_xz = max(tile_size_x*rt.num_x, tile_size_z*rt.num_z)
    perlin = make_perlin(args.seed, max_size_xz, octaves_per_km)
    coord_shift = 0.00000001  # mitigate bug in perlin-noise lib (wtf)
    heightmap = [[perlin([(rt.cur_x*tile_size_x + x)/max_size_xz + coord_shift, (rt.cur_z*tile_size_z + z)/max_size_xz + coord_shift]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]
    return heightmap


def gen_perlin_heightmap_smooth(tile_size_x: int, tile_size_z: int, args: Args, rt: RegionTiling, octaves_per_km=3.5, height=4*8) -> list[list[float]]:
    # default shape, a simple smooth perlin heightmap
    perlin_values = gen_perlin_values(tile_size_x, tile_size_z, args, rt, octaves_per_km)
    heightmap = [[point*2 for point in col] for col in perlin_values]  # -1 .. +1
    heightmap = [[point*height for point in col] for col in heightmap]  # -32 .. +32  # max 8 levels up and down from mid-level
    return heightmap


def gen_perlin_heightmap_demo(tile_size_x: int, tile_size_z: int, args: Args, rt: RegionTiling, sampling=1) -> list[list[float]]:
    # this shape is for me to play around with
    # sampling param is for generating overview image
    octaves_per_km = 2
    perlin_values = gen_perlin_values(tile_size_x, tile_size_z, args, rt, octaves_per_km)

    map_size_x = tile_size_x*rt.num_x + 1
    map_size_z = tile_size_z*rt.num_z + 1
    max_size_xz = max(map_size_x, map_size_z)

    heightmap = [[0.0 for _ in range(tile_size_z+1)] for _ in range(tile_size_x+1)]  # create array
    for x in range(tile_size_x+1):
        map_x = rt.cur_x * tile_size_x + x
        for z in range(tile_size_z+1):
            map_z = rt.cur_z*tile_size_z + z
            perlin_value = perlin_values[x][z]
            height = perlin_value  # -0.5 .. 0.5
            height *= 2  # -1 .. 1
            height *= 4  # -4 .. +4  # small node wall height
            height *= 40  # basic steepness of the map that gives a good relation of playable area and cutoffs
            if -12 < height < 12:
                height /= 3  # flatten play-area
            if -3 < height < 3:
                height /= 3  # flatten middle even more
            if height < -16:
                height *= 1.5  # steeper drop-offs to reach culling height more quickly
                height += 12 - height % 12  # multiples of 12 to hopefully make it easier for node-fitting
                height = min(-24.0, height)  # just to make sure

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

    if args.base_heightmap:
        base_heightmap_values = gen_perlin_heightmap_smooth(tile_size_x, tile_size_z, args, rt, 3, 4*2)
    else:
        base_heightmap_values = gen_perlin_heightmap_flat(tile_size_x, tile_size_z)

    heightmap_points = [[Point(x, z, heightmap_values[x][z], base_heightmap_values[x][z]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]
    for x in range(tile_size_x+1):
        for z in range(tile_size_z+1):
            heightmap_points[x][z].heightmap = heightmap_points

    # culled anyway -> flatten to relieve the algo
    if args.cull_below is not None or args.cull_above is not None:
        for col in heightmap_points:
            for point in col:
                if args.cull_above is not None:
                    point.set_height(min(point.height, args.cull_above + 4))
                if args.cull_below is not None:
                    point.set_height(max(point.height, args.cull_below - 4))

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


def generate_tile(tile: NodeTile, tiles: list[list[NodeTile]], tile_size_x: int, tile_size_z: int, last_try=False):
    assert tile.node_mesh is (None if not last_try else 'EMPTY')

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
    elif last_try:
        return True
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


def pre_fix_border(border: list[Point]):
    for point in border:
        point.set_height(round(point.height / 4) * 4)

    border[0].pre_fixed = True
    border[-1].pre_fixed = True
    border[1].set_height(border[0].height)
    border[1].pre_fixed = True
    border[-2].set_height(border[-1].height)
    border[-2].pre_fixed = True

    border[1].flatten_the_curve()
    border[-2].flatten_the_curve()
    for point in sorted(border, key=lambda x: abs(x.height)):
        point.flatten_the_curve()
        point.pre_fixed = True


def pre_fix_borders(heightmap: list[list[Point]], tile_size_x, tile_size_z):
    # pre-fix outer points to make region tiling possible (generating multiple regions that are stitchable)
    top = [heightmap[x][0] for x in range(tile_size_x+1)]
    bottom = [heightmap[x][tile_size_z] for x in range(tile_size_x+1)]
    left = [heightmap[0][z] for z in range(tile_size_z+1)]
    right = [heightmap[tile_size_x][z] for z in range(tile_size_z+1)]
    for border in [top, bottom, left, right]:
        pre_fix_border(border)


def generate_tiles(tile_size_x: int, tile_size_z: int, heightmap: list[list[Point]], args: Args, rt: RegionTiling, num_tries=5):
    pre_fix_borders(heightmap, tile_size_x, tile_size_z)
    # operation: "flatten the curve" for whole heightmap
    all_points = []
    for x in range(tile_size_x+1):
        all_points.extend(heightmap[x])
    for point in sorted(all_points, key=lambda p: abs(p.height)):
        point.flatten_the_curve()

    best_tiles = None
    best_target_tile = None
    best_gap_count = tile_size_x*tile_size_z
    best_heightmap = None

    i_try = 0
    while i_try < num_tries or i_try < best_gap_count/2:
        i_try += 1
        try_heightmap = [[Point(p.x, p.z, p.main_height, p.base_height, p.height, p.pre_fixed) for p in col] for col in heightmap]
        for col in try_heightmap:
            for point in col:
                point.heightmap = try_heightmap

        tiles, target_tile, gap_count = do_generate_tiles(tile_size_x, tile_size_z, try_heightmap, args)
        if gap_count < best_gap_count:
            best_tiles = tiles
            best_target_tile = target_tile
            best_gap_count = gap_count
            best_heightmap = try_heightmap
        if gap_count == 0:
            break

    print(f'using tiles with {best_gap_count} gaps')
    for x in range(tile_size_x+1):
        for z in range(tile_size_z+1):
            heightmap[x][z].set_height(best_heightmap[x][z].height)
            heightmap[x][z].tile_tl = best_heightmap[x][z].tile_tl
            heightmap[x][z].tile_tr = best_heightmap[x][z].tile_tr
            heightmap[x][z].tile_bl = best_heightmap[x][z].tile_bl
            heightmap[x][z].tile_br = best_heightmap[x][z].tile_br

    save_image_tiles(best_tiles, f'{args.map_name}-{rt.cur_region_name()}')
    return best_tiles, best_target_tile


def do_generate_tiles(tile_size_x: int, tile_size_z: int, heightmap: list[list[Point]], args: Args):
    tiles = [[NodeTile(x, z, heightmap) for z in range(tile_size_z)] for x in range(tile_size_x)]
    for x in range(tile_size_x):
        for z in range(tile_size_z):
            tiles[x][z].tiles = tiles

    all_tiles = []
    for tiles_col in tiles:
        all_tiles.extend(tiles_col)
    for tile in all_tiles:
        dx = abs((tile_size_x/2) - (tile.x + 0.5))
        dz = abs((tile_size_z/2) - (tile.z + 0.5))
        tile.dist2center = math.sqrt(dx * dx + dz * dz)
    # sort from mid-level to lowest/highest. map is generated from the mid-level out since mid-level is probably where the player would walk around
    all_tiles.sort(key=lambda x: abs(x.avg_main_height))

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

    for tile in all_tiles:
        if tile.node_mesh == 'EMPTY':
            generate_tile(tile, tiles, tile_size_x, tile_size_z, True)  # try one last time

    num_empty = sum([1 if tile.node_mesh == 'EMPTY' else 0 for tile in all_tiles])
    print(f'tiles generated ({num_empty} empty)')

    # culling
    if args.cull_above is not None or args.cull_below is not None:
        for x in range(tile_size_x):
            for z in range(tile_size_z):
                tile = tiles[x][z]
                if args.cull_above is not None and tile.min_height() >= args.cull_above:
                    tile.set_culled()
                if args.cull_below is not None and tile.max_height() <= args.cull_below:
                    tile.set_culled()
        node_count = len([tile for tile in all_tiles if tile.node_mesh != 'EMPTY'])
        cull_count = len([tile for tile in all_tiles if tile.is_culled])
        num_tiles = tile_size_x * tile_size_z
        cull_percent = 100 * cull_count / num_tiles
        print(f'culled {cull_count} tiles ({cull_percent}%), {node_count} nodes remaining')

    # erase lonely tiles
    for tile in all_tiles:
        if tile.node_mesh != 'EMPTY':
            if len([t for t in tile.neighbor_tiles() if t.node_mesh != 'EMPTY']) == 0:
                print(f'erasing lonely tile ({tile.x}|{tile.z})')
                tile.node_mesh = 'EMPTY'

    # find a suitable target tile
    target_candidates = [t for t in all_tiles if t.node_mesh == 't_xxx_flr_04x04-v0']
    target_candidates.sort(key=lambda x: x.dist2center)
    target_tile = target_candidates[0]
    target_tile.node_turn = 0
    print(f'target tile: ({target_tile.x} | {target_tile.z})')

    # erase unconnected tiles
    compute_connection_to_target(target_tile)
    unconnected_tiles = [tile for tile in all_tiles if tile.node_mesh != 'EMPTY' and not tile.connected_to_target]
    if len(unconnected_tiles) > 0:
        print(f'erasing {len(unconnected_tiles)} unconnected tiles')
        node_count = sum([1 if tile.node_mesh != 'EMPTY' else 0 for tile in all_tiles])
        assert tiles[0][0].node_mesh != 'EMPTY' and tiles[0][0] not in unconnected_tiles
        assert len(unconnected_tiles) < node_count / 10
        for tile in unconnected_tiles:
            tile.node_mesh = 'EMPTY'

    gap_count = len([tile for tile in all_tiles if tile.node_mesh == 'EMPTY' and not tile.is_culled])
    print(f'generate tiles successful - {gap_count} gaps')
    return tiles, target_tile, gap_count


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


def compute_connection_to_target(target_tile: NodeTile):
    target_tile.connected_to_target = True
    tiles_list = [target_tile]
    while len(tiles_list) > 0:
        tile = tiles_list.pop(0)
        new_neighbor_tiles = [t for t in tile.neighbor_tiles() if t.node_mesh != 'EMPTY' and not t.connected_to_target]
        for nt in new_neighbor_tiles:
            nt.connected_to_target = True
        tiles_list.extend(new_neighbor_tiles)


def verify(tiles: list[list[NodeTile]], target_tile: NodeTile, heightmap: list[list[Point]]):
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


def all_tiles_culled(tiles: list[list[NodeTile]]):
    for col in tiles:
        for tile in col:
            if not tile.is_culled:
                return False
    return True


def save_image_heightmap(heightmap: list[list[Point]], file_name_prefix):
    pic = [[pt.height for pt in col] for col in heightmap]
    save_image(pic, f'{file_name_prefix} heightmap')


def save_image_tiles(tiles: list[list[NodeTile]], file_name_prefix):
    pic = [[0 if tile.node_mesh == 'EMPTY' else 1 if tile.node_mesh.startswith('t_xxx_flr') else 0.5 for tile in col] for col in tiles]
    save_image(pic, f'{file_name_prefix} tiles')
