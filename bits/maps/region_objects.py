from bits.gas_dir_handler import GasDirHandler
from bits.maps.game_object import GameObject
from bits.maps.game_object_data import GameObjectData
from gas.gas import Attribute, Gas
from gas.gas_dir import GasDir
from gas.molecules import Hex


class RegionObjects(GasDirHandler):
    def __init__(self, gas_dir: GasDir, region):
        super().__init__(gas_dir)
        self.region = region
        self.generated_objects: list[GameObjectData] or None = None
        self.objects_non_interactive: list[GameObject] or None = None
        self.objects_loaded = False

    def get_objects_dir(self, world_level='regular'):
        assert world_level in ['regular', 'veteran', 'elite']
        objects_dir = self.gas_dir.get_subdir('objects')
        if objects_dir is None:
            return None
        if world_level == 'regular':
            if 'regular' in objects_dir.get_subdirs():
                objects_dir = objects_dir.get_subdir('regular')
        else:
            objects_dir = objects_dir.get_subdir(world_level)
        return objects_dir

    def store_generated_objects(self):
        snci_section = self.gas_dir.get_or_create_subdir('index').get_or_create_gas_file('streamer_node_content_index').get_gas().get_or_create_section('streamer_node_content_index')
        all_ioids = [Hex.parse('0x' + str(attr.value)[5:]) for attr in snci_section.get_attrs()]  # all internal object ids (internal meaning without scid range)
        streamer_node_content_index = {}
        object_sections = []
        last_ioid = 0
        for go_data in self.generated_objects:
            assert isinstance(go_data, GameObjectData)
            assert go_data.scid is None
            ioid = last_ioid + 1
            while ioid in all_ioids:  # find free oid
                ioid += 1
            last_ioid = ioid
            go_data.scid = Hex.parse('0x{:03X}{:05X}'.format(self.region.data.scid_range, ioid))

            object_sections.append(go_data.make_gas())
            node_guid = go_data.placement.position.node_guid
            if node_guid not in streamer_node_content_index:
                streamer_node_content_index[node_guid] = []
            streamer_node_content_index[node_guid].append(go_data.scid)
        objects_dir = self.gas_dir.get_or_create_subdir('objects')
        objects_dir.get_or_create_gas_file('_new').get_gas().items.extend(object_sections)  # Put into a new file, let Siege Editor sort them in
        snci_attrs = []
        for node_guid, oids in streamer_node_content_index.items():
            snci_attrs.extend([Attribute(node_guid, oid) for oid in oids])
        snci_section.items.extend(snci_attrs)

    def _do_load_objects(self, object_type: str, world_level='regular'):
        objects_dir = self.get_objects_dir(world_level)
        if objects_dir is None:
            return None
        objects_file = objects_dir.get_gas_file(object_type)
        if objects_file is None:
            return None
        objects_gas = objects_file.get_gas()
        objects = []
        for section in objects_gas.items:
            go = GameObject(section, self.region.map.bits)
            objects.append(go)
        return objects

    def do_load_objects_actor(self, world_level='regular'):
        return self._do_load_objects('actor', world_level)

    def do_load_objects_generator(self, world_level='regular'):
        return self._do_load_objects('generator', world_level)

    def do_load_objects_interactive(self):
        return self._do_load_objects('interactive')

    def do_load_objects_non_interactive(self):
        return self._do_load_objects('non_interactive')

    def do_load_objects_special(self):
        return self._do_load_objects('special')

    def load_objects(self):
        assert not self.objects_loaded
        assert not self.objects_non_interactive
        self.objects_non_interactive = self.do_load_objects_non_interactive()
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

    def store(self):
        if self.generated_objects is not None:
            self.store_generated_objects()
        if self.objects_non_interactive is not None:
            self.store_objects()
