import argparse

import sys

from bits.bits import Bits
from bits.maps.map import Map
from bits.maps.region import Region
from bits.maps.terrain import TerrainNode
from bits.snos import SNOs
from gas.gas_parser import GasParser


def combine_usages(combo_type: str, usages: dict, sub_usages: dict):
    assert combo_type in ['or', 'sum']
    for mesh_name in usages:
        if combo_type == 'or':
            usages[mesh_name] |= sub_usages[mesh_name]
        elif combo_type == 'sum':
            usages[mesh_name] += sub_usages[mesh_name]


class UsageCollector:
    def __init__(self, mesh_names: list[str]):
        self.mesh_names = mesh_names

    def default_value(self):
        return None

    def init_usages(self) -> dict:
        return {mesh_name: self.default_value() for mesh_name in self.mesh_names}

    def get_region_usages(self, region: Region):
        region_usages = self.init_usages()

        for mesh_name in region.get_node_meshes():
            assert mesh_name in region_usages, mesh_name
            region_usages[mesh_name] = True

        return region_usages

    def combine_region_usages(self, map_usages, region_usages):
        pass

    def collect_region_usages(self, region: Region, map_usages: dict):
        region_usages = self.get_region_usages(region)
        self.combine_region_usages(map_usages, region_usages)

    def get_map_usages(self, m: Map) -> dict:
        map_usages = self.init_usages()

        for region in m.get_regions().values():
            num_nodes = len(region.get_terrain().nodes)
            num_meshes = len(region.get_node_meshes())
            print(f'  {region.get_name()}: {num_nodes} nodes, {num_meshes} meshes')

            self.collect_region_usages(region, map_usages)

        return map_usages

    def collect_map_usages(self, m: Map, usages: dict):
        map_usages = self.get_map_usages(m)
        self.combine_map_usages(usages, map_usages)

    def combine_map_usages(self, usages, map_usages):
        pass

    def get_usages(self, maps: list[Map]) -> dict:
        usages = self.init_usages()

        print(f'Maps: {len(maps)}')
        for m in maps:
            m.print()

            self.collect_map_usages(m, usages)

        return usages


class NoneUsageCollector(UsageCollector):
    pass


class UsedUsageCollector(UsageCollector):
    def default_value(self):
        return False

    def combine_region_usages(self, map_usages, region_usages):
        combine_usages('or', map_usages, region_usages)

    def combine_map_usages(self, usages, map_usages):
        combine_usages('or', usages, map_usages)


class CountingUsageCollector(UsageCollector):
    def default_value(self):
        return 0


class CountMapsUsageCollector(CountingUsageCollector):
    def combine_region_usages(self, map_usages, region_usages):
        combine_usages('or', map_usages, region_usages)

    def combine_map_usages(self, usages, map_usages):
        combine_usages('sum', usages, map_usages)


class CountRegionsUsageCollector(CountingUsageCollector):
    def combine_region_usages(self, map_usages, region_usages):
        combine_usages('sum', map_usages, region_usages)

    def combine_map_usages(self, usages, map_usages):
        combine_usages('sum', usages, map_usages)


class CountNodesUsageCollector(CountRegionsUsageCollector):
    def get_region_usages(self, region: Region):
        region_usages = self.init_usages()

        for node in region.get_terrain().nodes:
            assert node.mesh_name.lower() in region_usages, node.mesh_name
            region_usages[node.mesh_name.lower()] += 1

        return region_usages


class NodeFlagUsage:
    def __init__(self):
        self.u = {True: 0, False: 0}

    def __str__(self):
        if self.u[True] == 0 and self.u[False] == 0:
            return 'unused'
        elif self.u[True] > 0 and self.u[False] > 0:
            return 'ambiguous'
        elif self.u[True] == 0 and self.u[False] > 0:
            return 'false'
        elif self.u[True] > 0 and self.u[False] == 0:
            return 'true'

    @classmethod
    def combine(cls, usages: dict[str, 'NodeFlagUsage'], sub_usages: dict[str, 'NodeFlagUsage']):
        for mesh_name in usages:
            usages[mesh_name].u[True] += sub_usages[mesh_name].u[True]
            usages[mesh_name].u[False] += sub_usages[mesh_name].u[False]


