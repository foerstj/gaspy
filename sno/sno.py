# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Sno(KaitaiStruct):

    class Floor(Enum):
        ignored = 536870912
        floor = 1073741825
        water = 2147483648
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(4)
        if not self.magic == b"\x53\x4E\x4F\x44":
            raise kaitaistruct.ValidationNotEqualError(b"\x53\x4E\x4F\x44", self.magic, self._io, u"/seq/0")
        self.version = Sno.Version(self._io, self, self._root)
        self.door_count = self._io.read_u4le()
        self.spot_count = self._io.read_u4le()
        self.vertex_count = self._io.read_u4le()
        self.triangle_count = self._io.read_u4le()
        self.texture_count = self._io.read_u4le()
        self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
        self.centroid_offset = Sno.V3(self._io, self, self._root)
        self.tile = self._io.read_u4le()
        self.reserved0 = self._io.read_u4le()
        self.reserved1 = self._io.read_u4le()
        self.reserved2 = self._io.read_u4le()
        if  ((self.version.major > 6) or ( ((self.version.major == 6) and (self.version.minor >= 2)) )) :
            self.checksum = self._io.read_u4le()

        self.door_array = [None] * (self.door_count)
        for i in range(self.door_count):
            self.door_array[i] = Sno.Door(self._io, self, self._root)

        self.spot_array = [None] * (self.spot_count)
        for i in range(self.spot_count):
            self.spot_array[i] = Sno.Spot(self._io, self, self._root)

        self.vertex_array = [None] * (self.vertex_count)
        for i in range(self.vertex_count):
            self.vertex_array[i] = Sno.Vertex(self._io, self, self._root)

        self.surface_array = [None] * (self.texture_count)
        for i in range(self.texture_count):
            self.surface_array[i] = Sno.Surface(self._io, self, self._root)

        self.logical_mesh_count = self._io.read_u4le()
        self.logical_mesh = [None] * (self.logical_mesh_count)
        for i in range(self.logical_mesh_count):
            self.logical_mesh[i] = Sno.LogicalMesh(self._io, self, self._root)


    class BspSection(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
            self.is_leaf = self._io.read_u1()
            self.triangle_count = self._io.read_u2le()
            self.triangle_data = [None] * (self.triangle_count)
            for i in range(self.triangle_count):
                self.triangle_data[i] = self._io.read_u2le()

            self.children = self._io.read_u1()
            self.bsp_child = [None] * (self.children)
            for i in range(self.children):
                self.bsp_child[i] = Sno.BspSection(self._io, self, self._root)



    class Door(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = self._io.read_u4le()
            self.center = Sno.V3(self._io, self, self._root)
            self.x_axis = Sno.V3(self._io, self, self._root)
            self.y_axis = Sno.V3(self._io, self, self._root)
            self.z_axis = Sno.V3(self._io, self, self._root)
            self.vertex_count = self._io.read_u4le()
            self.vertex_array = [None] * (self.vertex_count)
            for i in range(self.vertex_count):
                self.vertex_array[i] = self._io.read_u4le()



    class Vertex(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.position = Sno.V3(self._io, self, self._root)
            self.normal = Sno.V3(self._io, self, self._root)
            self.color = Sno.Color(self._io, self, self._root)
            self.uvcoords = Sno.Tcoords(self._io, self, self._root)


    class Surface(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.texture = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self.start_corner = self._io.read_u4le()
            self.span_corner = self._io.read_u4le()
            self.vertex_count = self._io.read_u4le()
            self.face_array = [None] * (self.vertex_count // 3)
            for i in range(self.vertex_count // 3):
                self.face_array[i] = Sno.Face(self._io, self, self._root)



    class LogicalMesh(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u1()
            self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
            self.floor = KaitaiStream.resolve_enum(Sno.Floor, self._io.read_u4le())
            self.num_connections = self._io.read_u4le()
            if  ((self._root.version.major == 6) and (self._root.version.minor >= 4)) :
                self.connection_section_array_6_2 = [None] * (self.num_connections)
                for i in range(self.num_connections):
                    self.connection_section_array_6_2[i] = Sno.ConnectionSection62(self._io, self, self._root)


            if self._root.version.major == 7:
                self.connection_section_array_7 = [None] * (self.num_connections)
                for i in range(self.num_connections):
                    self.connection_section_array_7[i] = Sno.ConnectionSection7(self._io, self, self._root)


            self.num_nodal_connections = self._io.read_u4le()
            self.nodal_array = [None] * (self.num_nodal_connections)
            for i in range(self.num_nodal_connections):
                self.nodal_array[i] = Sno.NodalSection(self._io, self, self._root)

            self.triangle_section_count = self._io.read_u4le()
            self.triangle_section = [None] * (self.triangle_section_count)
            for i in range(self.triangle_section_count):
                self.triangle_section[i] = Sno.TriangleSection(self._io, self, self._root)

            self.bsp_tree = Sno.BspSection(self._io, self, self._root)


    class ConnectionSection7(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u2le()
            self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
            self.center = Sno.V3(self._io, self, self._root)
            self.triangle_count = self._io.read_u2le()
            self.trangle_array = [None] * (self.triangle_count)
            for i in range(self.triangle_count):
                self.trangle_array[i] = self._io.read_u2le()

            self.local_connection_count = self._io.read_u4le()
            self.local_connection_array = [None] * (self.local_connection_count)
            for i in range(self.local_connection_count):
                self.local_connection_array[i] = self._io.read_u2le()



    class TriangleSection(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.triangle = Sno.Triangle(self._io, self, self._root)
            self.normal = Sno.V3(self._io, self, self._root)


    class Color(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.r = self._io.read_u1()
            self.g = self._io.read_u1()
            self.b = self._io.read_u1()
            self.a = self._io.read_u1()


    class Triangle(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.a = Sno.V3(self._io, self, self._root)
            self.b = Sno.V3(self._io, self, self._root)
            self.c = Sno.V3(self._io, self, self._root)


    class Face(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.a = self._io.read_u2le()
            self.b = self._io.read_u2le()
            self.c = self._io.read_u2le()


    class Version(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.major = self._io.read_u4le()
            self.minor = self._io.read_u4le()


    class ConnectionSection62(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u2le()
            self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
            self.triangle_count = self._io.read_u2le()
            self.triangle_array = [None] * (self.triangle_count)
            for i in range(self.triangle_count):
                self.triangle_array[i] = self._io.read_u2le()

            self.local_connection_count = self._io.read_u4le()
            self.local_connection_array = [None] * (self.local_connection_count)
            for i in range(self.local_connection_count):
                self.local_connection_array[i] = self._io.read_u2le()



    class NodalSection(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.far_id = self._io.read_u1()
            self.nodal_leaf_connection_count = self._io.read_u4le()
            self.data = [None] * ((self.nodal_leaf_connection_count * 2))
            for i in range((self.nodal_leaf_connection_count * 2)):
                self.data[i] = self._io.read_u2le()



    class Spot(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x_axis = Sno.V3(self._io, self, self._root)
            self.y_axis = Sno.V3(self._io, self, self._root)
            self.z_axis = Sno.V3(self._io, self, self._root)
            self.center = Sno.V3(self._io, self, self._root)
            self.label = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")


    class Tcoords(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.u = self._io.read_f4le()
            self.v = self._io.read_f4le()


    class V3(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_f4le()
            self.y = self._io.read_f4le()
            self.z = self._io.read_f4le()


    class BoundingBox(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.min = Sno.V3(self._io, self, self._root)
            self.max = Sno.V3(self._io, self, self._root)



