import os

from gas.gas import Gas, Section, Attribute
from gas.gas_dir import GasDir
from gas.molecules import Hex

from .gas_dir_handler import GasDirHandler
from .region import Region
from .start_positions import StartPositions, StartGroup, StartPos, Camera


class Map(GasDirHandler):
    class Data:
        class Camera:
            def __init__(self):
                self.azimuth = None
                self.distance = None
                self.position = None

        class World:
            def __init__(self, screen_name: str, description: str, required_level: int):
                self.screen_name = screen_name
                self.description = description
                self.required_level = required_level

        def __init__(self, name=None, screen_name=None):
            self.name = name
            self.screen_name = screen_name
            self.description = None
            self.dev_only = None
            self.timeofday = None
            self.use_node_mesh_index = None
            self.use_player_journal = None
            self.camera = Map.Data.Camera()
            self.worlds = None  # dict[str, World]

        @classmethod
        def from_gas(cls, map_main_gas: Gas):
            map_section = map_main_gas.get_section('t:map,n:map')
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
            worlds_section = map_section.get_section('worlds')
            if worlds_section is not None:
                worlds = dict()
                for world_section in worlds_section.get_sections():
                    name = world_section.header
                    screen_name = world_section.get_attr_value('screen_name')
                    description = world_section.get_attr_value('description')
                    required_level = int(world_section.get_attr_value('required_level'))
                    worlds[name] = Map.Data.World(screen_name, description, required_level)
                data.worlds = worlds
            return data

        def to_gas(self) -> Gas:
            map_section = Section('t:map,n:map', [
                Attribute('name', self.name),
                Attribute('screen_name', self.screen_name),
                Attribute('description', self.description),
                Attribute('dev_only', self.dev_only),
                Attribute('timeofday', self.timeofday),
                Attribute('use_node_mesh_index', self.use_node_mesh_index),
                Attribute('use_player_journal', self.use_player_journal),
                Section('camera', [
                    Attribute('azimuth', self.camera.azimuth),
                    Attribute('distance', self.camera.distance),
                    Attribute('position', self.camera.position)
                ])
            ])
            if self.worlds is not None:
                world_sections: list[Section] = []
                for name, world in self.worlds.items():
                    world_sections.append(Section(name, [
                        Attribute('screen_name', world.screen_name),
                        Attribute('description', world.description),
                        Attribute('required_level', str(world.required_level))
                    ]))
                map_section.items.append(Section('worlds', world_sections))
            map_main_gas = Gas([map_section])
            return map_main_gas

    def __init__(self, gas_dir, bits, data=None, start_positions=None):
        super().__init__(gas_dir)
        self.bits = bits
        self.data = data
        self.start_positions: StartPositions = start_positions

    def get_data(self) -> Data:
        if self.data is None:
            self.load_data()
        return self.data

    def get_name(self):
        return self.gas_dir.dir_name

    def load_data(self):
        main_file = self.gas_dir.get_gas_file('main')
        assert main_file is not None
        self.data = Map.Data.from_gas(main_file.get_gas())

    def store_data(self):
        map_main_gas: Gas = self.data.to_gas()
        self.gas_dir.get_or_create_gas_file('main', False).gas = map_main_gas

    def load_start_positions(self):
        assert self.start_positions is None
        start_groups = dict()
        default = None
        start_positions_gas = self.gas_dir.get_subdir('info').get_gas_file('start_positions').get_gas()
        for section in start_positions_gas.get_section('start_positions').get_sections():
            assert section.has_t_n_header()
            t, name = section.get_t_n_header()
            assert t == 'start_group'
            positions = []
            for pos_section in section.get_sections('start_position'):
                camera_section = pos_section.get_section('camera')
                camera = Camera(camera_section.get_attr_value('azimuth'), camera_section.get_attr_value('distance'), camera_section.get_attr_value('orbit'), camera_section.get_attr_value('position'))
                pos = StartPos(pos_section.get_attr_value('id'), pos_section.get_attr_value('position'), camera)
                positions.append(pos)
            start_group = StartGroup(section.get_attr_value('description'), section.get_attr_value('dev_only'), section.get_attr_value('id'), section.get_attr_value('screen_name'), positions)
            start_groups[name] = start_group
            if section.get_attr_value('default'):
                assert default is None
                default = name
        assert default is not None
        start_positions = StartPositions(start_groups, default)
        self.start_positions = start_positions

    def store_start_positions(self):
        assert self.start_positions is not None
        info_dir = self.gas_dir.get_or_create_subdir('info')
        start_group_sections = []
        gas_file = info_dir.get_or_create_gas_file('start_positions')
        gas_file.gas = Gas([
            Section('start_positions', start_group_sections)
        ])
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

    def is_multi_world(self) -> bool:
        data = self.get_data()
        if data.worlds is None:
            return False
        if len(data.worlds) == 0:
            return False
        if len(data.worlds) == 1:
            assert list(data.worlds.values())[0].required_level == 0
            return False
        return True

    def get_regions(self) -> dict[str, Region]:
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        return {name: Region(gas_dir, self) for name, gas_dir in regions.items()}

    def get_region(self, name):
        region_dirs = self.gas_dir.get_subdir('regions').get_subdirs()
        assert name in region_dirs, f'Region {name} does not exist'
        return Region(region_dirs[name], self)

    def create_region(self, name, region_id) -> Region:
        regions = self.get_regions()
        regions_data = [r.get_data() for r in regions.values()]
        region_ids = [rd.id for rd in regions_data]
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

        mesh_ranges = [rd.mesh_range for rd in regions_data]
        mesh_range = region_id if region_id not in mesh_ranges else (max(mesh_ranges + [0]) + 1)
        scid_ranges = [rd.scid_range for rd in regions_data]
        scid_range = region_id if region_id not in scid_ranges else (max(scid_ranges + [0]) + 1)

        region.data = Region.Data()
        region.data.id = region_id
        region.data.mesh_range = mesh_range
        region.data.scid_range = scid_range

        return region

    def delete_region(self, name):
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        assert name in regions
        region_dir: GasDir = regions[name]
        region_dir.delete()

    def get_all_node_ids(self) -> list[Hex]:
        all_node_ids = list()
        for region in self.get_regions().values():
            all_node_ids.extend(region.get_node_ids())
        return all_node_ids

    def print(self, print_map=None, print_regions='stitches'):
        name = self.get_data().name
        screen_name = self.get_data().screen_name
        name_str = name + ' ' + screen_name if name is not None else screen_name
        description = str(self.get_data().description)
        regions = self.get_regions()
        print('Map: ' + name_str + ' (' + str(len(regions)) + ' regions) - ' + description)

        if print_map == 'npcs':
            self.print_npcs()

        if print_regions:
            for region in regions.values():
                region.print('  ', print_regions)

    def print_npcs(self):
        npcs = []
        for region in self.get_regions().values():
            npcs.extend(region.get_npcs())
        npcs = [npc for npc in npcs if npc.compute_value('common', 'is_single_player') is not False]
        npc_names = [npc.compute_value('common', 'screen_name') for npc in npcs]
        npc_names = [name.strip('"') if name is not None else 'None' for name in npc_names]
        npc_name_counts = dict()
        for name in npc_names:
            if name in npc_name_counts:
                npc_name_counts[name] += 1
            else:
                npc_name_counts[name] = 1
        for npc_name in sorted(npc_name_counts):
            print(npc_name + (f' ({npc_name_counts[npc_name]})' if npc_name_counts[npc_name] != 1 else ''))
