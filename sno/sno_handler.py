from sno.geometry import is_point_inside_triangle_2d, snap_point_to_plane
from sno.sno import Sno


class SnoHandler:
    def __init__(self, sno_path):
        self.sno = Sno.from_file(sno_path)

    @classmethod
    def v3_str(cls, v3: Sno.V3):
        return f'({v3.x} | {v3.y} | {v3.z})'

    @classmethod
    def bb_str(cls, bounding_box: Sno.BoundingBox):
        return f'[{cls.v3_str(bounding_box.min)} - {cls.v3_str(bounding_box.max)}]'

    @classmethod
    def print_surface(cls, surface: Sno.Surface, indent=''):
        print(f'{indent}texture: {surface.texture}')

    @classmethod
    def print_logical_mesh(cls, logical_mesh: Sno.LogicalMesh, indent=''):
        print(f'{indent}- index: {logical_mesh.index}')
        print(f'{indent}  floor: {logical_mesh.floor}')
        print(f'{indent}  triangle_section_count: {logical_mesh.triangle_section_count}')
        for triangle_section in logical_mesh.triangle_section:
            print(f'{indent}  - {cls.v3_str(triangle_section.triangle.a)}, {cls.v3_str(triangle_section.triangle.b)}, {cls.v3_str(triangle_section.triangle.c)}')

    @classmethod
    def print_sno(cls, sno: Sno, indent='', redundant=False, basic=True, surfaces=False, logical_mesh=False):
        # printing fields in the order defined in the KSY
        if redundant:
            print(f'{indent}magic: {sno.magic}')
        if basic:
            print(f'{indent}version: {sno.version.major}.{sno.version.minor}')
            print(f'{indent}door count: {sno.door_count}')
            print(f'{indent}spot count: {sno.spot_count}')
            print(f'{indent}vertex count: {sno.vertex_count}')
            print(f'{indent}triangle count: {sno.triangle_count}')
            print(f'{indent}texture count: {sno.texture_count}')
            print(f'{indent}bounding box: {cls.bb_str(sno.bounding_box)}')
            print(f'{indent}centroid offset: {cls.v3_str(sno.centroid_offset)}')
            print(f'{indent}tile: {sno.tile}')
        if redundant:
            print(f'{indent}reserved 0-2: {sno.reserved0} {sno.reserved1} {sno.reserved2}')
            print(f'{indent}checksum: {sno.checksum}')
        if surfaces:
            print(f'{indent}surfaces:')
            for surface in sno.surface_array:
                cls.print_surface(surface, indent + '  ')
        if basic:
            print(f'{indent}logical mesh count: {sno.logical_mesh_count}')
        if logical_mesh:
            print(f'{indent}logical mesh:')
            for lm in sno.logical_mesh:
                cls.print_logical_mesh(lm, indent + '  ')

    def print(self, indent='', redundant=False, basic=True, surfaces=False, logical_mesh=False):
        self.print_sno(self.sno, indent, redundant, basic, surfaces, logical_mesh)

    @classmethod
    def _is_in_bounding_box(cls, x: float, y: float, z: float, box: Sno.BoundingBox):
        return box.min.x <= x <= box.max.x and\
               box.min.y <= y <= box.max.y and\
               box.min.z <= z <= box.max.z

    def is_in_bounding_box(self, x: float, y: float, z: float):
        return self._is_in_bounding_box(x, y, z, self.sno.bounding_box)

    @classmethod
    def _is_in_bounding_box_2d(cls, x: float, z: float, box: Sno.BoundingBox):
        return box.min.x <= x <= box.max.x and\
               box.min.z <= z <= box.max.z

    def is_in_bounding_box_2d(self, x: float, z: float):
        return self._is_in_bounding_box_2d(x, z, self.sno.bounding_box)

    @classmethod
    def _is_in_triangle_2d(cls, x: float, z: float, triangle: Sno.Triangle):
        return is_point_inside_triangle_2d(triangle.a.x, triangle.a.z, triangle.b.x, triangle.b.z, triangle.c.x, triangle.c.z, x, z)

    @classmethod
    def _find_triangle_2d(cls, x: float, z: float, mesh: Sno.LogicalMesh):
        if not cls._is_in_bounding_box_2d(x, z, mesh.bounding_box):
            return None
        for triangle in mesh.triangle_section:
            if cls._is_in_triangle_2d(x, z, triangle.triangle):
                return triangle
        return None

    @classmethod
    def _is_in_mesh_2d(cls, x: float, z: float, mesh: Sno.LogicalMesh):
        return cls._find_triangle_2d(x, z, mesh) is not None

    def is_in_floor_2d(self, x: float, z: float):
        if not self.is_in_bounding_box_2d(x, z):
            return False
        for mesh in self.sno.logical_mesh:
            if mesh.floor != Sno.Floor.floor:
                continue
            if self._is_in_mesh_2d(x, z, mesh):
                return True
        return False

    @classmethod
    def _snap_to_triangle(cls, x: float, z: float, triangle: Sno.Triangle, normal: Sno.V3) -> float:
        return snap_point_to_plane(triangle.a.x, triangle.a.y, triangle.a.z, normal.x, normal.y, normal.z, x, z)

    def snap_to_ground(self, x: float, z: float):
        triangle = None
        for mesh in self.sno.logical_mesh:
            if mesh.floor != Sno.Floor.floor:
                continue
            t = self._find_triangle_2d(x, z, mesh)
            if t is not None:
                triangle = t
                break
        assert isinstance(triangle, Sno.TriangleSection)

        return self._snap_to_triangle(x, z, triangle.triangle, triangle.normal)
