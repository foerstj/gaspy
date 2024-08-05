from bits.maps.terrain import TerrainNode


class NodeMask:
    def matches(self, node: TerrainNode) -> bool:
        raise NotImplementedError()

    @classmethod
    def parse(cls, node_mask_str: str) -> 'NodeMask':
        node_mask_3strs = (node_mask_str + '::').split(':')[:3]
        section, level, object = [int(s) if s else -1 for s in node_mask_3strs]
        return FadeNodeMask(section, level, object)


class FadeNodeMask(NodeMask):
    def __init__(self, section: int = -1, level: int = -1, object: int = -1):
        self.section = section
        self.level = level
        self.object = object

    @classmethod
    def number_matches(cls, mask_number, node_number):
        return mask_number == -1 or mask_number == node_number

    def matches(self, node: TerrainNode) -> bool:
        return self.number_matches(self.section, node.section) and self.number_matches(self.level, node.level) and self.number_matches(self.object, node.object)


class NodeMasks:
    def __init__(self, included_nodes: list[str], excluded_nodes: list[str]):
        self.included_nodes = [NodeMask.parse(nm_def) for nm_def in included_nodes]
        self.excluded_nodes = [NodeMask.parse(nm_def) for nm_def in excluded_nodes]

    def is_included(self, node: TerrainNode) -> bool:
        if len(self.included_nodes) > 0:
            if not any([node_mask.matches(node) for node_mask in self.included_nodes]):
                return False
        if len(self.excluded_nodes) > 0:
            if any([node_mask.matches(node) for node_mask in self.excluded_nodes]):
                return False
        return True

    def has_filters(self):
        return len(self.included_nodes) > 0 or len(self.excluded_nodes) > 0
