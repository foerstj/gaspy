from sno.sno import Sno


class SnoHandler:
    def __init__(self, sno_path):
        self.sno = Sno.from_file(sno_path)

    @classmethod
    def v3_str(cls, v3: Sno.V3):
        return f'({v3.x} | {v3.y} | {v3.z})'

    @classmethod
    def print_surface(cls, surface: Sno.Surface, indent=''):
        print(f'{indent}texture: {surface.texture}')

    @classmethod
    def print_sno(cls, sno: Sno, indent='', redundant=False, basic=True, surfaces=False):
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
            print(f'{indent}bounding box: {cls.v3_str(sno.bounding_box.min)} - {cls.v3_str(sno.bounding_box.max)}')
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

    def print(self, indent='', redundant=False, basic=True, surfaces=False):
        self.print_sno(self.sno, indent, redundant, basic, surfaces)
