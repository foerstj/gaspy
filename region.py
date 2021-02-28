from gas import Hex, Gas, Section, Attribute
from gas_dir_handler import GasDirHandler
from terrain import Terrain, random_hex


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


class DirectionalLight:
    def __init__(self, id: Hex = None, color: Hex = 0xffffffff, draw_shadow: bool = False, intensity: float = 1, occlude_geometry: bool = False, on_timer: bool = False, direction: (float, float, float) = (0, 1, 0)):
        if id is None:
            id = Hex.parse(random_hex())
        self.id = id
        self.color = color
        self.draw_shadow = draw_shadow
        self.intensity = intensity
        self.occlude_geometry = occlude_geometry
        self.on_timer = on_timer
        self.direction = direction


class Region(GasDirHandler):
    class Data:
        def __init__(self):
            self.id = None

    def __init__(self, gas_dir, _map, data=None, terrain=None):
        super().__init__(gas_dir)
        self.map = _map
        self.data: Region.Data = data
        self.terrain: Terrain = terrain
        self.objects_non_interactive = None
        self.lights: list[DirectionalLight] = []

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

    def store_terrain(self):
        mesh_index = self.terrain.get_mesh_index()
        mesh_index = {Hex.parse('0x{:03X}{:05X}'.format(self.data.id, guid)): name for guid, name in mesh_index.items()}
        self.gas_dir.create_subdir('index', {
            'node_mesh_index': Gas([
                Section('node_mesh_index', [
                    Attribute(str(mesh_guid), mesh_name) for mesh_guid, mesh_name in mesh_index.items()
                ])
            ]),
            'streamer_node_index': Gas([
                Section('streamer_node_index', [
                    Attribute('*', node.guid) for node in self.terrain.nodes
                ])
            ])
        })
        node_sections: list = []
        for node in self.terrain.nodes:
            door_sections: list = [
                Section('door*', [
                    Attribute('id', door),
                    Attribute('farguid', far_node.guid),
                    Attribute('fardoor', far_door)
                ]) for door, (far_node, far_door) in node.doors.items()
            ]
            node_sections.append(
                Section('t:snode,n:' + str(node.guid), [
                    Attribute('guid', node.guid),
                    Attribute('mesh_guid', Hex.parse('0x{:03X}{:05X}'.format(self.data.id, self.terrain.mesh_index_lookup[node.mesh_name]))),
                    Attribute('texsetabbr', node.texture_set)
                ] + door_sections)
            )
        self.gas_dir.create_subdir('terrain_nodes', {
            'nodes': Gas([
                Section('t:terrain_nodes,n:siege_node_list', [
                    Attribute('ambient_color', self.terrain.ambient_light.color),
                    Attribute('ambient_intensity', self.terrain.ambient_light.intensity),
                    Attribute('object_ambient_color', self.terrain.ambient_light.object_color),
                    Attribute('object_ambient_intensity', self.terrain.ambient_light.object_intensity),
                    Attribute('actor_ambient_color', self.terrain.ambient_light.actor_color),
                    Attribute('actor_ambient_intensity', self.terrain.ambient_light.actor_intensity),
                    Attribute('targetnode', self.terrain.target_node.guid),
                ] + node_sections)
            ])
        })

    def store_objects(self):
        streamer_node_content_index = {}
        object_sections = []
        for i, (template_name, position, orientation) in enumerate(self.objects_non_interactive):
            oid = Hex.parse('0x{:03X}{:05X}'.format(self.data.id, i+1))
            object_sections.append(Section('t:{},n:{}'.format(template_name, oid), [
                Section('placement', [
                    Attribute('position', position),
                    Attribute('orientation', orientation)
                ])
            ]))
            node_guid = position.node_guid
            if node_guid not in streamer_node_content_index:
                streamer_node_content_index[node_guid] = []
            streamer_node_content_index[node_guid].append(oid)
        objects_dir = self.gas_dir.get_or_create_subdir('objects', False)
        objects_dir.create_gas_file('non_interactive', Gas(object_sections))
        index_dir = self.gas_dir.get_or_create_subdir('index', False)
        snci_attrs = []
        for node_guid, oids in streamer_node_content_index.items():
            snci_attrs.extend([Attribute(node_guid, oid) for oid in oids])
        index_dir.create_gas_file('streamer_node_content_index', Gas([Section('streamer_node_content_index', snci_attrs)]))

    def store_lights(self):
        # node: ambient light is part of terrain
        target_node = self.terrain.target_node
        lights_dir = self.gas_dir.get_or_create_subdir('lights', False)
        lights_dir.create_gas_file('lights', Gas([
            Section('lights', [
                Section('t:directional,n:light_'+str(dl.id), [
                    Attribute('active', True),
                    Attribute('affects_actors', True),
                    Attribute('affects_items', True),
                    Attribute('affects_terrain', True),
                    Attribute('inner_radius', float(0)),
                    Attribute('outer_radius', float(0)),
                    Attribute('color', dl.color),
                    Attribute('draw_shadow', dl.draw_shadow),
                    Attribute('intensity', float(dl.intensity)),
                    Attribute('occlude_geometry', dl.occlude_geometry),
                    Attribute('on_timer', dl.on_timer),
                    Section('direction', [
                        Attribute('node', target_node.guid),
                        Attribute('x', dl.direction[0]),
                        Attribute('y', dl.direction[1]),
                        Attribute('z', dl.direction[2]),
                    ])
                ]) for dl in self.lights
            ])
        ]))

    def ensure_north_vector(self):
        if not self.gas_dir.has_subdir('editor', False):
            self.gas_dir.create_subdir('editor', {
                'hotpoints': Gas([
                    Section('hotpoints', [
                        Section('t:hotpoint_directional,n:' + str(Hex(1)), [
                            Attribute('direction', '0,0,-1'),
                            Attribute('id', Hex(1))
                        ])
                    ])
                ])
            })

    def save(self):
        if self.data is not None:
            self.store_data()
        if self.terrain is not None:
            self.store_terrain()
        if self.objects_non_interactive is not None:
            self.store_objects()
        if self.lights is not None:
            self.store_lights()
        self.ensure_north_vector()
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
