import os
import sys

from bits.bits import Bits
from sno.sno_handler import SnoHandler


def print_sno(sno_path):
    sno = SnoHandler(sno_path)
    sno.print()


def main(argv):
    sno_path = argv[0]
    bits = Bits()
    base_path = bits.gas_dir.get_subdir(['art', 'terrain']).path
    print_sno(os.path.join(base_path, sno_path))


if __name__ == '__main__':
    main(sys.argv[1:])
