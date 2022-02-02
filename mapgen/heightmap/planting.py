import math
import random
from itertools import accumulate

from gas.gas import Position
from mapgen.flat.mapgen_terrain import MapgenTerrain
from mapgen.heightmap.args import Args, RegionTiling
from mapgen.heightmap.perlin import make_perlin
from mapgen.heightmap.progression import Progression, ProgressionStep, ProfileVariants, SingleProfile
from mapgen.heightmap.terrain import NodeTile
from plant_gen import PlantableArea, Plant, load_mesh_info


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
