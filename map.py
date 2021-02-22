import os

from gas import Hex
from gas_dir import GasDir
from gas_dir_handler import GasDirHandler


class GameObject:
    def __init__(self, section, bits):
        self._bits = bits
        self.section = section
        [t, n] = section.header.split(',')
        assert t.startswith('t:')
        assert n.startswith('n:')
        self.template_name = t[2:]
        self.object_id = n[2:]

    def get_template(self):
        template = self._bits.templates.get_templates().get(self.template_name)
        assert template is not None, self.template_name
        return template

    def compute_value(self, section_header, attr_name):
        section = self.section.get_section(section_header)
        if section is not None:
            attr = section.get_attr(attr_name)
            if attr is not None:
                return attr.value
        return self.get_template().compute_value(section_header, attr_name)


class Region(GasDirHandler):
    class Data:
        def __init__(self):
            self.id = None

    def __init__(self, gas_dir, _map, data=None):
        super().__init__(gas_dir)
        self.map = _map
        self.data: Region.Data = data

    def get_name(self):
        return self.gas_dir.dir_name

    def load_data(self):
        main_file = self.gas_dir.get_gas_file('main')
        assert main_file is not None
        main = main_file.get_gas()
        region_section = main.get_section('t:region,n:region')
        data = Region.Data()
        guid = region_section.get_attr_value('guid')
        mesh_range = region_section.get_attr_value('mesh_range')
        scid_range = region_section.get_attr_value('scid_range')
        assert guid == mesh_range == scid_range
        data.id = Hex.parse(guid)
        self.data = data

    def store_data(self):
        main = self.gas_dir.get_or_create_gas_file('main', False).get_gas()
        region_section = main.get_or_create_section('t:region,n:region')
        region_id = Hex(self.data.id)
        region_section.set_attr_value('guid', region_id)
        region_section.set_attr_value('mesh_range', region_id)
        region_section.set_attr_value('scid_range', region_id)

    def get_data(self):
        if self.data is None:
            self.load_data()
        return self.data

    def save(self):
        if self.data is not None:
            self.store_data()
        self.gas_dir.save()

    # stuff for printouts

    def get_actors(self):
        objects_dir = self.gas_dir.get_subdir('objects')
        if objects_dir is None:
            return []
        if 'regular' in objects_dir.get_subdirs():
            objects_dir = objects_dir.get_subdir('regular')  # deal with multiple worlds another time
        actor_file = objects_dir.get_gas_file('actor')
        if actor_file is None:
            return []
        actor_sections = actor_file.get_gas().items
        return [GameObject(s, self.map.bits) for s in actor_sections]

    def get_stitches(self):
        stitch_helper_file = self.gas_dir.get_subdir('editor').get_gas_file('stitch_helper')
        if stitch_helper_file is None:
            return []
        stitch_sections = stitch_helper_file.get_gas().get_section('stitch_helper_data').get_sections()
        return [s.get_attr('dest_region').value for s in stitch_sections]

    def get_enemies(self):
        actors = self.get_actors()
        evil_actors = [a for a in actors if a.get_template().is_descendant_of('actor_evil')]
        enemies = [a for a in evil_actors if a.compute_value('actor', 'alignment') == 'aa_evil']
        return enemies

    def get_xp(self):
        # note: generators still missing. (also hireables but that's a topic for a separate method.) and summons
        enemies = self.get_enemies()
        xps = [e.compute_value('aspect', 'experience_value') for e in enemies]
        return sum([int(xp) if xp is not None else 0 for xp in xps])

    def actors_str(self):
        actors = self.get_actors()
        actor_templates = [a.template_name for a in actors]
        counts_by_template = {t: 0 for t in set(actor_templates)}
        for t in actor_templates:
            counts_by_template[t] += 1
        actor_templates_str = ': ' + ', '.join([str(count) + ' ' + t for t, count in counts_by_template.items()]) if len(actors) > 0 else ''
        return str(len(actors)) + ' actors' + actor_templates_str

    def xp_str(self):
        enemies = self.get_enemies()
        enemy_strs = [enemy.template_name + ' ' + (enemy.compute_value('aspect', 'experience_value') or '0') + ' XP' for enemy in enemies]
        counts = {t: 0 for t in set(enemy_strs)}
        for es in enemy_strs:
            counts[es] += 1
        enemy_xps_str = ': ' + ', '.join([str(count) + 'x ' + t for t, count in counts.items()]) if len(enemies) > 0 else ''
        return str(self.get_xp()) + ' XP' + enemy_xps_str

    def stitches_str(self):
        stitches = self.get_stitches()
        return ', '.join(stitches)

    def print(self, indent='', info='xp'):
        if info == 'actors':
            info_str = self.actors_str()
        elif info == 'stitches':
            info_str = self.stitches_str()
        elif info == 'xp':
            info_str = self.xp_str()
        else:
            info_str = None
        print(indent + self.gas_dir.dir_name + (' - ' + info_str if info_str is not None else ''))


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

    def __init__(self, gas_dir, bits, data=None):
        super().__init__(gas_dir)
        self.bits = bits
        self.data = data

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

    def save(self):
        if self.data is not None:
            self.store_data()
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

        return region

    def delete_region(self, name):
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        assert name in regions
        region: GasDir = regions[name]
        region.delete()

    def print(self, print_regions='stitches'):
        name = self.get_data().name
        screen_name = self.get_data().screen_name
        name_str = name.value + ' ' + screen_name if name is not None else screen_name
        description = str(self.get_data().description)
        regions = self.get_regions()
        print('Map: ' + name_str + ' (' + str(len(regions)) + ' regions) - ' + description)
        if print_regions:
            for region in regions.values():
                region.print('  ', print_regions)
