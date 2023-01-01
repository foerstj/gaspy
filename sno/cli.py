import os
import sys

from bits.bits import Bits
from sno.sno_handler import SnoHandler


def print_sno(sno_path):
    sno = SnoHandler(sno_path)
    sno.print('', False, False, True)


def main(argv):
    sno_path = argv[0]
    bits_path = argv[1] if len(argv) > 1 else None
    bits = Bits(bits_path)
    assert bits.snos, 'Bits contains no SNOs'
    base_path = bits.snos.path
    print_sno(os.path.join(base_path, sno_path))


if __name__ == '__main__':
    main(sys.argv[1:])
