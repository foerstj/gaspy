import os

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
    def __init__(self, gas_dir, _map):
        super().__init__(gas_dir)
        self.map = _map

    def get_name(self):
        return self.gas_dir.dir_name

    def save(self):
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
            def __init__(self, **kwargs):
                self.azimuth = kwargs.get('azimuth')
                self.distance = kwargs.get('distance')
                self.position = kwargs.get('position')

        def __init__(self, **kwargs):
            self.name = kwargs.get('name')
            self.screen_name = kwargs.get('screen_name')
            self.description = kwargs.get('description')
            self.dev_only = kwargs.get('dev_only')
            self.timeofday = kwargs.get('timeofday')
            self.use_node_mesh_index = kwargs.get('use_node_mesh_index')
            self.use_player_journal = kwargs.get('use_player_journal')
            self.camera = Map.Data.Camera(**kwargs['camera']) if 'camera' in kwargs else Map.Data.Camera()

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
        data.camera = Map.Data.Camera(
            azimuth=camera_section.get_attr_value('azimuth'),
            distance=camera_section.get_attr_value('distance'),
            position=camera_section.get_attr_value('position')
        ) if camera_section is not None else Map.Data.Camera()
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

    def get_regions(self):
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        return {name: Region(gas_dir, self) for name, gas_dir in regions.items()}

    def create_region(self, name):
        region_dirs = self.gas_dir.get_subdir('regions').get_subdirs()
        assert name not in region_dirs
        region_dir = GasDir(os.path.join(self.gas_dir.path, 'regions', name))
        region = Region(region_dir, self)
        region_dirs[name] = region_dir
        return region

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
