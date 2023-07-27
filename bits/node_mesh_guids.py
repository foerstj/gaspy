from bits.bits import Bits
from gas.gas_dir import GasDir


class NodeMeshGuids:
    def __init__(self, bits: Bits):
        self.bits = bits
        self.node_mesh_guids = None

    def get_node_mesh_guids(self) -> dict[str, str]:  # dict guid->filename
        if self.node_mesh_guids is None:
            self.node_mesh_guids = self.load_node_mesh_guids(self.bits)
        return self.node_mesh_guids

    @classmethod
    def load_node_mesh_guids_recursive(cls, gas_dir: GasDir, node_mesh_guids: dict):
        for gas_file in gas_dir.get_gas_files().values():
            mesh_file_sections = gas_file.get_gas().find_sections_recursive('mesh_file*')
            for mesh_file_section in mesh_file_sections:
                filename = mesh_file_section.get_attr_value('filename')
                guid = mesh_file_section.get_attr_value('guid')
                node_mesh_guids[guid] = filename
        for subdir in gas_dir.get_subdirs().values():
            cls.load_node_mesh_guids_recursive(subdir, node_mesh_guids)

    @classmethod
    def load_node_mesh_guids(cls, bits: Bits):
        assert bits.gas_dir.has_subdir('world'), 'Conversion to NMI requires Bits/world/global/siege_nodes to be extracted'
        assert bits.gas_dir.get_subdir('world').has_subdir('global'), 'Conversion to NMI requires Bits/world/global/siege_nodes to be extracted'
        assert bits.gas_dir.get_subdir('world').get_subdir('global').has_subdir('siege_nodes'), 'Conversion to NMI requires Bits/world/global/siege_nodes to be extracted'
        siege_nodes_dir = bits.gas_dir.get_subdir('world').get_subdir('global').get_subdir('siege_nodes')
        node_mesh_guids = {}
        cls.load_node_mesh_guids_recursive(siege_nodes_dir, node_mesh_guids)
        return node_mesh_guids
