# Script to generate the veteran & elite templates from the regular ones
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits
from gas.gas import Section
from gas.gas_dir import GasDir
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
                    wl_file_name = f'{wl_prefix.lower()}_{file_name}'
                    if file_name == 'dsx_generators.gas':
                        wl_file_name = f'{wl_prefix.lower()}_dsx_generator.gas'  # how could they
                    shutil.copy(os.path.join(regular_subdir.path, current_rel, file_name), os.path.join(wl_subdir.path, current_rel, wl_file_name))
            time.sleep(0.1)  # shutil...


def adapt_wl_template(section: Section, wl_prefix: str, file_name: str, static_template_names: list[str], prefix_doc=True, prefix_category=True):
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
        if specializes_attr.value.lower() not in static_template_names:
            specializes_attr.set_value(f'{wl_prefix}_{specializes_attr.value}')
    # child template name
    child_template_name_attrs = section.find_attrs_recursive('child_template_name')
    for child_template_name_attr in child_template_name_attrs:
        if child_template_name_attr.value.lower() not in static_template_names:
            child_template_name_attr.set_value(f'{wl_prefix}_{child_template_name_attr.value}')

    # doc & category_name
    if prefix_doc:
        doc_attrs = section.get_attrs('doc')
        for doc_attr in doc_attrs:
            doc = doc_attr.value.strip('"')
            if doc.lower().startswith('1w_'):
                doc = doc[3:]
            doc = f'"{wl_prefix}_{doc}"'
            doc_attr.set_value(doc)
    if prefix_category:
        category_attrs = section.get_attrs('category_name')
        for category_attr in category_attrs:
            category = category_attr.value.strip('"')
            if category.lower().startswith('1w_'):
                category = category[3:]
            category_prefix = wl_prefix if prefix_category != 'lower' else wl_prefix.lower()
            category = f'"{category_prefix}_{category}"'
            category_attr.set_value(category)

    # templates inside templates - looking at you, dsx_scorpion.gas!
    for subsection in section.get_sections():
        if subsection.has_t_n_header():
            adapt_wl_template(subsection, wl_prefix, file_name, static_template_names, prefix_doc, prefix_category)


def adapt_wl_template_file(gas_file: GasFile, wl: str, wl_prefix: str, static_template_names: list[str], prefix_doc: bool, prefix_category: bool):
    print(f'{wl} ({wl_prefix}): {gas_file.path}')
    for section in gas_file.get_gas().items:
        adapt_wl_template(section, wl_prefix, gas_file.path, static_template_names, prefix_doc, prefix_category)
    gas_file.save()


def lowers(strs: list[str]) -> list[str]:
    return [s.lower() for s in strs]


def do_adapt_wl_templates(wl_dir: GasDir, wl: str, wl_prefix: str, static_template_names: list[str], prefix_doc: bool, prefix_category: bool | str):
    for current_dir, subdirs, files in os.walk(wl_dir.path):
        for file_name in files:
            if not file_name.endswith('.gas'):
                continue
            adapt_wl_template_file(GasFile(os.path.join(current_dir, file_name)), wl, wl_prefix, static_template_names, prefix_doc, prefix_category)


def get_static_template_names(bits: Bits) -> dict[str, list[str]]:
    core_template_names = bits.templates.get_core_template_names()
    decorative_container_template_names = bits.templates.get_decorative_container_template_names()
    nonblocking_template_names = bits.templates.get_nonblocking_template_names()
    return {'core': lowers(core_template_names), 'decorative_containers': lowers(decorative_container_template_names), 'nonblocking': lowers(nonblocking_template_names)}


def adapt_wl_templates(bits: Bits):
    static_template_names = get_static_template_names(bits)
    templates_dir = bits.templates.gas_dir
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        wl_dir = templates_dir.get_subdir(wl)
        do_adapt_wl_templates(wl_dir.get_subdir('actors'), wl, wl_prefix, static_template_names['core'], True, True)
        do_adapt_wl_templates(wl_dir.get_subdir('generators'), wl, wl_prefix, static_template_names['core'] + static_template_names['nonblocking'] + ['base_breakable_wood'], False, 'lower')
        do_adapt_wl_templates(wl_dir.get_subdir(['interactive', 'containers']), wl, wl_prefix, static_template_names['core'] + static_template_names['decorative_containers'], True, False)


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
