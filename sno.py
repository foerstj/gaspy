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
        self.corner_count = self._io.read_u4le()
        self.face_count = self._io.read_u4le()
        self.texture_count = self._io.read_u4le()
        self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
        self.unk1 = self._io.read_u4le()
        self.unk2 = self._io.read_u4le()
        self.unk3 = self._io.read_u4le()
        self.unk4 = self._io.read_u4le()
        self.unk5 = self._io.read_u4le()
        self.unk6 = self._io.read_u4le()
        self.unk7 = self._io.read_u4le()
        self.checksum = self._io.read_u4le()
        self.spot_array = [None] * (self.spot_count)
        for i in range(self.spot_count):
            self.spot_array[i] = Sno.Spot(self._io, self, self._root)

        self.door_array = [None] * (self.door_count)
        for i in range(self.door_count):
            self.door_array[i] = Sno.Door(self._io, self, self._root)

        self.corner_array = [None] * (self.corner_count)
        for i in range(self.corner_count):
            self.corner_array[i] = Sno.Corner(self._io, self, self._root)

        self.surface_array = [None] * (self.texture_count)
        for i in range(self.texture_count):
            self.surface_array[i] = Sno.Surface(self._io, self, self._root)

        self.mystery_section_count = self._io.read_u4le()
        self.mystery = [None] * (self.mystery_section_count)
        for i in range(self.mystery_section_count):
            self.mystery[i] = Sno.MysterySection(self._io, self, self._root)


    class Door(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u4le()
            self.x = self._io.read_f4le()
            self.y = self._io.read_f4le()
            self.z = self._io.read_f4le()
            self.r0 = self._io.read_f4le()
            self.r1 = self._io.read_f4le()
            self.r2 = self._io.read_f4le()
            self.r3 = self._io.read_f4le()
            self.r4 = self._io.read_f4le()
            self.r5 = self._io.read_f4le()
            self.r6 = self._io.read_f4le()
            self.r7 = self._io.read_f4le()
            self.r8 = self._io.read_f4le()
            self.hot_spot_count = self._io.read_u4le()
            self.hot_spot_array = [None] * (self.hot_spot_count)
            for i in range(self.hot_spot_count):
                self.hot_spot_array[i] = self._io.read_u4le()



    class ShortPairSection(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.unk = self._io.read_u1()
            self.count = self._io.read_u4le()
            self.data = [None] * ((self.count * 2))
            for i in range((self.count * 2)):
                self.data[i] = self._io.read_u2le()



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
            self.corner_count = self._io.read_u4le()
            self.face_array = [None] * (self.corner_count // 3)
            for i in range(self.corner_count // 3):
                self.face_array[i] = Sno.Face(self._io, self, self._root)



    class CrazySection62(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u2le()
            self.r0 = self._io.read_f4le()
            self.r1 = self._io.read_f4le()
            self.r2 = self._io.read_f4le()
            self.r3 = self._io.read_f4le()
            self.r4 = self._io.read_f4le()
            self.r5 = self._io.read_f4le()
            self.count1 = self._io.read_u2le()
            self.short_array_1 = [None] * (self.count1)
            for i in range(self.count1):
                self.short_array_1[i] = self._io.read_u2le()

            self.count2 = self._io.read_u4le()
            self.short_array_2 = [None] * (self.count2)
            for i in range(self.count2):
                self.short_array_2[i] = self._io.read_u2le()



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


    class MysterySection(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u1()
            self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
            self.floor = KaitaiStream.resolve_enum(Sno.Floor, self._io.read_u4le())
            self.crazy_section_count = self._io.read_u4le()
            if  ((self._root.version.major == 6) and (self._root.version.minor == 2)) :
                self.crazy_section_array_6_2 = [None] * (self.crazy_section_count)
                for i in range(self.crazy_section_count):
                    self.crazy_section_array_6_2[i] = Sno.CrazySection62(self._io, self, self._root)


            if self._root.version.major == 7:
                self.crazy_section_array_7 = [None] * (self.crazy_section_count)
                for i in range(self.crazy_section_count):
                    self.crazy_section_array_7[i] = Sno.CrazySection7(self._io, self, self._root)


            self.short_pair_section_count = self._io.read_u4le()
            self.short_pair_section_array = [None] * (self.short_pair_section_count)
            for i in range(self.short_pair_section_count):
                self.short_pair_section_array[i] = Sno.ShortPairSection(self._io, self, self._root)

            self.triangle_section_count = self._io.read_u4le()
            self.triangle_section = [None] * (self.triangle_section_count)
            for i in range(self.triangle_section_count):
                self.triangle_section[i] = Sno.TriangleSection(self._io, self, self._root)

            self.wtf = Sno.WtfSection(self._io, self, self._root)


    class Corner(KaitaiStruct):
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


    class Spot(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.r0 = self._io.read_f4le()
            self.r1 = self._io.read_f4le()
            self.r2 = self._io.read_f4le()
            self.r3 = self._io.read_f4le()
            self.r4 = self._io.read_f4le()
            self.r5 = self._io.read_f4le()
            self.r6 = self._io.read_f4le()
            self.r7 = self._io.read_f4le()
            self.r8 = self._io.read_f4le()
            self.x = self._io.read_f4le()
            self.y = self._io.read_f4le()
            self.z = self._io.read_f4le()
            self.iunno = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")


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


    class WtfSection(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.bounding_box = Sno.BoundingBox(self._io, self, self._root)
            self.unk = self._io.read_u1()
            self.count = self._io.read_u2le()
            self.data = [None] * (self.count)
            for i in range(self.count):
                self.data[i] = self._io.read_u2le()

            self.ind = self._io.read_u1()
            self.moar = [None] * (self.ind)
            for i in range(self.ind):
                self.moar[i] = Sno.WtfSection(self._io, self, self._root)



    class CrazySection7(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u2le()
            self.r0 = self._io.read_f4le()
            self.r1 = self._io.read_f4le()
            self.r2 = self._io.read_f4le()
            self.r3 = self._io.read_f4le()
            self.r4 = self._io.read_f4le()
            self.r5 = self._io.read_f4le()
            self.r6 = self._io.read_f4le()
            self.r7 = self._io.read_f4le()
            self.r8 = self._io.read_f4le()
            self.count1 = self._io.read_u2le()
            self.short_array_1 = [None] * (self.count1)
            for i in range(self.count1):
                self.short_array_1[i] = self._io.read_u2le()

            self.count2 = self._io.read_u4le()
            self.short_array_2 = [None] * (self.count2)
            for i in range(self.count2):
                self.short_array_2[i] = self._io.read_u2le()



