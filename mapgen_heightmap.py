import argparse
import math
import random
import sys

from perlin_noise import PerlinNoise

from bits import Bits
from gas import Hex
from region import DirectionalLight
from terrain import TerrainNode, Terrain

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


class Tile:
    def __init__(self, x, z, heightmap):
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
        self.height = self.calc_height()
        self.node_mesh = None
        self.node_turn = None
        self.node_base_height = None
        self.fail_count = 0
        self.node = None
        self.doors = None

    def calc_height(self):
        tl = self.point_tl.height
        tr = self.point_tr.height
        bl = self.point_bl.height
        br = self.point_br.height
        return max(tl, tr, bl, br)


class Point:
    def __init__(self, x: int, z: int, height: float):
        self.x = x
        self.z = z
        self.height = height
        self.tile_tl = None
        self.tile_tr = None
        self.tile_bl = None
        self.tile_br = None


def gen_perlin_heightmap(tile_size_x, tile_size_z, seed=None) -> list[list[Point]]:
    max_size_xz = max(tile_size_x, tile_size_z)
    octaves = max_size_xz * 4 / 1000 * 12  # 12 octaves per km
    print(f'perlin octaves: {octaves}')
    perlin = PerlinNoise(octaves, seed)
    heightmap = [[perlin([x/max_size_xz, z/max_size_xz]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]  # -0.5 .. +0.5
    heightmap = [[point*2 for point in col] for col in heightmap]  # -1 .. +1
    heightmap = [[point*4 for point in col] for col in heightmap]  # -4 .. +4  # small node wall height
    heightmap = [[point*8 for point in col] for col in heightmap]  # -32 .. +32  # max 8 levels up and down from mid-level
    return [[Point(x, z, heightmap[x][z]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]


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
        avg_height = (tl + tr + bl + br) / 4
        fixed_base_height = round(avg_height / 4) * 4

    # find best-fitting node
    node_fits = list()
    nodes = list(NODES.items())
    random.shuffle(nodes)
    for mesh, points in nodes:
        turns = list(range(0, 4))
        random.shuffle(turns)
        for turn in turns:
            turned_points = (points[(0 - turn) % 4], points[(1 - turn) % 4], points[(2 - turn) % 4], points[(3 - turn) % 4])
            for base_height in [fixed_base_height, fixed_base_height - 4, fixed_base_height - 8, fixed_base_height - 12]:
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


def gen_tile(tile: Tile, tiles: list[list[Tile]], tile_size_x: int, tile_size_z: int):
    tl = tile.point_tl.height
    tr = tile.point_tr.height
    bl = tile.point_bl.height
    br = tile.point_br.height

    tl_fixed = 0
    tr_fixed = 0
    bl_fixed = 0
    br_fixed = 0
    if tile.x > 0 and tile.z > 0 and tiles[tile.x - 1][tile.z - 1].node_mesh is not None:  # top left
        tl_fixed += 1
    if tile.z > 0 and tiles[tile.x][tile.z - 1].node_mesh is not None:  # top
        tl_fixed += 1
        tr_fixed += 1
    if tile.x + 1 < tile_size_x and tile.z > 0 and tiles[tile.x + 1][tile.z - 1].node_mesh is not None:  # top right
        tr_fixed += 1
    if tile.x > 0 and tiles[tile.x - 1][tile.z].node_mesh is not None:  # left
        tl_fixed += 1
        bl_fixed += 1
    if tile.x + 1 < tile_size_x and tiles[tile.x + 1][tile.z].node_mesh is not None:  # right
        tr_fixed += 1
        br_fixed += 1
    if tile.x > 0 and tile.z + 1 < tile_size_z and tiles[tile.x - 1][tile.z + 1].node_mesh is not None:  # bottom left
        bl_fixed += 1
    if tile.z + 1 < tile_size_z and tiles[tile.x][tile.z + 1].node_mesh is not None:  # bottom
        bl_fixed += 1
        br_fixed += 1
    if tile.x + 1 < tile_size_x and tile.z + 1 < tile_size_z and tiles[tile.x + 1][tile.z + 1].node_mesh is not None:  # bottom right
        br_fixed += 1

    # find best-fitting node
    best_fit = fit_nodes(tl, tl_fixed, tr, tr_fixed, bl, bl_fixed, br, br_fixed)

    if best_fit is not None:
        mesh, turn, height, fit, points = best_fit

        # apply found node
        tile.node_mesh = mesh
        tile.node_turn = turn
        tile.node_base_height = height
        tl, tr, bl, br = points
        tile.point_tl.height = tl
        tile.point_tr.height = tr
        tile.point_bl.height = bl
        tile.point_br.height = br
        return False
    else:
        print(f'{(tile.x, tile.z)}: no fit found for TR-TL-BL-BR {((tr, tr_fixed), (tl, tl_fixed), (bl, bl_fixed), (br, br_fixed))}')
        # pick a fixed point and un-fix it by deleting the surrounding nodes
        fixed_points = [
            (0, 0, tl_fixed) if tl_fixed else None,
            (1, 0, tr_fixed) if tr_fixed else None,
            (0, 1, bl_fixed) if bl_fixed else None,
            (1, 1, br_fixed) if br_fixed else None,
        ]
        fixed_points = [p for p in fixed_points if p is not None]
        random.shuffle(fixed_points)
        x, z, fixed = fixed_points[0]
        print(f'un-fixing point {(x, z)}')

        x += tile.x
        z += tile.z
        if x > 0 and z > 0:
            t = tiles[x-1][z-1]
            t.node_mesh = None
        if x < tile_size_x and z > 0:
            t = tiles[x-0][z-1]
            t.node_mesh = None
        if x > 0 and z < tile_size_z:
            t = tiles[x-1][z-0]
            t.node_mesh = None
        if x < tile_size_x and z < tile_size_z:
            t = tiles[x-0][z-0]
            t.node_mesh = None

        gen_tile(tile, tiles, tile_size_x, tile_size_z)  # try again with fewer constraints
        tile.fail_count += 1
        return True  # restart to re-generate all deleted tiles


def gen_tiles(tile_size_x, tile_size_z, heightmap: list[list[Point]]):
    tiles = [[Tile(x, z, heightmap) for z in range(tile_size_z)] for x in range(tile_size_x)]

    # designate & apply target tile
    target_tile_x = int(tile_size_x/2)
    target_tile_z = int(tile_size_z/2)
    target_tile = tiles[target_tile_x][target_tile_z]
    target_tile.node_mesh = 't_xxx_flr_04x04-v0'
    target_tile.node_turn = 0
    avg_height = (target_tile.point_tl.height + target_tile.point_tr.height + target_tile.point_bl.height + target_tile.point_br.height) / 4
    target_tile_height = round(avg_height / 4) * 4
    target_tile.point_tl.height = target_tile_height
    target_tile.point_tr.height = target_tile_height
    target_tile.point_bl.height = target_tile_height
    target_tile.point_br.height = target_tile_height
    target_tile.node_base_height = target_tile_height

    # sort from mid-level to lowest/highest. map is generated from the mid-level out since mid-level is probably where the player would walk around
    all_tiles = []
    for tiles_col in tiles:
        all_tiles.extend(tiles_col)
    all_tiles.sort(key=lambda x: abs(x.height))

    i = 0
    while True:
        tile = all_tiles[i]
        i += 1
        if tile.node_mesh is not None:
            continue
        if tile.fail_count >= 13:
            tile.node_mesh = 'EMPTY'  # give up
            continue
        need_backtrack = gen_tile(tile, tiles, tile_size_x, tile_size_z)
        if need_backtrack:
            i = 0
        if i >= len(all_tiles):
            break
    num_empty = sum([1 if tile.node_mesh == 'EMPTY' else 0 for tile in all_tiles])
    print(f'generate tiles successful ({num_empty} empty)')

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


def verify(tiles: list[list[Tile]], target_tile: Tile, heightmap: list[list[Point]]):
    for tile_row in tiles:
        for tile in tile_row:
            if tile.node_mesh == 'EMPTY':
                continue
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


def gen_terrain(size_x, size_z, seed=None):
    assert size_x % 4 == 0
    assert size_z % 4 == 0
    tile_size_x = int(size_x / 4)
    tile_size_z = int(size_z / 4)

    heightmap = gen_perlin_heightmap(tile_size_x, tile_size_z, seed)

    tiles, target_tile = gen_tiles(tile_size_x, tile_size_z, heightmap)

    verify(tiles, target_tile, heightmap)

    terrain = make_terrain(tiles, target_tile, tile_size_x, tile_size_z)

    print('generate terrain successful')
    return terrain


def mapgen_heightmap(map_name, region_name, size_x, size_z, seed=None):
    print(f'mapgen heightmap {map_name}.{region_name} {size_x}x{size_z}' + f' (seed {seed})' if seed is not None else '')
    # check inputs
    assert size_x % 4 == 0
    assert size_z % 4 == 0
    assert size_x * size_z <= 65536  # no larger than 256x256 plz, that's 64x64=4096 nodes

    # check map exists
    bits = Bits()
    _map = bits.maps[map_name]

    # generate the terrain!
    terrain = gen_terrain(size_x, size_z, seed)

    # add lighting
    terrain.ambient_light.intensity = 0.2
    terrain.ambient_light.object_intensity = 0.2
    terrain.ambient_light.actor_intensity = 0.2
    dir_lights = [
        DirectionalLight(None, Hex(0xffffffff), True, 1, True, True, (0, math.cos(math.tau / 8), math.sin(math.tau / 8))),
        DirectionalLight(None, Hex(0xffccccff), False, 0.7, False, False, (0, math.cos(-math.tau / 8), math.sin(-math.tau / 8)))
    ]

    # save
    if region_name in _map.get_regions():
        print('deleting existing region')
        _map.delete_region(region_name)
        _map.gas_dir.clear_cache()
    region = _map.create_region(region_name, None)
    region.terrain = terrain
    region.lights = dir_lights
    region.save()
    print('new region saved')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen Heightmap')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--size')
    parser.add_argument('--seed', nargs='?')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    size_x, size_z = [int(x) for x in args.size.split('x')]
    mapgen_heightmap(args.map, args.region, size_x, size_z, args.seed)


if __name__ == '__main__':
    main(sys.argv[1:])