class NodeFlagUsageCollector(UsageCollector):
    def default_value(self):
        return NodeFlagUsage()

    def get_node_flag(self, node: TerrainNode):
        return False

    def get_region_usages(self, region: Region):
        region_usages = self.init_usages()

        for node in region.get_terrain().nodes:
            mesh_name = node.mesh_name.lower()
            node_flag = self.get_node_flag(node)
            assert mesh_name in region_usages, mesh_name
            region_usages[mesh_name].u[node_flag] += 1

        return region_usages

    def combine_region_usages(self, map_usages, region_usages):
        NodeFlagUsage.combine(map_usages, region_usages)

    def combine_map_usages(self, usages, map_usages):
        NodeFlagUsage.combine(usages, map_usages)


class BoundsCameraUsageCollector(NodeFlagUsageCollector):
    def get_node_flag(self, node: TerrainNode):
        return node.bounds_camera


class CameraFadeUsageCollector(NodeFlagUsageCollector):
    def get_node_flag(self, node: TerrainNode):
        return node.camera_fade


def get_usage_collector(usage_type: str, mesh_names: list[str]) -> UsageCollector:
    assert usage_type in ['none', 'used', 'count-maps', 'count-regions', 'count-nodes', 'bounds-camera', 'camera-fade']
    if usage_type == 'none':
        return NoneUsageCollector(mesh_names)
    elif usage_type == 'used':
        return UsedUsageCollector(mesh_names)
    elif usage_type == 'count-maps':
        return CountMapsUsageCollector(mesh_names)
    elif usage_type == 'count-regions':
        return CountRegionsUsageCollector(mesh_names)
    elif usage_type == 'count-nodes':
        return CountNodesUsageCollector(mesh_names)
    elif usage_type == 'bounds-camera':
        return BoundsCameraUsageCollector(mesh_names)
    elif usage_type == 'camera-fade':
        return CameraFadeUsageCollector(mesh_names)


def sno_usage(usage_type: str, map_names: list[str] = None, count_usage_values=False, bits_path=None, node_bits_path=None):
    if map_names is None:
        map_names = list()

    GasParser.get_instance().print_warnings = False
    bits = Bits(bits_path)
    node_bits = bits if node_bits_path is None else Bits(node_bits_path)

    snos = node_bits.snos
    print(f'SNOs: {len(snos.snos)}')
    mesh_names = [SNOs.get_name_for_path(sno_path) for sno_path in snos.snos]

    usage_collector = get_usage_collector(usage_type, mesh_names)

    maps = bits.maps
    maps = [m for n, m in maps.items() if len(map_names) == 0 or n in map_names]

    usages = usage_collector.get_usages(maps)

    print('Usages:')
    for node_mesh_name, usage in usages.items():
        print(f'  {node_mesh_name}: {usage}')
    if count_usage_values:
        usage_values = [str(v) for v in usages.values()]
        usage_value_counts = {v: 0 for v in usage_values}
        for usage_value in usage_values:
            usage_value_counts[usage_value] += 1
        print('Usage value summary:')
        for usage_value, count in usage_value_counts.items():
            print(f'  {usage_value}: {count}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printouts sno_usage')
    parser.add_argument('--usage', choices=['none', 'used', 'count-maps', 'count-regions', 'count-nodes', 'bounds-camera', 'camera-fade'], default='used')
    parser.add_argument('--maps', nargs='*')
    parser.add_argument('--count-usage-values', action='store_true')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--node-bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    sno_usage(args.usage, args.maps, args.count_usage_values, args.bits, args.node_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
