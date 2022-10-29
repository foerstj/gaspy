import os

from gas.gas import Hex, Gas, Section, Attribute
from gas.gas_dir import GasDir
from .conversations_gas import ConversationsGas
from .decals_gas import DecalsGas

from .game_object import GameObject
from bits.gas_dir_handler import GasDirHandler
from .light import Light, DirectionalLight
from .nodes_gas import NodesGas, SNode, Door
from .region_objects import RegionObjects
from .stitch_helper_gas import StitchHelperGas
from .terrain import Terrain, AmbientLight, TerrainNode
from ..templates import Templates, Template


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
        self.lights: list[Light] = lights
        self.stitch_helper: StitchHelperGas or None = None
        self.decals: DecalsGas or None = None
        self.conversations: ConversationsGas or None = None
        self.objects = RegionObjects(self.gas_dir, self)

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
            node.bounds_camera = snode.bounds_camera
            node.camera_fade = snode.camera_fade
            node.occludes_camera = snode.occludes_camera
            node.occludes_light = snode.occludes_light
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
        terrain.node_mesh_index = nmi
        self.terrain = terrain

    def store_terrain(self):
        # index
        mesh_index = self.terrain.create_node_mesh_index(self.get_data().mesh_range)
        index_dir = self.gas_dir.get_or_create_subdir('index')
        index_dir.get_or_create_gas_file('node_mesh_index').gas = Gas([
            Section('node_mesh_index', [
                Attribute(mesh_guid.to_str_lower(), mesh_name) for mesh_guid, mesh_name in mesh_index.items()
            ])
        ])
        index_dir.get_or_create_gas_file('streamer_node_index').gas = Gas([
            Section('streamer_node_index', [
                Attribute('*', node.guid) for node in self.terrain.nodes
            ])
        ])

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
        reverse_nmi = self.terrain.reverse_node_mesh_index()
        for node in self.terrain.nodes:
            mesh_guid = reverse_nmi[node.mesh_name]
            doors = [Door(door_id, far_node.guid, far_door) for door_id, (far_node, far_door) in node.doors.items()]
            nodesection = Hex(node.section if node.section != -1 else 0xffffffff)
            nodelevel = Hex(node.level if node.level != -1 else 0xffffffff)
            nodeobject = Hex(node.object if node.object != -1 else 0xffffffff)
            snode = SNode(node.guid, mesh_guid, node.texture_set, node.bounds_camera, node.camera_fade, node.occludes_camera, node.occludes_light, nodesection, nodelevel, nodeobject, doors)
            snodes.append(snode)
        nodes_gas.nodes = snodes
        terrain_nodes_dir = self.gas_dir.get_or_create_subdir('terrain_nodes')
        terrain_nodes_dir.get_or_create_gas_file('nodes').gas = nodes_gas.write_gas()

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

    def get_lights(self) -> list[Light]:
        if not self.lights:
            self.load_lights()
        return self.lights

    def load_stitch_helper(self):
        assert self.stitch_helper is None
        stitch_helper_file = self.gas_dir.get_subdir('editor').get_gas_file('stitch_helper')
        self.stitch_helper = StitchHelperGas.load(stitch_helper_file)

    def store_stitch_helper(self):
        assert self.stitch_helper is not None
        stitch_helper_file = self.gas_dir.get_or_create_subdir('editor').get_or_create_gas_file('stitch_helper')
        stitch_helper_file.gas = self.stitch_helper.write_gas()

    def load_conversations(self):
        assert self.conversations is None
        conversations_dir = self.gas_dir.get_subdir('conversations')
        if conversations_dir is None:
            return
        conversations_file = conversations_dir.get_gas_file('conversations')
        self.conversations = ConversationsGas.load(conversations_file)

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
        self.objects.store()
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
        assert node_index_file, self.get_name() + ': streamer_node_index not found'
        node_id_attrs: list[Attribute] = node_index_file.get_gas().get_section('streamer_node_index').items
        return [attr.value for attr in node_id_attrs]

    def get_scids(self) -> list[Hex]:
        node_content_index_file = self.gas_dir.get_subdir('index').get_gas_file('streamer_node_content_index')
        scid_attrs: list[Attribute] = node_content_index_file.get_gas().get_section('streamer_node_content_index').items
        return [attr.value for attr in scid_attrs]

    def delete_lnc(self):
        lnc_file = os.path.join(self.gas_dir.get_subdir('terrain_nodes').path, 'siege_nodes.lnc')
        if os.path.isfile(lnc_file):
            os.remove(lnc_file)

    # stuff for printouts

    def get_actors(self, world_level='regular') -> list[GameObject]:
        return self.objects.do_load_objects_actor(world_level) or []

    def get_stitches(self):
        if self.stitch_helper is None:
            self.load_stitch_helper()
        return [se.dest_region for se in self.stitch_helper.stitch_editors]

    def get_npcs(self):
        actors = self.get_actors()
        npcs = [a for a in actors if a.get_template().is_descendant_of('actor_good') or a.get_template().is_descendant_of('npc') or a.get_template().is_descendant_of('hero')]
        return npcs

    # Enemy actors placed directly. Enemies from generators, summons etc. not included
    def get_enemy_actors(self, world_level='regular'):
        actors = self.get_actors(world_level)
        evil_actors = [a for a in actors if a.get_template().is_descendant_of('actor_evil')]
        enemies = [a for a in evil_actors if a.compute_value('actor', 'alignment') == 'aa_evil']
        return enemies

    def get_generated_enemies(self, world_level='regular') -> dict[str, list[int, Template]]:
        generated_enemies = dict()
        generators = self.objects.do_load_objects_generator(world_level) or []
        templates: Templates = self.map.bits.templates
        generator_components = ['advanced_a2', 'auto_object_exploding', 'basic', 'breakable', 'cage', 'dumb_guy', 'in_object', 'multiple_mp', 'object_exploding', 'object_pcontent', 'random']
        generator_components = ['generator_'+x for x in generator_components]
        for gen in generators:
            num_enemies = 0
            for gen_comp in generator_components:
                child_template_name = gen.compute_value(gen_comp, 'child_template_name')
                if child_template_name is None:
                    continue
                child_template_name = child_template_name.strip('"').lower()
                child_template = templates.get_templates().get(child_template_name)
                if child_template is None:
                    print(f'Generator child_template_name not found: {gen.template_name} {gen.object_id}: {child_template_name}')
                    continue
                if not child_template.is_descendant_of('actor_evil'):
                    continue  # not an enemy
                num_enemies += 1
                num_children_incubating = gen.compute_value(gen_comp, 'num_children_incubating')
                if num_children_incubating is None:
                    num_children_incubating = 1
                if child_template_name not in generated_enemies:
                    generated_enemies[child_template_name] = [0, child_template]
                generated_enemies[child_template_name][0] += int(num_children_incubating)
            if num_enemies != 1:
                pass  # print(f'Generator with {num_enemies} enemy templates: {gen.template_name} {gen.object_id}')
        return generated_enemies

    def get_xp(self, world_level='regular'):
        # note: generators still missing. (also hireables but that's a topic for a separate method.) and summons
        xp = 0

        for enemy in self.get_enemy_actors(world_level):
            enemy_xp = enemy.compute_value('aspect', 'experience_value')
            if enemy_xp is None:
                # print(f'Enemy without aspect:experience_value: {enemy.template_name} {enemy.object_id}')  # goblin coils
                continue
            xp += int(enemy_xp)

        generated_enemies = self.get_generated_enemies(world_level)
        for count, enemy_template in generated_enemies.values():
            assert isinstance(enemy_template, Template)
            gen_enemy_xp = enemy_template.compute_value('aspect', 'experience_value')
            if gen_enemy_xp is None:
                print(f'Enemy without aspect:experience_value: {enemy_template.name}')
                continue
            xp += int(gen_enemy_xp) * int(count)

        return xp

    def actors_str(self):
        actors = self.get_actors()
        actor_templates = [a.template_name for a in actors]
        counts_by_template = {t: 0 for t in set(actor_templates)}
        for t in actor_templates:
            counts_by_template[t] += 1
        actor_templates_str = ': ' + ', '.join([str(count) + ' ' + t for t, count in counts_by_template.items()]) if len(actors) > 0 else ''
        return str(len(actors)) + ' actors' + actor_templates_str

    def xp_str(self):
        enemies = self.get_enemy_actors()
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
        return self.objects.do_load_objects_non_interactive() or []

    def get_plants(self):
        nis = self.get_non_interactives()
        return [ni for ni in nis if ni.is_plant()]

    def plants_str(self):
        plants = self.get_plants()
        plants_str = f'{len(plants)} plants'
        if len(plants) > 0:
            plants_str += ': '
            tree_templates = [a.template_name for a in plants]
            counts_by_template = {t: 0 for t in set(tree_templates)}
            for t in tree_templates:
                counts_by_template[t] += 1
            plants_str += ', '.join([f'{count} {t}' for t, count in counts_by_template.items()])
        return plants_str

    def data_str(self):
        return f'guid: {self.get_data().id}'

    def print(self, indent='', info='data'):
        if info == 'actors':
            info_str = self.actors_str()
        elif info == 'stitches':
            info_str = self.stitches_str()
        elif info == 'xp':
            info_str = self.xp_str()
        elif info == 'plants':
            info_str = self.plants_str()
        elif info == 'data':
            info_str = self.data_str()
        else:
            info_str = None
        print(indent + self.get_name() + (' - ' + info_str if info_str is not None else ''))
