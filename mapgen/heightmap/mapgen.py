from __future__ import annotations

import random
import sys

from bits.bits import Bits
from bits.decals import DecalsGas
from bits.game_object_data import GameObjectData, Placement, Common, TriggerInstance, Aspect
from gas.gas import Hex, Position, Quaternion
from mapgen.heightmap.args import parse_args, parse_region_tiling, Args, RegionTilingArg, RegionTiling
from mapgen.heightmap.planting import generate_game_objects, get_progression
from mapgen.heightmap.save_image import save_image
from mapgen.heightmap.terrain import NodeTile, gen_perlin_heightmap, save_image_heightmap, generate_tiles, verify, make_terrain, all_tiles_culled, apply_progression_node_sets
from bits.region import DirectionalLight, Region
from bits.start_positions import StartPos, StartGroup, Camera
from bits.stitch_helper_gas import StitchHelperGas, StitchEditor


def generate_region_data(size_x: int, size_z: int, args: Args, region_name, rt: RegionTiling, map_node_ids):
    assert size_x % 4 == 0
    assert size_z % 4 == 0
    tile_size_x = int(size_x / 4)
    tile_size_z = int(size_z / 4)

    heightmap = gen_perlin_heightmap(tile_size_x, tile_size_z, args, rt)
    save_image_heightmap(heightmap, f'{args.map_name}-{region_name}')

    tiles, target_tile = generate_tiles(tile_size_x, tile_size_z, heightmap, args, rt)

    verify(tiles, target_tile, heightmap)
    if all_tiles_culled(tiles):
        return None

    terrain = make_terrain(tiles, target_tile, tile_size_x, tile_size_z, map_node_ids)

    if args.game_objects is not None:
        max_size_xz = max(tile_size_x * rt.num_x, tile_size_z * rt.num_z)
        progression = get_progression(args, max_size_xz)
        plants = generate_game_objects(tile_size_x, tile_size_z, tiles, progression, args, rt)
        decals = apply_progression_node_sets(tiles, tile_size_x, tile_size_z, progression, rt)
    else:
        plants = []
        decals = []

    stitches = make_region_tile_stitches(tiles, tile_size_x, tile_size_z, rt)

    print('generate region data successful')
    return terrain, plants, stitches, decals


def get_stitch_id(rx: int, rz: int, hv: bool, xz: int):
    assert 0 <= rx < 100
    assert 0 <= rz < 100
    assert 0 <= xz < 0x1000
    rx = str(rx).zfill(2)
    rz = str(rz).zfill(2)
    hv = '0' if hv else '1'
    stitch_range = f'0x{rx}{rz}{hv}000'
    return Hex.parse(stitch_range) + xz


