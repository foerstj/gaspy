from __future__ import annotations

import math
import random
import sys
from itertools import accumulate

from bits.bits import Bits
from bits.game_object_data import GameObjectData, Placement, Common, TriggerInstance, Aspect
from gas.gas import Hex, Position, Quaternion
from mapgen.flat.mapgen_terrain import MapgenTerrain
from mapgen.heightmap.args import parse_args, parse_region_tiling, Args, RegionTilingArg, RegionTiling
from mapgen.heightmap.perlin import make_perlin
from mapgen.heightmap.progression import Progression, ProgressionStep, ProfileVariants, SingleProfile
from mapgen.heightmap.save_image import save_image
from mapgen.heightmap.terrain import NodeTile, gen_perlin_heightmap, save_image_heightmap, generate_tiles, verify, make_terrain
from plant_gen import Plant, load_mesh_info, PlantableArea
from bits.region import DirectionalLight, Region
from bits.start_positions import StartPos, StartGroup, Camera
from bits.stitch_helper_gas import StitchHelperGas, StitchEditor


def get_progression_demo(seed: int, max_size_xz: int) -> Progression:
    perlin_prog_tx = make_perlin(seed, max_size_xz, 5)  # curving progression tx lines
    perlin_variants = make_perlin(seed+1, max_size_xz, 3)  # for main a/b variants
    perlin_subvar_a = make_perlin(seed+1, max_size_xz, 5)  # two overlapping distributions for four sub-variants
    perlin_subvar_b = make_perlin(seed+2, max_size_xz, 5)
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
    return progression


def get_progression(args: Args, max_size_xz: int) -> Progression:
    if args.game_objects == 'demo':
        return get_progression_demo(args.seed, max_size_xz)
    else:
        assert False, args.game_objects


class PlantableTileArea:
    def __init__(self, tile: NodeTile, mesh_info: dict[str, PlantableArea]):
        self.tile = tile
        self.plantable_area = mesh_info.get(tile.node_mesh)
        self.tile_x_min = 0.0
        self.tile_x_max = 0.0
        self.tile_z_min = 0.0
        self.tile_z_max = 0.0
        if self.plantable_area is not None:
            node_turn_angle = self.tile.turn_angle()
            x1, z1 = MapgenTerrain.turn(self.plantable_area.x_min, self.plantable_area.z_min, node_turn_angle)
            x2, z2 = MapgenTerrain.turn(self.plantable_area.x_max, self.plantable_area.z_max, node_turn_angle)
            self.tile_x_min = min(x1, x2) + 2
            self.tile_x_max = max(x1, x2) + 2
            self.tile_z_min = min(z1, z2) + 2
            self.tile_z_max = max(z1, z2) + 2

    def node_coords(self, tile_x, tile_z):
        x = tile_x - 2
        z = tile_z - 2
        node_turn_angle = self.tile.turn_angle()
        return MapgenTerrain.turn(x, z, -node_turn_angle)

    def node_orientation(self, tile_orientation):
        node_turn_angle = self.tile.turn_angle()
        return tile_orientation - node_turn_angle


def generate_game_objects(tile_size_x, tile_size_z, tiles: list[list[NodeTile]], args: Args, rt: RegionTiling) -> list[Plant]:
    max_size_xz = max(tile_size_x*rt.num_x, tile_size_z*rt.num_z)
    perlin_plants_main = make_perlin(args.seed, max_size_xz, 6)  # main plant growth
    perlin_plants_underlay = make_perlin(args.seed, max_size_xz, 4)  # wider plant growth underlay

    plantable_tiles = []
    for tcol in tiles:
        plantable_tiles.extend([tile for tile in tcol if tile.node_mesh != 'EMPTY' and not tile.is_culled])
    mesh_info = load_mesh_info()
    plantable_tile_areas = [PlantableTileArea(tile, mesh_info) for tile in plantable_tiles]
    plantable_tile_areas = [pta for pta in plantable_tile_areas if pta.plantable_area is not None]
    game_objects: list[Plant] = list()
    progression = get_progression(args, max_size_xz)
    plantable_area_size = sum([pta.plantable_area.size() for pta in plantable_tile_areas])
    plantable_tile_area_cum_sizes = list(accumulate([pta.plantable_area.size() for pta in plantable_tile_areas]))
    for pe in ['plants', 'enemies']:
        is_plants = pe == 'plants'
        generated_pes = list()
        num_seeds = int(plantable_area_size * progression.max_sum_seed_factor(is_plants))
        print(f'generate {pe} - {num_seeds} seeds')
        for i_seed in range(num_seeds):
            distribution_seed_index = i_seed / plantable_area_size

            area = random.choices(plantable_tile_areas, cum_weights=plantable_tile_area_cum_sizes, k=1)[0]
            if is_plants and area.tile.crosses_middle() and i_seed % 2 == 0:
                continue  # place less plants across pathable middle
            if not is_plants:
                if area.tile.min_main_height() < -4 or area.tile.max_main_height() > 4:
                    continue  # place enemies only on reachable area
            x = random.uniform(area.tile_x_min, area.tile_x_max)
            z = random.uniform(area.tile_z_min, area.tile_z_max)
            map_norm_x = (rt.cur_x*tile_size_x + area.tile.x + x/4) / max_size_xz  # x on whole map, normalized (0-1)
            map_norm_z = (rt.cur_z*tile_size_z + area.tile.z + z/4) / max_size_xz  # z on whole map, normalized (0-1)

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
            if (template.startswith('tree_') or template.startswith('bush_')) and area.tile.crosses_middle():
                continue  # place no large plants on pathable middle
            if '_trunk_' in template and area.tile.min_height() < -20:
                continue  # don't place trunks too far down or you'll see the top
            perlin_value = perlin_plants_main([map_norm_x, map_norm_z]) + 0.5*perlin_plants_underlay([map_norm_x, map_norm_z])
            probability = perlin_value*distribution.perlin_spread + 0.5+distribution.perlin_offset
            grows = random.uniform(0, 1) < probability
            if grows:
                orientation = random.uniform(0, math.tau)
                node_x, node_z = area.node_coords(x, z)
                node_orientation = area.node_orientation(orientation)
                size = random.uniform(distribution.size_from, distribution.size_to) + distribution.size_perlin*perlin_value
                generated_pes.append(Plant(template, Position(node_x, area.plantable_area.y, node_z, area.tile.node.guid), node_orientation, size))
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

    plants = generate_game_objects(tile_size_x, tile_size_z, tiles, args, rt) if args.game_objects != 'none' else []

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


def save_image_whole_world_tile_estimation(size_x, size_z, args: Args, rt_base: RegionTilingArg):
    sampling = 1
    map_size_x = int(size_x/4*rt_base.num_x / sampling)
    map_size_z = int(size_z/4*rt_base.num_z / sampling)
    print(f'generating whole world heightmap ({map_size_x}x{map_size_z} tiles)')
    whole_world_heightmap = gen_perlin_heightmap(map_size_x, map_size_z, args, RegionTiling(1, 1, 0, 0, args.map_name), sampling)
    print(f'saving image... ({len(whole_world_heightmap)}x{len(whole_world_heightmap[0])} px)')
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
    save_image(pic, f'{args.map_name} overview {args.seed}')
    print('done')


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
        save_image_whole_world_tile_estimation(size_x, size_z, args, rt_base)

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
