from __future__ import annotations

import argparse
import math
import random
import sys

from perlin_noise import PerlinNoise

from bits import Bits
from game_object_data import GameObjectData, Placement, Common, TriggerInstance, Aspect
from gas import Hex, Position
from mapgen_terrain import MapgenTerrain
from plant_gen import Plant
from region import DirectionalLight
from start_positions import StartPos, StartGroup, Camera
from terrain import TerrainNode, Terrain

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
    def __init__(self, x, z, heightmap: list[list[Point]]):
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
        self.height = self.avg_height()  # used to determine tile generation order
        self.dist2center = None
        self.node_mesh = None
        self.node_turn = None  # number of times the node is turned counter-clockwise (0-3)
        self.node_base_height = None
        self.fail_count = 0
        self.node = None
        self.doors = None

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


def gen_perlin_heightmap_smooth(tile_size_x: int, tile_size_z: int, args: Args) -> list[list[float]]:
    # default shape, a simple smooth perlin heightmap
    max_size_xz = max(tile_size_x, tile_size_z)
    octaves_per_km = 12
    octaves = max_size_xz * 4 / 1000 * octaves_per_km
    print(f'terrain perlin octaves: {octaves}')
    perlin = PerlinNoise(octaves, args.seed)
    heightmap = [[perlin([x/max_size_xz, z/max_size_xz]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]  # -0.5 .. +0.5
    heightmap = [[point*2 for point in col] for col in heightmap]  # -1 .. +1
    heightmap = [[point*4 for point in col] for col in heightmap]  # -4 .. +4  # small node wall height
    heightmap = [[point*8 for point in col] for col in heightmap]  # -32 .. +32  # max 8 levels up and down from mid-level
    return heightmap


def gen_perlin_heightmap_demo(tile_size_x: int, tile_size_z: int, args: Args) -> list[list[float]]:
    # this shape is for me to play around with
    max_size_xz = max(tile_size_x, tile_size_z)
    octaves_per_km = 4
    octaves = max_size_xz * 4 / 1000 * octaves_per_km
    print(f'terrain perlin octaves: {octaves}')
    perlin = PerlinNoise(octaves, args.seed)
    heightmap = [[perlin([x/max_size_xz, z/max_size_xz]) for z in range(tile_size_z+1)] for x in range(tile_size_x+1)]  # -0.5 .. +0.5
    heightmap = [[point*2 for point in col] for col in heightmap]  # -1 .. +1
    heightmap = [[point*4 for point in col] for col in heightmap]  # -4 .. +4  # small node wall height
    heightmap = [[point*42 for point in col] for col in heightmap]
    heightmap = [[point/3 if -12 < point < 12 else point for point in col] for col in heightmap]
    heightmap = [[point/3 if -3 < point < 3 else point for point in col] for col in heightmap]
    heightmap = [[point*2 if point < -16 else point for point in col] for col in heightmap]
    heightmap = [[32 if point > 32 else point for point in col] for col in heightmap]
    heightmap = [[-40 if point < -40 else point for point in col] for col in heightmap]
    return heightmap


def gen_perlin_heightmap(tile_size_x: int, tile_size_z: int, args: Args) -> list[list[Point]]:
    shape = args.shape
    if shape == 'demo':
        heightmap_values = gen_perlin_heightmap_demo(tile_size_x, tile_size_z, args)
    else:
        assert shape == 'smooth'
        heightmap_values = gen_perlin_heightmap_smooth(tile_size_x, tile_size_z, args)
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
        random.shuffle(fixed_points)
        point: Point = fixed_points[0]
        # print(f'clearing point {(point.x, point.z)}')
        point.clear()

        generate_tile(tile, tiles, tile_size_x, tile_size_z)  # try again with fewer constraints
        tile.fail_count += 1
        return True  # restart to re-generate all deleted tiles


def pre_fix_border_sub(border: list[Point]):
    for point in sorted(border, key=lambda x: abs(x.height)):
        height = round(point.height / 4) * 4
        for pfn in [np for np in point.neighbor_points() if np.pre_fixed]:
            if height - pfn.height < -12:
                height = pfn.height - 12
            if height - pfn.height > 12:
                height = pfn.height + 12
        point.set_height(height)
        point.pre_fixed = True


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


def generate_tiles(tile_size_x: int, tile_size_z: int, heightmap: list[list[Point]], args: Args):
    tiles = [[Tile(x, z, heightmap) for z in range(tile_size_z)] for x in range(tile_size_x)]

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
        if tile.fail_count >= 23:
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

    # find a suitable target tile
    all_tiles.sort(key=lambda x: x.dist2center)
    target_tile = [t for t in all_tiles if t.node_mesh == 't_xxx_flr_04x04-v0' and t.node_turn == 0 and t.node_base_height == 0][0]
    print(f'target tile: ({target_tile.x} | {target_tile.z})')

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


def generate_plants(tile_size_x, tile_size_z, tiles: list[list[Tile]], args: Args) -> list[Plant]:
    max_size_xz = max(tile_size_x, tile_size_z)
    octaves_per_km = 16
    octaves = max_size_xz * 4 / 1000 * octaves_per_km
    print(f'plants perlin octaves: {octaves}')
    perlin = PerlinNoise(octaves, args.seed)

    floor_tiles = []
    for tcol in tiles:
        floor_tiles.extend([tile for tile in tcol if tile.node_mesh == 't_xxx_flr_04x04-v0'])
    plants: list[Plant] = list()
    plant_types = {
        'trunks': (0.1, -0.5, 3, ['tree_grs_pine_trunk_03']),
        'trees': (0.2, -0.125, 4, ['tree_glb_sway_05', 'tree_glb_sway_06', 'tree_grs_deciduous_sway_01', 'tree_grs_deciduous_sway_02', 'tree_grs_sapling_01']),
        'bushes': (0.4, -0.25, 2, ['bush_grs_04', 'bush_grs_button_01', 'bush_grs_rhod_01', 'bush_grs_rhod_03']),
        'flowers': (0.1, 0, 2, ['flowers_grs_06', 'flowers_grs_06', 'flowers_grs_08']),
        'grass': (0.3, 0, 0.5, ['foliage_grs_01', 'foliage_grs_01', 'grass_grs_06', 'grass_grs_07', 'groundcover_grs_02', 'groundcover_grs_03']),
    }
    for density, perlin_offset, perlin_spread, templates in plant_types.values():
        for _ in range(int(len(floor_tiles) * 4*4 * density)):  # density = num potential plants per m²
            tile = random.choice(floor_tiles)
            x = random.uniform(0, 4)
            z = random.uniform(0, 4)
            perlin_value = perlin([(tile.x*4 + x)/max_size_xz, (tile.z*4 + z)/max_size_xz])
            probability = perlin_value*perlin_spread+0.5+perlin_offset
            grows = random.uniform(0, 1) < probability
            if grows:
                orientation = random.uniform(0, math.tau)
                x -= 2
                z -= 2
                node_turn_angle = tile.turn_angle()
                x, z = MapgenTerrain.turn(x, z, -node_turn_angle)
                orientation -= node_turn_angle
                template = random.choice(templates)
                size = random.uniform(0.8, 1.2)
                plants.append(Plant(template, Position(x, 0, z, tile.node.guid), orientation, size))
    print(f'generate plants successful ({len(plants)} plants generated)')
    return plants


def generate_region_data(size_x: int, size_z: int, args: Args, region_name):
    assert size_x % 4 == 0
    assert size_z % 4 == 0
    tile_size_x = int(size_x / 4)
    tile_size_z = int(size_z / 4)

    heightmap = gen_perlin_heightmap(tile_size_x, tile_size_z, args)

    tiles, target_tile = generate_tiles(tile_size_x, tile_size_z, heightmap, args)

    verify(tiles, target_tile, heightmap)

    save_image_heightmap(heightmap, f'{args.map_name}-{region_name}')
    save_image_tiles(tiles, f'{args.map_name}-{region_name}')

    terrain = make_terrain(tiles, target_tile, tile_size_x, tile_size_z)

    plants = generate_plants(tile_size_x, tile_size_z, tiles, args)

    print('generate region data successful')
    return terrain, plants


def generate_region(_map, region_name, size_x, size_z, args: Args):
    print(f'generate region {region_name} {size_x}x{size_z} ({args})')

    # generate the region!
    terrain, plants = generate_region_data(size_x, size_z, args, region_name)

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
        print(f'deleting existing region {region_name}')
        _map.delete_region(region_name)
        _map.gas_dir.clear_cache()
    region = _map.create_region(region_name, None)
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
                placement=Placement(position=plant.position, orientation=MapgenTerrain.rad_to_quat(plant.orientation)),
                aspect=Aspect(scale_multiplier=plant.size)
            ) for plant in plants
        ])
    region.save()
    print(f'new region {region_name} saved')


def mapgen_heightmap(map_name, region_name, size_x, size_z, args: Args):
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

    # check map exists
    bits = Bits()
    _map = bits.maps[map_name]

    generate_region(_map, region_name, size_z, size_z, args)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen Heightmap')
    parser.add_argument('map')
    parser.add_argument('region')
    parser.add_argument('--size')
    parser.add_argument('--seed', nargs='?', type=int)
    parser.add_argument('--cull-above', nargs='?', type=float)
    parser.add_argument('--cull-below', nargs='?', type=float)
    parser.add_argument('--shape', nargs='?', choices=['smooth', 'demo'], default='smooth')
    parser.add_argument('--start-pos', nargs='?')
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


def main(argv):
    args = parse_args(argv)
    size_x, size_z = [int(x) for x in args.size.split('x')]
    mapgen_heightmap(args.map, args.region, size_x, size_z, Args(args))


if __name__ == '__main__':
    main(sys.argv[1:])
