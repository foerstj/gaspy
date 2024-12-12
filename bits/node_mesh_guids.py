from gas.gas_dir import GasDir


class NodeMeshGuids:
    def __init__(self, bits_dir: GasDir):
        self.bits_dir = bits_dir
        self.node_mesh_guids = None

    def get_node_mesh_guids(self) -> dict[str, str]:  # dict guid->filename
        if self.node_mesh_guids is None:
            self.node_mesh_guids = self.load_node_mesh_guids(self.bits_dir)
        return self.node_mesh_guids

    @classmethod
    def load_node_mesh_guids_recursive(cls, gas_dir: GasDir, node_mesh_guids: dict):
        for gas_file in gas_dir.get_gas_files().values():
            mesh_file_sections = gas_file.get_gas().find_sections_recursive('mesh_file*')
            for mesh_file_section in mesh_file_sections:
                filename = mesh_file_section.get_attr_value('filename')
                guid = mesh_file_section.get_attr_value('guid').strip()
                node_mesh_guids[guid] = filename
        for subdir in gas_dir.get_subdirs().values():
            cls.load_node_mesh_guids_recursive(subdir, node_mesh_guids)

    @classmethod
    def load_node_mesh_guids(cls, bits_dir: GasDir):
        siege_nodes_dir = bits_dir.get_subdir('world').get_subdir('global').get_subdir('siege_nodes')
        node_mesh_guids = {}
        cls.load_node_mesh_guids_recursive(siege_nodes_dir, node_mesh_guids)
        return node_mesh_guids

    def print(self):
        for guid, name in self.get_node_mesh_guids().items():
            print(f'{guid}: {name}')
