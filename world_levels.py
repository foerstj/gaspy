import os
import shutil
import sys

from bits import Bits


def rem_world_levels(map_name):
    bits = Bits()
    _map = bits.maps[map_name]
    for region_name, region in _map.get_regions().items():
        print(region_name)

        index_dir = region.gas_dir.get_subdir('index')
        os.rename(os.path.join(index_dir.path, 'regular', 'streamer_node_content_index.gas'), os.path.join(index_dir.path, 'streamer_node_content_index.gas'))
        shutil.rmtree(os.path.join(index_dir.path, 'regular'))
        shutil.rmtree(os.path.join(index_dir.path, 'veteran'))
        shutil.rmtree(os.path.join(index_dir.path, 'elite'))

        objects_dir = region.gas_dir.get_subdir('objects')
        for file_name in os.listdir(os.path.join(objects_dir.path, 'regular')):
            os.rename(os.path.join(objects_dir.path, 'regular', file_name), os.path.join(objects_dir.path, file_name))
        shutil.rmtree(os.path.join(objects_dir.path, 'regular'))
        shutil.rmtree(os.path.join(objects_dir.path, 'veteran'))
        shutil.rmtree(os.path.join(objects_dir.path, 'elite'))


def main(argv):
    assert len(argv) == 2
    assert argv[0] == 'rem'
    map_name = argv[1]
    rem_world_levels(map_name)


if __name__ == '__main__':
    main(sys.argv[1:])
