# Handler for nodes.gas file
from gas import Hex, Gas, Section, Attribute
from gas_file import GasFile


class Door:
    def __init__(self, id: int, farguid: Hex, fardoor: int):
        self.id: int = id
        self.farguid = farguid
        self.fardoor = fardoor


class SNode:
    def __init__(
            self,
            guid: Hex,
            mesh_guid: Hex,
            texsetabbr: str,
            bounds_camera: bool,
            camera_fade: bool,
            occludes_camera: bool,
            occludes_light: bool,
            nodesection: Hex,
            nodelevel: Hex,
            nodeobject: Hex,
            doors: list[Door] = None):
        self.guid = guid
        self.mesh_guid = mesh_guid
        self.texsetabbr = texsetabbr
        self.bounds_camera = bounds_camera
        self.camera_fade = camera_fade
        self.occludes_camera = occludes_camera
        self.occludes_light = occludes_light
        self.nodesection = nodesection
        self.nodelevel = nodelevel
        self.nodeobject = nodeobject
        self.doors = doors


class NodesGas:
    def __init__(
            self,
            ambient_color: Hex = 0xffffffff,
            ambient_intensity: float = 1,
            object_ambient_color: Hex = 0xffffffff,
            object_ambient_intensity: float = 1,
            actor_ambient_color: Hex = 0xffffffff,
            actor_ambient_intensity: float = 1,
            targetnode: Hex = 0,
            nodes: list[SNode] = None):
        self.ambient_color = ambient_color
        self.ambient_intensity = ambient_intensity
        self.object_ambient_color = object_ambient_color
        self.object_ambient_intensity = object_ambient_intensity
        self.actor_ambient_color = actor_ambient_color
        self.actor_ambient_intensity = actor_ambient_intensity
        self.targetnode = targetnode
        self.nodes = nodes

    @classmethod
    def load(cls, gas_file: GasFile):
        gas = gas_file.get_gas()
        siege_node_list = gas.get_section('t:terrain_nodes,n:siege_node_list')
        nodes_gas = NodesGas()

        # attributes
        nodes_gas.ambient_color = siege_node_list.get_attr_value('ambient_color')
        nodes_gas.ambient_intensity = siege_node_list.get_attr_value('ambient_intensity')
        nodes_gas.object_ambient_color = siege_node_list.get_attr_value('object_ambient_color')
        nodes_gas.object_ambient_intensity = siege_node_list.get_attr_value('object_ambient_intensity')
        nodes_gas.actor_ambient_color = siege_node_list.get_attr_value('actor_ambient_color')
        nodes_gas.actor_ambient_intensity = siege_node_list.get_attr_value('actor_ambient_intensity')
        nodes_gas.target_node = siege_node_list.get_attr_value('targetnode')

        node_sections = siege_node_list.get_sections()
        nodes = list()
        for node_section in node_sections:
            guid = node_section.get_attr_value('guid')
            mesh_guid = node_section.get_attr_value('mesh_guid')
            texsetabbr = node_section.get_attr_value('texsetabbr')
            bounds_camera = node_section.get_attr_value('bounds_camera')
            camera_fade = node_section.get_attr_value('camera_fade')
            occludes_camera = node_section.get_attr_value('occludes_camera')
            occludes_light = node_section.get_attr_value('occludes_light')
            nodesection = node_section.get_attr_value('nodesection')
            nodelevel = node_section.get_attr_value('nodelevel')
            nodeobject = node_section.get_attr_value('nodeobject')
            snode = SNode(guid, mesh_guid, texsetabbr, bounds_camera, camera_fade, occludes_camera, occludes_light, nodesection, nodelevel, nodeobject)
            nodes.append(snode)
            snode.doors = list()
            door_sections = node_section.get_sections('door*')
            for door_section in door_sections:
                id = door_section.get_attr_value('id')
                farguid = door_section.get_attr_value('farguid')
                fardoor = door_section.get_attr_value('fardoor')
                snode.doors.append(Door(id, farguid, fardoor))
        nodes_gas.nodes = nodes

        return nodes_gas

    def write_gas(self) -> Gas:
        node_sections = [Section('t:snode,n:' + snode.guid.to_str_lower(), [
            Attribute('bounds_camera', snode.bounds_camera),
            Attribute('camera_fade', snode.camera_fade),
            Attribute('guid', snode.guid),
            Attribute('mesh_guid', snode.mesh_guid),
            Attribute('nodelevel', snode.nodelevel),
            Attribute('nodeobject', snode.nodeobject),
            Attribute('nodesection', snode.nodesection),
            Attribute('occludes_camera', snode.occludes_camera),
            Attribute('occludes_light', snode.occludes_light),
            Attribute('texsetabbr', snode.texsetabbr),
        ] + [Section('door*', [
            Attribute('fardoor', door.fardoor),
            Attribute('farguid', door.farguid),
            Attribute('id', door.id),
        ]) for door in snode.doors]) for snode in self.nodes]
        return Gas([
            Section('t:terrain_nodes,n:siege_node_list', [
                Attribute('ambient_color', self.ambient_color),
                Attribute('ambient_intensity', self.ambient_intensity),
                Attribute('object_ambient_color', self.object_ambient_color),
                Attribute('object_ambient_intensity', self.object_ambient_intensity),
                Attribute('actor_ambient_color', self.actor_ambient_color),
                Attribute('actor_ambient_intensity', self.actor_ambient_intensity),
                Attribute('targetnode', self.targetnode)
            ] + node_sections)
        ])
