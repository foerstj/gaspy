import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits


def install_minibits_templates(bits: Bits, minibits_single_path: str):
    minibits_name = os.path.basename(os.path.dirname(minibits_single_path))
    src_templates_path = os.path.join(minibits_single_path, 'world', 'contentdb', 'templates')
    if not os.path.exists(src_templates_path):
        return
    dst_templates_path = os.path.join(bits.gas_dir.path, 'world', 'contentdb', 'templates', 'minibits', minibits_name)
    shutil.copytree(src_templates_path, dst_templates_path)
    time.sleep(0.1)  # shutil...


def install_minibits_single(bits: Bits, minibits_path: str, minibits_single: str):
    print(minibits_single)
    minibits_single_path = os.path.join(minibits_path, minibits_single, 'Bits')
    assert os.path.exists(minibits_single_path)
    install_minibits_templates(bits, minibits_single_path)


def install_minibits_list(bits: Bits, minibits_path: str, minibits_list: list[str]):
    for minibits_single in minibits_list:
        install_minibits_single(bits, minibits_path, minibits_single)


def install_minibits(bits_path: str, minibits_path: str):
    print('Here we go!')
    assert os.path.exists(minibits_path)
    bits = Bits(bits_path)
    minibits_txt_path = os.path.join(bits.gas_dir.path, 'minibits.txt')
    assert os.path.exists(minibits_txt_path)
    with open(minibits_txt_path, 'r') as minibits_txt:
        minibits_list = minibits_txt.readlines()
    minibits_list = [x.strip() for x in minibits_list]
    install_minibits_list(bits, minibits_path, minibits_list)
    print('That\'s it folks!')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy install_minibits')
    parser.add_argument('--bits', default='DSLOA')
    parser.add_argument('--minibits', required=True)
    return parser


def parse_args(argv: list[str]):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv: list[str]):
    args = parse_args(argv)
    install_minibits(args.bits, args.minibits)


if __name__ == '__main__':
    main(sys.argv[1:])
