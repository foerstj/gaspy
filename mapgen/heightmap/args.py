import argparse
from argparse import Namespace


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
        x_str = str(x).zfill(len(str(self.num_x)))
        z_str = str(z).zfill(len(str(self.num_z)))
        return f'{self.region_basename}-x{x_str}z{z_str}'

    def cur_region_name(self):
        return self.region_name(self.cur_x, self.cur_z)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy MapGen Heightmap')
    parser.add_argument('map', help='name of the map to generate region(s) in')
    parser.add_argument('region', help='(base) name of the region(s) to generate')
    parser.add_argument('--size', help='XxZ size of region (tile) in meters')
    parser.add_argument('--region-id', nargs='?', choices=['tile', 'next'], default='tile', help='how to decide region id')
    parser.add_argument('--seed', nargs='?', type=int, help='perlin seed')
    parser.add_argument('--cull-above', nargs='?', type=float, help='cull nodes from this height upwards')
    parser.add_argument('--cull-below', nargs='?', type=float, help='cull nodes from this height downwards')
    parser.add_argument('--shape', nargs='?', choices=['smooth', 'demo', 'flat'], default='smooth', help='shaping of the perlin heightmap')
    parser.add_argument('--base-heightmap', action='store_true', help='underlay a smooth curve under the main heightmap')
    parser.add_argument('--map-cutoff', action='store_true', help='cut off the terrain in a diamond shape')
    parser.add_argument('--start-pos', nargs='?', help='provide start group name to generate a start pos')
    parser.add_argument('--region-tiling', nargs='?', help='XxZ num of region tiles, followed by which tiles to generate right now')
    parser.add_argument('--game-objects', nargs='?', help='profile progression of plants & enemies')
    parser.add_argument('--print-world', action='store_true', help='produce a whole-world (all region tiles) overview of the heightmap')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


class Args:
    def __init__(self, args: Namespace = None):
        if args is None:
            args = Namespace()
        self.map_name: str = args.map
        self.region_name: str = args.region
        self.region_id: str = args.region_id
        self.seed: int = args.seed
        self.cull_above: float = args.cull_above
        self.cull_below: float = args.cull_below
        self.shape: str = args.shape
        self.base_heightmap: bool = args.base_heightmap
        self.start_pos: str = args.start_pos
        self.game_objects: str = args.game_objects
        self.map_cutoff: bool = args.map_cutoff

    def __str__(self):
        d = {
            'seed': self.seed,
            'cull_above': self.cull_above,
            'cull_below': self.cull_below,
            'shape': self.shape,
            'base_heightmap': self.base_heightmap,
            'start_pos': self.start_pos,
            'game_objects': self.game_objects,
            'map_cutoff': self.map_cutoff,
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
