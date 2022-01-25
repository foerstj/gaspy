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
    def print_sno(cls, sno: Sno):
        print(f'magic: {sno.magic}')
        print(f'version: {sno.version.major}.{sno.version.minor}')
        print(f'door count: {sno.door_count}')
        print(f'spot count: {sno.spot_count}')
        print(f'corner count: {sno.corner_count}')
        print(f'face count: {sno.face_count}')
        print(f'texture count: {sno.texture_count}')
        print(f'bounding box: {cls.v3_str(sno.bounding_box.min)} - {cls.v3_str(sno.bounding_box.max)}')
        print(f'unk 1-7: {sno.unk1} {sno.unk2} {sno.unk3} {sno.unk4} {sno.unk5} {sno.unk6} {sno.unk7}')
        print(f'mystery section count: {sno.mystery_section_count}')
        print(f'checksum: {sno.checksum}')
        print(f'surfaces:')
        for surface in sno.surface_array:
            cls.print_surface(surface, '  ')

    def print(self):
        self.print_sno(self.sno)
