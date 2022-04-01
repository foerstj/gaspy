from gas.gas import Hex, Gas, Section, Attribute
from gas.gas_dir import GasDir
from .decals import DecalsGas

from .game_object import GameObject
from .game_object_data import GameObjectData
from .gas_dir_handler import GasDirHandler
from .light import Light, DirectionalLight
from .nodes_gas import NodesGas, SNode, Door
from .stitch_helper_gas import StitchHelperGas
from .terrain import Terrain, AmbientLight, TerrainNode


class Region(GasDirHandler):
    class Data:
        def __init__(self):
            self.id = None
            self.mesh_range = None
            self.scid_range = None

    def __init__(self, gas_dir: GasDir, _map, data=None, terrain: Terrain = None, lights: list[Light] = None):
        super().__init__(gas_dir)
        self.map = _map
        self.data: Region.Data = data
        self.terrain: Terrain = terrain
        self.generated_objects_non_interactive: list[GameObjectData] or None = None
        self.objects_non_interactive: list[GameObject] or None = None
        self.objects_loaded = False
        self.lights: list[Light] = lights
        self.stitch_helper: StitchHelperGas or None = None
        self.decals: DecalsGas or None = None

    def get_name(self):
        return self.gas_dir.dir_name

    def load_data(self):
        main_file = self.gas_dir.get_gas_file('main')
        assert main_file is not None
        main = main_file.get_gas()
        region_section = main.get_section('t:region,n:region')
        data = Region.Data()
        guid = Hex(region_section.get_attr_value('guid'))
        mesh_range = Hex(region_section.get_attr_value('mesh_range'))
        scid_range = Hex(region_section.get_attr_value('scid_range'))
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
            node.section = snode.nodesection if snode.nodesection != 0xffffffff else -1
            node.level = snode.nodelevel if snode.nodelevel != 0xffffffff else -1
            node.object = snode.nodeobject if snode.nodeobject != 0xffffffff else -1
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
        mesh_index = {Hex.parse('0x{:03X}{:05X}'.format(self.data.mesh_range, mesh_guid)): mesh_name for mesh_guid, mesh_name in mesh_index.items()}
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
        nodes_gas.ambient_color = self.terrain.ambient_light.terrain_color
        nodes_gas.ambient_intensity = self.terrain.ambient_light.terrain_intensity
        nodes_gas.object_ambient_color = self.terrain.ambient_light.object_color
        nodes_gas.object_ambient_intensity = self.terrain.ambient_light.object_intensity
        nodes_gas.actor_ambient_color = self.terrain.ambient_light.actor_color
        nodes_gas.actor_ambient_intensity = self.terrain.ambient_light.actor_intensity
        nodes_gas.targetnode = self.terrain.target_node.guid
        snodes = list()
        for node in self.terrain.nodes:
            mesh_guid = Terrain.mesh_index_lookup[node.mesh_name]
            mesh_guid = Hex.parse('0x{:03X}{:05X}'.format(self.data.mesh_range, mesh_guid))
            doors = [Door(door_id, far_node.guid, far_door) for door_id, (far_node, far_door) in node.doors.items()]
            nodesection = Hex(node.section if node.section != -1 else 0xffffffff)
            nodelevel = Hex(node.section if node.section != -1 else 0xffffffff)
            nodeobject = Hex(node.section if node.section != -1 else 0xffffffff)
            snode = SNode(node.guid, mesh_guid, node.texture_set, True, False, False, True, nodesection, nodelevel, nodeobject, doors)
            snodes.append(snode)
        nodes_gas.nodes = snodes
        self.gas_dir.create_subdir('terrain_nodes', {
            'nodes': nodes_gas.write_gas()
        })

    def store_generated_objects(self):
        snci_section = self.gas_dir.get_or_create_subdir('index').get_or_create_gas_file('streamer_node_content_index').get_gas().get_or_create_section('streamer_node_content_index')
        all_ioids = [Hex.parse('0x' + str(attr.value)[5:]) for attr in snci_section.get_attrs()]  # all internal object ids (internal meaning without scid range)
        streamer_node_content_index = {}
        object_sections = []
        last_ioid = 0
        for go_data in self.generated_objects_non_interactive:
            assert isinstance(go_data, GameObjectData)
            assert go_data.scid is None
            ioid = last_ioid + 1
            while ioid in all_ioids:  # find free oid
                ioid += 1
            last_ioid = ioid
            go_data.scid = Hex.parse('0x{:03X}{:05X}'.format(self.data.scid_range, ioid))

            object_sections.append(go_data.make_gas())
            node_guid = go_data.placement.position.node_guid
            if node_guid not in streamer_node_content_index:
                streamer_node_content_index[node_guid] = []
            streamer_node_content_index[node_guid].append(go_data.scid)
        objects_dir = self.gas_dir.get_or_create_subdir('objects')
        objects_dir.get_or_create_gas_file('non_interactive').get_gas().items.extend(object_sections)
        snci_attrs = []
        for node_guid, oids in streamer_node_content_index.items():
            snci_attrs.extend([Attribute(node_guid, oid) for oid in oids])
        snci_section.items.extend(snci_attrs)

    def load_objects(self):
        assert not self.objects_non_interactive
        self.objects_non_interactive = []
        objects_dir = self.gas_dir.get_subdir('objects')
        non_interactive_file = objects_dir.get_gas_file('non_interactive')
        non_interactive_gas = non_interactive_file.get_gas()
        for section in non_interactive_gas.items:
            go = GameObject(section, self.map.bits)
            self.objects_non_interactive.append(go)
        self.objects_loaded = True

    def store_objects(self):
        assert self.objects_non_interactive is not None
        objects_dir = self.gas_dir.get_or_create_subdir('objects')
        object_sections = [go.section for go in self.objects_non_interactive]
        if self.objects_loaded:
            objects_dir.get_gas_file('non_interactive').gas = Gas(object_sections)
        else:
            # if the objects weren't loaded and you try to override the file, this will fail, because it was most probably not intentional
            objects_dir.create_gas_file('non_interactive', Gas(object_sections))

    def load_lights(self):
        assert not self.lights
        lights_dir = self.gas_dir.get_subdir('lights')
        lights_file = lights_dir.get_gas_file('lights')
        lights_gas = lights_file.get_gas()
        lights_section = lights_gas.get_section('lights')
        self.lights = [Light.from_gas_section(section) for section in lights_section.items]

    def store_lights(self):
        # Note: storing directional / point / spot lights; ambient light is part of terrain.

        # prepare
        if self.terrain is not None:
            target_node = self.terrain.target_node
            for light in self.lights:
                if isinstance(light, DirectionalLight):
                    if light.direction.node_guid is None:
                        light.direction.node_guid = target_node.guid

        # store
        lights_dir = self.gas_dir.get_or_create_subdir('lights', False)
        lights_dir.get_or_create_gas_file('lights').gas = Gas([
            Section('lights', [
                light.to_gas_section() for light in self.lights
            ])
        ])

    def load_stitch_helper(self):
        assert self.stitch_helper is None
        stitch_helper_file = self.gas_dir.get_subdir('editor').get_gas_file('stitch_helper')
        self.stitch_helper = StitchHelperGas.load(stitch_helper_file)

    def store_stitch_helper(self):
        assert self.stitch_helper is not None
        stitch_helper_file = self.gas_dir.get_or_create_subdir('editor').get_or_create_gas_file('stitch_helper')
        stitch_helper_file.gas = self.stitch_helper.write_gas()

    def store_decals(self):
        assert self.decals is not None
        decals_file = self.gas_dir.get_or_create_subdir('decals').get_or_create_gas_file('decals')
        decals_file.gas = self.decals.write_gas()

    def ensure_north_vector(self):
        editor_subdir = self.gas_dir.get_or_create_subdir('editor')
        if not editor_subdir.has_gas_file('hotpoints'):
            hotpoints_gas = Gas([
                Section('hotpoints', [
                    Section('t:hotpoint_directional,n:' + str(Hex(1)), [
                        Attribute('direction', '0,0,-1'),
                        Attribute('id', Hex(1))
                    ])
                ])
            ])
            editor_subdir.create_gas_file('hotpoints', hotpoints_gas)

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
        if self.stitch_helper is not None:
            self.store_stitch_helper()
        if self.decals is not None:
            self.store_decals()
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
        objects_dir = self.get_objects_dir()
        if objects_dir is None:
            return []
        actor_file = objects_dir.get_gas_file('actor')
        if actor_file is None:
            return []
        actor_sections = actor_file.get_gas().items
        return [GameObject(s, self.map.bits) for s in actor_sections]

    def get_stitches(self):
        if self.stitch_helper is None:
            self.load_stitch_helper()
        return [se.dest_region for se in self.stitch_helper.stitch_editors]

    def get_npcs(self):
        actors = self.get_actors()
        npcs = [a for a in actors if a.get_template().is_descendant_of('actor_good') or a.get_template().is_descendant_of('npc') or a.get_template().is_descendant_of('hero')]
        return npcs

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

    def data_str(self):
        return f'guid: {self.get_data().id}'

    def print(self, indent='', info='data'):
        if info == 'actors':
            info_str = self.actors_str()
        elif info == 'stitches':
            info_str = self.stitches_str()
        elif info == 'xp':
            info_str = self.xp_str()
        elif info == 'trees':
            info_str = self.trees_str()
        elif info == 'data':
            info_str = self.data_str()
        else:
            info_str = None
        print(indent + self.gas_dir.dir_name + (' - ' + info_str if info_str is not None else ''))
