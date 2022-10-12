# Script to generate the veteran & elite templates from the regular ones
import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits


def copy_template_files(bits: Bits):
    templates_dir = bits.templates.gas_dir
    regular_dir = templates_dir.get_subdir('regular')
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        wl_dir = templates_dir.get_or_create_subdir(wl)
        for subdir_path in ['actors', 'generators', ['interactive', 'containers']]:
            regular_subdir = regular_dir.get_subdir(subdir_path)
            assert os.path.exists(regular_subdir.path)
            wl_subdir = wl_dir.get_or_create_subdir(subdir_path)
            wl_subdir.save()  # create real dir if it doesn't exist
            print(f'{wl} {subdir_path if isinstance(subdir_path, str) else os.path.join(*subdir_path)}')
            for current_dir, subdirs, files in os.walk(regular_subdir.path):
                current_rel = os.path.relpath(current_dir, regular_subdir.path)
                for file_name in files:
                    if not file_name.endswith('.gas'):
                        continue
                    shutil.copy(os.path.join(regular_subdir.path, current_rel, file_name), os.path.join(wl_subdir.path, current_rel, f'{wl_prefix.lower()}_{file_name}'))
            time.sleep(0.1)  # shutil...


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
