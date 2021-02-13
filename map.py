import os

from gas_dir_handler import GasDirHandler


class Region(GasDirHandler):
    def get_actors(self):
        objects_dir = self.gas_dir.get_subdir('objects')
        if objects_dir is None:
            return []
        if 'regular' in objects_dir.get_subdirs():
            objects_dir = objects_dir.get_subdir('regular')
        actor_file = objects_dir.get_gas_file('actor')
        if actor_file is None:
            return []
        return actor_file.get_gas().items

    def print(self, indent=''):
        print(indent + os.path.basename(self.gas_dir.path) + ': ' + str(len(self.get_actors())) + ' actors')


class Map(GasDirHandler):
    def get_regions(self):
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        return {name: Region(gas_dir) for name, gas_dir in regions.items()}

    def print(self, print_regions=True):
        main_file = self.gas_dir.get_gas_file('main')
        assert main_file is not None
        main = main_file.get_gas()
        map_main = main.get_section('t:map,n:map')
        name = map_main.get_attr('name')
        screen_name = map_main.get_attr('screen_name').value
        name_str = name.value + ' ' + screen_name if name is not None else screen_name
        description = map_main.get_attr('description').value
        regions = self.get_regions()
        print('Map: ' + name_str + ' (' + str(len(regions)) + ' regions) - ' + description)
        if print_regions:
            for region in regions.values():
                region.print('  ')
