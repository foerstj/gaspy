# Script to generate the veteran & elite templates from the regular ones
import argparse
import os
import sys

from bits.bits import Bits


def copy_template_files(bits: Bits):
    templates_dir = bits.templates.gas_dir
    regular_dir = templates_dir.get_subdir('regular')
    for wl in ['veteran', 'elite']:
        wl_dir = templates_dir.get_or_create_subdir(wl)
        for subdir_path in ['actors', 'generators', ['interactive', 'containers']]:
            regular_subdir = regular_dir.get_subdir(subdir_path)
            assert os.path.exists(regular_subdir.path)
            wl_subdir = wl_dir.get_or_create_subdir(subdir_path)
            wl_subdir.save()  # create real dir if it doesn't exist
            sub_subdirs = ', '.join(wl_subdir.get_subdirs().keys())
            sub_files = ', '.join(wl_subdir.get_gas_files().keys())
            print(f'{wl} {subdir_path} - subdirs: {sub_subdirs} - files: {sub_files}')


def world_level_templates(bits_dir=None):
    bits = Bits(bits_dir)
    copy_template_files(bits)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world level templates')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    world_level_templates(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
