import os
import sys

from bits.bits import Bits
from sno.sno import Sno


def v3_str(v3: Sno.V3):
    return f'({v3.x} | {v3.y} | {v3.z})'


def print_surface(surface: Sno.Surface, indent=''):
    print(f'{indent}texture: {surface.texture}')


def print_sno(sno_path):
    sno = Sno.from_file(sno_path)
    print(f'magic: {sno.magic}')
    print(f'version: {sno.version.major}.{sno.version.minor}')
    print(f'door count: {sno.door_count}')
    print(f'spot count: {sno.spot_count}')
    print(f'corner count: {sno.corner_count}')
    print(f'face count: {sno.face_count}')
    print(f'texture count: {sno.texture_count}')
    print(f'bounding box: {v3_str(sno.bounding_box.min)} - {v3_str(sno.bounding_box.max)}')
    print(f'unk 1-7: {sno.unk1} {sno.unk2} {sno.unk3} {sno.unk4} {sno.unk5} {sno.unk6} {sno.unk7}')
    print(f'mystery section count: {sno.mystery_section_count}')
    print(f'checksum: {sno.checksum}')
    print(f'surfaces:')
    for surface in sno.surface_array:
        print_surface(surface, '  ')


def main(argv):
    sno_path = argv[0]
    bits = Bits()
    base_path = bits.gas_dir.get_subdir(['art', 'terrain']).path
    print_sno(os.path.join(base_path, sno_path))


if __name__ == '__main__':
    main(sys.argv[1:])