def make_region_tile_stitches(tiles: list[list[NodeTile]], tile_size_x, tile_size_z, rt: RegionTiling):
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
    region_data = generate_region_data(size_x, size_z, args, region_name, rt, _map.get_all_node_ids())
    if region_data is None:
        print('all tiles culled - not saving region')
        return
    terrain, plants, stitches, decals = region_data

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
    region.decals = DecalsGas(decals) if len(decals) > 0 else None
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
            GameObjectData('trigger_change_mood_box', placement=Placement(position=pos), common=Common(instance_triggers=[
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


def save_whole_world_image(pic, name, size_x, size_z):
    for x in range(len(pic)):
        for z in range(len(pic[x])):
            px = pic[x][z]
            if x % (size_x/4) == 0:
                px -= 0.25
            elif z % (size_z/4) == 0:
                px -= 0.25
            pic[x][z] = px
    save_image(pic, name)


def create_image_whole_world_tile_estimation(size_x, size_z, args: Args, rt_base: RegionTilingArg):
    map_size_x = int(size_x/4*rt_base.num_x)
    map_size_z = int(size_z/4*rt_base.num_z)
    print(f'generating whole world heightmap ({map_size_x}x{map_size_z} tiles)')
    whole_world_heightmap = gen_perlin_heightmap(map_size_x, map_size_z, args, RegionTiling(1, 1, 0, 0, args.map_name))
    pic = [[pt.height for pt in col] for col in whole_world_heightmap]
    for x in range(len(pic)):
        for z in range(len(pic[x])):
            px = pic[x][z]
            if args.cull_below and px <= args.cull_below:
                px = 2
            elif args.cull_above and px >= args.cull_above:
                px = 1.75
            elif -6 <= px <= 6:
                px = 0
            else:
                px = 1
            pic[x][z] = px
    return pic


def save_image_whole_world_tile_estimation(size_x, size_z, args: Args, rt_base: RegionTilingArg):
    pic = create_image_whole_world_tile_estimation(size_x, size_z, args, rt_base)
    save_whole_world_image(pic, f'{args.map_name} terrain {args.seed}', size_x, size_z)
    print('done')


def create_image_whole_world_progression(size_x, size_z, args: Args, rt_base: RegionTilingArg, tx='sharp'):
    map_size_x = int(size_x/4*rt_base.num_x)
    map_size_z = int(size_z/4*rt_base.num_z)
    max_size_xz = max(map_size_x, map_size_z)
    progression = get_progression(args, max_size_xz)
    print(f'generating whole world progression ({map_size_x}x{map_size_z} tiles)')
    whole_world_progression = [[progression.choose_progression_step(x/max_size_xz, z/max_size_xz, tx) for z in range(map_size_z+1)] for x in range(map_size_x+1)]
    pic = [[pt.count if pt else 0 for pt in col] for col in whole_world_progression]
    return pic


def save_image_whole_world_progression(size_x, size_z, args: Args, rt_base: RegionTilingArg, tx='sharp'):
    pic = create_image_whole_world_progression(size_x, size_z, args, rt_base, tx)
    save_whole_world_image(pic, f'{args.map_name} progression {args.seed}', size_x, size_z)
    print('done')


def save_image_whole_world_variants(size_x, size_z, args: Args, rt_base: RegionTilingArg, is_plants=True):
    map_size_x = int(size_x/4*rt_base.num_x)
    map_size_z = int(size_z/4*rt_base.num_z)
    max_size_xz = max(map_size_x, map_size_z)
    progression = get_progression(args, max_size_xz)
    print(f'generating whole world variants ({map_size_x}x{map_size_z} tiles)')
    variants = [[progression.choose_progression_step(x / max_size_xz, z / max_size_xz, 'blur' if is_plants else 'gap') for z in range(map_size_z + 1)] for x in range(map_size_x + 1)]
    variants = [[p.get_profile(is_plants) if p is not None else None for p in col] for col in variants]
    variants = [[variants[x][z].choose_profile(x/max_size_xz, z/max_size_xz) if variants[x][z] is not None else None for z in range(map_size_z+1)] for x in range(map_size_x+1)]
    pic = [[pt.count % 5.5 + 1 if pt else 0 for pt in col] for col in variants]
    pe = 'plants' if is_plants else 'enemies'
    save_whole_world_image(pic, f'{args.map_name} variants {pe} {args.seed}', size_x, size_z)
    print('done')


def save_image_whole_world_overview(size_x, size_z, args: Args, rt_base: RegionTilingArg):
    tile_est_pic = create_image_whole_world_tile_estimation(size_x, size_z, args, rt_base)
    progression_pic = create_image_whole_world_progression(size_x, size_z, args, rt_base, 'gap')
    for x in range(len(tile_est_pic)):
        for z in range(len(tile_est_pic[x])):
            if progression_pic[x][z] == 0:  # gap
                tile_est_pic[x][z] -= 0.5
    save_whole_world_image(tile_est_pic, f'{args.map_name} overview {args.seed}', size_x, size_z)
    print('done')


def print_world_plots(size_x, size_z, args: Args, rt_base: RegionTilingArg):
    save_image_whole_world_overview(size_x, size_z, args, rt_base)
    save_image_whole_world_tile_estimation(size_x, size_z, args, rt_base)
    if args.game_objects:
        save_image_whole_world_progression(size_x, size_z, args, rt_base)
        save_image_whole_world_variants(size_x, size_z, args, rt_base, True)
        save_image_whole_world_variants(size_x, size_z, args, rt_base, False)


def mapgen(map_name, region_name, size_x, size_z, args: Args, rt_base: RegionTilingArg, print_world=False):
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
        print_world_plots(size_x, size_z, args, rt_base)

    # check map exists
    bits = Bits()
    assert map_name in bits.maps, f'Map {map_name} does not exist'
    _map = bits.maps[map_name]

    start_pos_arg = args.start_pos
    for rtx in range(rt_base.gen_x_from, rt_base.gen_x_to):
        for rtz in range(rt_base.gen_z_from, rt_base.gen_z_to):
            args.start_pos = None
            if rtx == int(rt_base.num_x/2) and rtz == int(rt_base.num_z/2):
                args.start_pos = start_pos_arg  # put start-pos in middle region
            rt = RegionTiling(rt_base.num_x, rt_base.num_z, rtx, rtz, region_name)
            generate_region(_map, rt.cur_region_name(), size_x, size_z, args, rt)


def main(argv):
    args = parse_args(argv)
    size_x, size_z = [int(x) for x in args.size.split('x')]
    rt = parse_region_tiling(args.region_tiling)
    mapgen(args.map, args.region, size_x, size_z, Args(args), rt, args.print_world)


if __name__ == '__main__':
    main(sys.argv[1:])
