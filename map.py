import os

from gas import Gas, Section, Attribute
from gas_dir import GasDir
from gas_dir_handler import GasDirHandler
from region import Region
from start_positions import StartPositions


class Map(GasDirHandler):
    class Data:
        class Camera:
            def __init__(self):
                self.azimuth = None
                self.distance = None
                self.position = None

        def __init__(self, name=None, screen_name=None):
            self.name = name
            self.screen_name = screen_name
            self.description = None
            self.dev_only = None
            self.timeofday = None
            self.use_node_mesh_index = None
            self.use_player_journal = None
            self.camera = Map.Data.Camera()

    def __init__(self, gas_dir, bits, data=None, start_positions=None):
        super().__init__(gas_dir)
        self.bits = bits
        self.data = data
        self.start_positions: StartPositions = start_positions

    def get_data(self) -> Data:
        if self.data is None:
            self.load_data()
        return self.data

    def load_data(self):
        main_file = self.gas_dir.get_gas_file('main')
        assert main_file is not None
        main = main_file.get_gas()
        map_section = main.get_section('t:map,n:map')
        data = Map.Data()
        data.name = map_section.get_attr_value('name')
        data.screen_name = map_section.get_attr_value('screen_name')
        data.description = map_section.get_attr_value('description')
        data.dev_only = map_section.get_attr_value('dev_only')
        data.timeofday = map_section.get_attr_value('timeofday')
        data.use_node_mesh_index = map_section.get_attr_value('use_node_mesh_index')
        data.use_player_journal = map_section.get_attr_value('use_player_journal')
        camera_section = map_section.get_section('camera')
        data.camera.azimuth = camera_section.get_attr_value('azimuth')
        data.camera.distance = camera_section.get_attr_value('distance')
        data.camera.position = camera_section.get_attr_value('position')
        self.data = data

    def store_data(self):
        main = self.gas_dir.get_or_create_gas_file('main', False).get_gas()
        map_section = main.get_or_create_section('t:map,n:map')
        map_section.set_attr_value('name', self.data.name)
        map_section.set_attr_value('screen_name', self.data.screen_name)
        map_section.set_attr_value('description', self.data.description)
        map_section.set_attr_value('dev_only', self.data.dev_only)
        map_section.set_attr_value('timeofday', self.data.timeofday)
        map_section.set_attr_value('use_node_mesh_index', self.data.use_node_mesh_index)
        map_section.set_attr_value('use_player_journal', self.data.use_player_journal)
        camera_section = map_section.get_or_create_section('camera')
        camera_section.set_attr_value('azimuth', self.data.camera.azimuth)
        camera_section.set_attr_value('distance', self.data.camera.distance)
        camera_section.set_attr_value('position', self.data.camera.position)

    def store_start_positions(self):
        info_dir = self.gas_dir.get_or_create_subdir('info')
        start_group_sections = []
        info_dir.create_gas_file('start_positions', Gas([
            Section('start_positions', start_group_sections)
        ]))
        for sg_name, sg in self.start_positions.start_groups.items():
            sp_sections: list = [
                Section('start_position', [
                    Attribute('id', sp.id),
                    Attribute('position', str(sp.position)),
                    Section('camera', [
                        Attribute('azimuth', float(sp.camera.azimuth)),
                        Attribute('distance', float(sp.camera.distance)),
                        Attribute('orbit', float(sp.camera.orbit)),
                        Attribute('position', str(sp.camera.position))
                    ])
                ]) for sp in sg.start_positions
            ]
            start_group_sections.append(Section('t:start_group,n:' + sg_name, [
                Attribute('default', self.start_positions.default == sg_name),
                Attribute('description', sg.description),
                Attribute('dev_only', sg.dev_only),
                Attribute('id', sg.id),
                Attribute('screen_name', sg.screen_name)
            ] + sp_sections))

    def save(self):
        if self.data is not None:
            self.store_data()
        if self.start_positions is not None:
            self.store_start_positions()
        self.gas_dir.get_or_create_subdir('regions', False)
        self.gas_dir.save()

    def delete(self):
        self.gas_dir.delete()

    def get_regions(self) -> dict[str, Region]:
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        return {name: Region(gas_dir, self) for name, gas_dir in regions.items()}

    def get_region(self, name):
        region_dirs = self.gas_dir.get_subdir('regions').get_subdirs()
        assert name in region_dirs
        return Region(region_dirs[name], self)

    def create_region(self, name, region_id):
        regions = self.get_regions()
        region_ids = {r.get_data().id for r in regions.values()}
        if region_id is not None:
            assert region_id not in region_ids
        else:
            max_region_id = max(region_ids) if region_ids else 0
            region_id = max_region_id + 1

        region_dirs = self.gas_dir.get_subdir('regions').get_subdirs()
        assert name not in region_dirs
        region_dir = GasDir(os.path.join(self.gas_dir.path, 'regions', name))
        region = Region(region_dir, self)
        region_dirs[name] = region_dir

        region.data = Region.Data()
        region.data.id = region_id
        region.data.mesh_range = region_id
        region.data.scid_range = region_id

        return region

    def delete_region(self, name):
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        assert name in regions
        region: GasDir = regions[name]
        region.delete()

    def get_all_node_ids(self):
        all_node_ids = list()
        for region in self.get_regions().values():
            all_node_ids.extend(region.get_node_ids())
        return all_node_ids

    def print(self, print_regions='stitches'):
        name = self.get_data().name
        screen_name = self.get_data().screen_name
        name_str = name + ' ' + screen_name if name is not None else screen_name
        description = str(self.get_data().description)
        regions = self.get_regions()
        print('Map: ' + name_str + ' (' + str(len(regions)) + ' regions) - ' + description)
        if print_regions:
            for region in regions.values():
                region.print('  ', print_regions)
