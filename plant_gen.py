# This script generates plants on *existing* regions
import sys

from bits import Bits
from nodes_gas import NodesGas


def plant_gen(map_name, region_name):
    bits = Bits()
    _map = bits.maps[map_name]
    region = _map.get_region(region_name)
    region.print(info=None)
    nodes_gas_file = region.gas_dir.get_subdir('terrain_nodes').get_gas_file('nodes')
    nodes_gas = NodesGas.load(nodes_gas_file)
    nodes_gas.print()


def main(argv):
    map_name = argv[0]
    region_name = argv[1]
    plant_gen(map_name, region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
