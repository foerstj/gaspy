from gas_dir_handler import GasDirHandler


class Map(GasDirHandler):
    def print(self):
        main_file = self.gas_dir.get_gas_file('main')
        assert main_file is not None
        main = main_file.get_gas()
        map_main = main.get_section('t:map,n:map')
        name = map_main.get_attr('name')
        screen_name = map_main.get_attr('screen_name').value
        name_str = name.value + ' ' + screen_name if name is not None else screen_name
        description = map_main.get_attr('description').value
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        assert regions is not None
        print('Map: ' + name_str + ' (' + str(len(regions)) + ' regions) - ' + description)
