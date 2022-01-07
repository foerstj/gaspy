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
    't_xxx_cnr_04-ccav': (0, 4, 4, 4),
    't_xxx_cnr_04-cnvx': (0, 0, 4, 0)
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
    heightmap = [[perlin([x/max_size_xz, z/max_size_xz])*2*4*3 for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]
    return heightmap


def gen_tiles(tile_size_x, tile_size_z, heightmap):
    tiles = [[Tile(x, z) for z in range(tile_size_z)] for x in range(tile_size_x)]

    # designate & apply target tile
    target_tile_x = int(tile_size_x/2)
    target_tile_z = int(tile_size_z/2)
    target_tile = tiles[target_tile_x][target_tile_z]
    target_tile.node_mesh = 't_xxx_flr_04x04-v0'
    target_tile.node_turn = 0
    heightmap[target_tile_x+0][target_tile_z+0] = 0
    heightmap[target_tile_x+0][target_tile_z+1] = 0
    heightmap[target_tile_x+1][target_tile_z+0] = 0
    heightmap[target_tile_x+1][target_tile_z+1] = 0

    # sort tiles by dist to target tile. map is generated from the target tile outwards
    all_tiles = []
    for tiles_col in tiles:
        all_tiles.extend(tiles_col)
    for tile in all_tiles:
        dx = tile.x - target_tile_x
        dz = tile.z - target_tile_z
        tile.dist2target = math.sqrt(dx*dx + dz*dz)
    all_tiles.sort(key=lambda x: x.dist2target)

    for tile in all_tiles:
        if tile.node_mesh is not None:
            continue

        tl = heightmap[tile.x+0][tile.z+0]
        tr = heightmap[tile.x+1][tile.z+0]
        bl = heightmap[tile.x+0][tile.z+1]
        br = heightmap[tile.x+1][tile.z+1]

        tl_fixed = False
        tr_fixed = False
        bl_fixed = False
        br_fixed = False
        if tile.x > 0 and tiles[tile.x-1][tile.z].node_mesh is not None:
            tl_fixed = True
            bl_fixed = True
        if tile.x+1 < tile_size_x and tiles[tile.x+1][tile.z].node_mesh is not None:
            tr_fixed = True
            br_fixed = True
        if tile.z > 0 and tiles[tile.x][tile.z-1].node_mesh is not None:
            tl_fixed = True
            tr_fixed = True
        if tile.z+1 < tile_size_z and tiles[tile.x][tile.z+1].node_mesh is not None:
            bl_fixed = True
            br_fixed = True
        assert tl_fixed or tr_fixed or bl_fixed or br_fixed

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
                turned_points = (points[(0-turn) % 4], points[(1-turn) % 4], points[(2-turn) % 4], points[(3-turn) % 4])
                hs = [fixed_base, fixed_base-4]
                random.shuffle(hs)
                for h in hs:
                    tn_tl = turned_points[1]+h
                    tn_tr = turned_points[0]+h
                    tn_bl = turned_points[2]+h
                    tn_br = turned_points[3]+h
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
        assert len(node_fits) > 0
        node_fits.sort(key=lambda x: x[2])  # sort by fit
        mesh, turn, fit, points = node_fits[0]

        # apply found node
        tile.node_mesh = mesh
        tile.node_turn = turn
        tl, tr, bl, br = points
        heightmap[tile.x+0][tile.z+0] = tl
        heightmap[tile.x+1][tile.z+0] = tr
        heightmap[tile.x+0][tile.z+1] = bl
        heightmap[tile.x+1][tile.z+1] = br

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
