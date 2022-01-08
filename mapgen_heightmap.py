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
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.node_mesh = None
        self.node_turn = None
        self.dist2target = None
        self.node = None
        self.doors = None


def gen_perlin_heightmap(tile_size_x, tile_size_z):
    max_size_xz = max(tile_size_x, tile_size_z)
    octaves = math.sqrt(max_size_xz) / 2
    print('perlin octaves: ' + str(octaves))
    perlin = PerlinNoise(octaves)
    heightmap = [[perlin([x/max_size_xz, z/max_size_xz])*2*4*8 for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]
    return heightmap


def fit_nodes(tl, tl_fixed, tr, tr_fixed, bl, bl_fixed, br, br_fixed):
    fixed_heights = [
        tl if tl_fixed else None,
        tr if tr_fixed else None,
        bl if bl_fixed else None,
        br if br_fixed else None,
    ]
    fixed_heights = [p for p in fixed_heights if p is not None]
    fixed_base = min(fixed_heights)

    # find best-fitting node
    node_fits = list()
    nodes = list(NODES.items())
    random.shuffle(nodes)
    for mesh, points in nodes:
        turns = list(range(0, 4))
        random.shuffle(turns)
        for turn in turns:
            turned_points = (points[(0 - turn) % 4], points[(1 - turn) % 4], points[(2 - turn) % 4], points[(3 - turn) % 4])
            for h in [fixed_base, fixed_base - 4, fixed_base - 8, fixed_base - 12]:
                tn_tl = turned_points[1] + h
                tn_tr = turned_points[0] + h
                tn_bl = turned_points[2] + h
                tn_br = turned_points[3] + h
                if tl_fixed and tn_tl != tl:
                    continue
                if tr_fixed and tn_tr != tr:
                    continue
                if bl_fixed and tn_bl != bl:
                    continue
                if br_fixed and tn_br != br:
                    continue
                fit = abs(tl - tn_tl) + abs(tr - tn_tr) + abs(bl - tn_bl) + abs(br - tn_br)
                node_fits.append((mesh, turn, fit, (tn_tl, tn_tr, tn_bl, tn_br)))
    node_fits.sort(key=lambda x: x[2])  # sort by fit
    return node_fits[0] if len(node_fits) > 0 else None


def gen_tile(tile, tiles, heightmap, tile_size_x, tile_size_z):
    tl = heightmap[tile.x + 0][tile.z + 0]
    tr = heightmap[tile.x + 1][tile.z + 0]
    bl = heightmap[tile.x + 0][tile.z + 1]
    br = heightmap[tile.x + 1][tile.z + 1]

    tl_fixed = 0
    tr_fixed = 0
    bl_fixed = 0
    br_fixed = 0
    if tile.x > 0 and tiles[tile.x - 1][tile.z].node_mesh is not None:  # left
        tl_fixed += 1
        bl_fixed += 1
    if tile.x + 1 < tile_size_x and tiles[tile.x + 1][tile.z].node_mesh is not None:  # right
        tr_fixed += 1
        br_fixed += 1
    if tile.z > 0 and tiles[tile.x][tile.z - 1].node_mesh is not None:  # top
        tl_fixed += 1
        tr_fixed += 1
    if tile.z + 1 < tile_size_z and tiles[tile.x][tile.z + 1].node_mesh is not None:  # bottom
        bl_fixed += 1
        br_fixed += 1
    assert tl_fixed or tr_fixed or bl_fixed or br_fixed

    # find best-fitting node
    best_fit = fit_nodes(tl, tl_fixed, tr, tr_fixed, bl, bl_fixed, br, br_fixed)

    if best_fit is not None:
        mesh, turn, fit, points = best_fit

        # apply found node
        tile.node_mesh = mesh
        tile.node_turn = turn
        tl, tr, bl, br = points
        heightmap[tile.x + 0][tile.z + 0] = tl
        heightmap[tile.x + 1][tile.z + 0] = tr
        heightmap[tile.x + 0][tile.z + 1] = bl
        heightmap[tile.x + 1][tile.z + 1] = br
        return False
    else:
        print(repr((tile.x, tile.z)) + ': no fit found for TR-TL-BL-BR ' + repr(((tr, tr_fixed), (tl, tl_fixed), (bl, bl_fixed), (br, br_fixed))))
        # pick a fixed point and un-fix it by deleting the surrounding nodes
        fixed_points = [
            (0, 0, tl_fixed) if tl_fixed else None,
            (1, 0, tr_fixed) if tr_fixed else None,
            (0, 1, bl_fixed) if bl_fixed else None,
            (1, 1, br_fixed) if br_fixed else None,
        ]
        fixed_points = [p for p in fixed_points if p is not None]
        random.shuffle(fixed_points)
        fixed_points.sort(key=lambda x: x[2])  # sort by fixed (num nodes)
        x, z, fixed = fixed_points[0]  # avoid unfixing the point with the most nodes
        print('un-fixing point ' + repr((x, z)))

        x += tile.x
        z += tile.z
        if x > 0 and z > 0:
            tiles[x-1][z-1].node_mesh = None
        if x < tile_size_x and z > 0:
            tiles[x-0][z-1].node_mesh = None
        if x > 0 and z < tile_size_z:
            tiles[x-1][z-0].node_mesh = None
        if x < tile_size_x and z < tile_size_z:
            tiles[x-0][z-0].node_mesh = None

        gen_tile(tile, tiles, heightmap, tile_size_x, tile_size_z)  # try again with fewer constraints
        return True  # restart to re-generate all deleted tiles


def gen_tiles(tile_size_x, tile_size_z, heightmap: list[list[float]]):
    tiles = [[Tile(x, z) for z in range(tile_size_z)] for x in range(tile_size_x)]

    # designate & apply target tile
    target_tile_x = int(tile_size_x/2)
    target_tile_z = int(tile_size_z/2)
    target_tile = tiles[target_tile_x][target_tile_z]
    target_tile.node_mesh = 't_xxx_flr_04x04-v0'
    target_tile.node_turn = 0
    avg_height = (heightmap[target_tile_x+0][target_tile_z+0] + heightmap[target_tile_x+0][target_tile_z+1] + heightmap[target_tile_x+1][target_tile_z+0] + heightmap[target_tile_x+1][target_tile_z+1]) / 4
    target_tile_height = round(avg_height / 4) * 4
    heightmap[target_tile_x+0][target_tile_z+0] = target_tile_height
    heightmap[target_tile_x+0][target_tile_z+1] = target_tile_height
    heightmap[target_tile_x+1][target_tile_z+0] = target_tile_height
    heightmap[target_tile_x+1][target_tile_z+1] = target_tile_height

    # sort tiles by dist to target tile. map is generated from the target tile outwards
    all_tiles = []
    for tiles_col in tiles:
        all_tiles.extend(tiles_col)
    for tile in all_tiles:
        dx = tile.x - target_tile_x
        dz = tile.z - target_tile_z
        tile.dist2target = math.sqrt(dx*dx + dz*dz)
    all_tiles.sort(key=lambda x: x.dist2target)

    i = 0
    while True:
        tile = all_tiles[i]
        i += 1
        if tile.node_mesh is not None:
            continue
        need_backtrack = gen_tile(tile, tiles, heightmap, tile_size_x, tile_size_z)
        if need_backtrack:
            i = 0
        if i >= len(all_tiles):
            break

    return tiles, target_tile


def make_terrain(tiles, target_tile, tile_size_x, tile_size_z):
    terrain = Terrain()
    for x in range(0, tile_size_x):
        for z in range(0, tile_size_z):
            tile = tiles[x][z]
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
            if x > 0:
                nnt = tiles[x-1][z]
                node.connect_doors(nt.doors[1], nnt.node, nnt.doors[3])
            if x < tile_size_x-1:
                nnt = tiles[x+1][z]
                node.connect_doors(nt.doors[3], nnt.node, nnt.doors[1])
            if z > 0:
                nnt = tiles[x][z-1]
                node.connect_doors(nt.doors[0], nnt.node, nnt.doors[2])
            if z < tile_size_z-1:
                nnt = tiles[x][z+1]
                node.connect_doors(nt.doors[2], nnt.node, nnt.doors[0])

    return terrain


def gen_terrain(size_x, size_z):
    assert size_x % 4 == 0
    assert size_z % 4 == 0
    tile_size_x = int(size_x / 4)
    tile_size_z = int(size_z / 4)

    heightmap = gen_perlin_heightmap(tile_size_x, tile_size_z)

    tiles, target_tile = gen_tiles(tile_size_x, tile_size_z, heightmap)

    return make_terrain(tiles, target_tile, tile_size_x, tile_size_z)


def mapgen_heightmap(map_name, region_name, size_x, size_z):
    # check inputs
    assert size_x % 4 == 0
    assert size_z % 4 == 0

    # check map exists
    bits = Bits()
    _map = bits.maps[map_name]

    # generate the terrain!
    terrain = gen_terrain(size_x, size_z)

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
        _map.delete_region(region_name)
        _map.gas_dir.clear_cache()
    region = _map.create_region(region_name, None)
    region.terrain = terrain
    region.lights = dir_lights
    region.save()


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    mapgen_heightmap(map_name, region_name, 256, 192)


if __name__ == '__main__':
    main(sys.argv[1:])
