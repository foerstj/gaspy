# Script to generate the veteran & elite templates from the regular ones
import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits
from gas.gas import Section
from gas.gas_file import GasFile


def copy_template_files(bits: Bits):
    templates_dir = bits.templates.gas_dir
    regular_dir = templates_dir.get_subdir('regular')
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        wl_dir = templates_dir.get_or_create_subdir(wl)
        for subdir_path in [['actors', 'ambient'], ['actors', 'evil'], ['actors', 'good', 'npc'], 'generators', ['interactive', 'containers']]:
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


def adapt_wl_template(section: Section, wl_prefix: str, file_name: str):
    if not section.has_t_n_header():
        # ignore rogue components after template accidentally closed with one too many brackets
        print(f'Warning: non-template section [{section.header}] in file {file_name}')
        return

    # template name in header
    t, n = section.get_t_n_header()
    assert t == 'template'
    n = f'{wl_prefix}_{n}'
    section.set_t_n_header(t, n)

    # base template name
    specializes_attr = section.get_attr('specializes')
    if specializes_attr is not None:
        specializes_attr.set_value(f'{wl_prefix}_{specializes_attr.value}')

    # doc & category
    doc_attrs = section.get_attrs('doc')
    for doc_attr in doc_attrs:
        doc = doc_attr.value.strip('"')
        if doc.lower().startswith('1w_'):
            doc = doc[3:]
        doc = f'"{wl_prefix}_{doc}"'
        doc_attr.set_value(doc)
    category_attrs = section.get_attrs('category_name')
    for category_attr in category_attrs:
        category = category_attr.value.strip('"')
        if category.lower().startswith('1w_'):
            category = category[3:]
        category = f'"{wl_prefix}_{category}"'
        category_attr.set_value(category)


def adapt_wl_template_file(gas_file: GasFile, wl: str, wl_prefix: str):
    print(f'{wl} ({wl_prefix}): {gas_file.path}')
    for section in gas_file.get_gas().items:
        adapt_wl_template(section, wl_prefix, gas_file.path)
    gas_file.save()


def adapt_wl_templates(bits: Bits):
    templates_dir = bits.templates.gas_dir
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        wl_dir = templates_dir.get_subdir(wl)
        for current_dir, subdirs, files in os.walk(wl_dir.path):
            for file_name in files:
                if not file_name.endswith('.gas'):
                    continue
                adapt_wl_template_file(GasFile(os.path.join(current_dir, file_name)), wl, wl_prefix)


def world_level_templates(bits_dir=None):
    bits = Bits(bits_dir)
    copy_template_files(bits)
    adapt_wl_templates(bits)


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
