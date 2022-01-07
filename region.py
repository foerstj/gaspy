from gas import Hex, Gas, Section, Attribute, Position, Quaternion
from gas_dir import GasDir
from gas_dir_handler import GasDirHandler
from nodes_gas import NodesGas, SNode, Door
from templates import Template
from terrain import Terrain, random_hex, AmbientLight, TerrainNode


class GameObject:
    def __init__(self, section: Section, bits):
        self._bits = bits
        self.section = section
        [t, n] = section.header.split(',')
        assert t.startswith('t:')
        assert n.startswith('n:')
        self.template_name: str = t[2:]
        self.object_id: str = n[2:]

    def get_template(self) -> Template:
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
    def __init__(
            self,
            dl_id: Hex = None,
            color: Hex = 0xffffffff,
            draw_shadow: bool = False,
            intensity: float = 1,
            occlude_geometry: bool = False,
            on_timer: bool = False,
            direction: (float, float, float) = (0, 1, 0)):
        if dl_id is None:
            dl_id = Hex.parse(random_hex())
        self.id = dl_id
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
            self.mesh_range = None
            self.scid_range = None

    def __init__(self, gas_dir: GasDir, _map, data=None, terrain=None):
        super().__init__(gas_dir)
        self.map = _map
        self.data: Region.Data = data
        self.terrain: Terrain = terrain
        self.generated_objects_non_interactive: list[(str, Position, Quaternion, float)] or None = None
        self.objects_non_interactive: list[GameObject] or None = None
        self.lights: list[DirectionalLight] or None = None

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
        # assert guid == mesh_range == scid_range  # not the case in map_world
        data.id = guid
        data.mesh_range = mesh_range
        data.scid_range = scid_range
        self.data = data

    def store_data(self):
        main = self.gas_dir.get_or_create_gas_file('main', False).get_gas()
        region_section = main.get_or_create_section('t:region,n:region')
        region_section.set_attr_value('guid', Hex(self.data.id))
        region_section.set_attr_value('mesh_range', Hex(self.data.mesh_range))
        region_section.set_attr_value('scid_range', Hex(self.data.scid_range))

    def get_data(self):
        if self.data is None:
            self.load_data()
        return self.data

    def load_terrain(self):
        node_mesh_index_file = self.gas_dir.get_subdir('index').get_gas_file('node_mesh_index')
        nmi = {Hex.parse(attr.name): attr.value for attr in node_mesh_index_file.get_gas().get_section('node_mesh_index').get_attrs()}

        nodes_gas_file = self.gas_dir.get_subdir('terrain_nodes').get_gas_file('nodes')
        nodes_gas = NodesGas.load(nodes_gas_file)

        # ambient light
        ambient_light = AmbientLight(
            nodes_gas.ambient_color,
            nodes_gas.ambient_intensity,
            nodes_gas.object_ambient_color,
            nodes_gas.object_ambient_intensity,
            nodes_gas.actor_ambient_color,
            nodes_gas.actor_ambient_intensity)

        # nodes
        nodes = list()
        nodes_dict = dict()
        for snode in nodes_gas.nodes:
            assert snode.mesh_guid in nmi, 'unknown mesh_guid: ' + str(snode.mesh_guid)
            mesh_name = nmi[snode.mesh_guid]
            node = TerrainNode(snode.guid, mesh_name, snode.texsetabbr)
            nodes_dict[snode.guid] = node
            nodes.append(node)
        for snode in nodes_gas.nodes:
            node = nodes_dict[snode.guid]
            for door in snode.doors:
                far_node = nodes_dict[door.farguid]
                node.doors[door.id] = (far_node, door.fardoor)

        target_node = nodes_dict[nodes_gas.targetnode]

        terrain = Terrain()
        terrain.nodes = nodes
        terrain.target_node = target_node
        terrain.ambient_light = ambient_light
        self.terrain = terrain

    def store_terrain(self):
        # index
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

        # terrain_nodes
        nodes_gas = NodesGas()
        nodes_gas.ambient_color = self.terrain.ambient_light.color
        nodes_gas.ambient_intensity = self.terrain.ambient_light.intensity
        nodes_gas.object_ambient_color = self.terrain.ambient_light.object_color
        nodes_gas.object_ambient_intensity = self.terrain.ambient_light.object_intensity
        nodes_gas.actor_ambient_color = self.terrain.ambient_light.actor_color
        nodes_gas.actor_ambient_intensity = self.terrain.ambient_light.actor_intensity
        nodes_gas.targetnode = self.terrain.target_node.guid
        snodes = list()
        for node in self.terrain.nodes:
            mesh_guid = Terrain.mesh_index_lookup[node.mesh_name]
            doors = [Door(door_id, far_node.guid, far_door) for door_id, (far_node, far_door) in node.doors.items()]
            snode = SNode(node.guid, mesh_guid, node.texture_set, True, False, False, True, Hex(1), Hex(-1), Hex(-1), doors)
            snodes.append(snode)
        nodes_gas.nodes = snodes
        self.gas_dir.create_subdir('terrain_nodes', {
            'nodes': nodes_gas.write_gas()
        })

    def store_generated_objects(self):
        snci_section = self.gas_dir.get_or_create_subdir('index', False).get_or_create_gas_file('streamer_node_content_index').get_gas().get_or_create_section('streamer_node_content_index')
        all_ioids = [Hex.parse('0x' + str(attr.value)[5:]) for attr in snci_section.get_attrs()]  # all internal object ids (internal meaning without scid range)
        streamer_node_content_index = {}
        object_sections = []
        last_ioid = 0
        for i, (template_name, position, orientation, size) in enumerate(self.generated_objects_non_interactive):
            ioid = last_ioid + 1
            while ioid in all_ioids:  # find free oid
                ioid += 1
            last_ioid = ioid
            oid = Hex.parse('0x{:03X}{:05X}'.format(self.data.scid_range, ioid))
            obj_sections = []
            if size is not None and size != 1:
                obj_sections.append(Section('aspect', [
                    Attribute('scale_multiplier', size)
                ]))
            obj_sections.append(Section('placement', [
                Attribute('position', position),
                Attribute('orientation', orientation)
            ]))
            object_sections.append(Section('t:{},n:{}'.format(template_name, oid), obj_sections))
            node_guid = position.node_guid
            if node_guid not in streamer_node_content_index:
                streamer_node_content_index[node_guid] = []
            streamer_node_content_index[node_guid].append(oid)
        objects_dir = self.gas_dir.get_or_create_subdir('objects', False)
        objects_dir.get_or_create_gas_file('non_interactive').get_gas().items.extend(object_sections)
        snci_attrs = []
        for node_guid, oids in streamer_node_content_index.items():
            snci_attrs.extend([Attribute(node_guid, oid) for oid in oids])
        snci_section.items.extend(snci_attrs)

    def load_objects(self):
        assert not self.objects_non_interactive
        self.objects_non_interactive = []
        objects_dir = self.get_objects_dir()
        non_interactive_file = objects_dir.get_gas_file('non_interactive')
        non_interactive_gas = non_interactive_file.get_gas()
        for section in non_interactive_gas.items:
            go = GameObject(section, self.map.bits)
            self.objects_non_interactive.append(go)

    def store_objects(self):
        assert self.objects_non_interactive
        objects_dir = self.get_objects_dir()
        object_sections = [go.section for go in self.objects_non_interactive]
        objects_dir.create_gas_file('non_interactive', Gas(object_sections))

    def store_lights(self):
        # note: storing directional lights; ambient light is part of terrain
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
        if self.generated_objects_non_interactive is not None:
            self.store_generated_objects()
        if self.objects_non_interactive is not None:
            self.store_objects()
        if self.lights is not None:
            self.store_lights()
        self.ensure_north_vector()
        self.gas_dir.save()

    def get_node_ids(self) -> list[Hex]:
        node_index_file = self.gas_dir.get_subdir('index').get_gas_file('streamer_node_index')
        node_id_attrs: list[Attribute] = node_index_file.get_gas().get_section('streamer_node_index').items
        return [attr.value for attr in node_id_attrs]

    def get_scids(self) -> list[Hex]:
        node_content_index_file = self.gas_dir.get_subdir('index').get_gas_file('streamer_node_content_index')
        scid_attrs: list[Attribute] = node_content_index_file.get_gas().get_section('streamer_node_content_index').items
        return [attr.value for attr in scid_attrs]

    # stuff for printouts

    def get_objects_dir(self):
        objects_dir = self.gas_dir.get_subdir('objects')
        if objects_dir is None:
            return None
        if 'regular' in objects_dir.get_subdirs():
            objects_dir = objects_dir.get_subdir('regular')  # deal with multiple worlds another time
        return objects_dir

    def get_actors(self):
        actor_file = self.get_objects_dir().get_gas_file('actor')
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

    def get_non_interactives(self):
        non_interactive_file = self.get_objects_dir().get_gas_file('non_interactive')
        if non_interactive_file is None:
            return []
        ni_sections = non_interactive_file.get_gas().items
        return [GameObject(s, self.map.bits) for s in ni_sections]

    def get_trees(self):
        nis = self.get_non_interactives()
        return [ni for ni in nis if ni.template_name.startswith('tree_')]

    def trees_str(self):
        trees = self.get_trees()
        tree_templates = [a.template_name for a in trees]
        counts_by_template = {t: 0 for t in set(tree_templates)}
        for t in tree_templates:
            counts_by_template[t] += 1
        tree_templates_str = ': ' + ', '.join([str(count) + ' ' + t for t, count in counts_by_template.items()]) if len(trees) > 0 else ''
        return str(len(trees)) + ' trees' + tree_templates_str

    def print(self, indent='', info='xp'):
        if info == 'actors':
            info_str = self.actors_str()
        elif info == 'stitches':
            info_str = self.stitches_str()
        elif info == 'xp':
            info_str = self.xp_str()
        elif info == 'trees':
            info_str = self.trees_str()
        else:
            info_str = None
        print(indent + self.gas_dir.dir_name + (' - ' + info_str if info_str is not None else ''))
