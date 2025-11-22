# Script to generate the veteran & elite templates from the regular ones
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

from bits.bits import Bits
from bits.templates import Templates
from gas.gas import Section, Attribute
from gas.gas_dir import GasDir
from gas.gas_file import GasFile
from gas.molecules import PContentSelector
from printouts.world_level_pcontent import get_pcontent_category
from world_levels.wl_scaler import WLScaler


class WlGenOpts:
    def __init__(self, prefix_doc: bool, prefix_category: bool | str):
        self.prefix_doc = prefix_doc
        self.prefix_category = prefix_category


TEMPLATE_SUBS = {
    'actors/ambient': WlGenOpts(True, True),
    'actors/evil': WlGenOpts(True, True),
    'actors/good/npc': WlGenOpts(True, True),
    'generators': WlGenOpts(False, 'lower'),
    'interactive/containers': WlGenOpts(True, False)
}


def copy_template_files(bits: Bits, template_base: str = None, no_wl_filename=False):
    print('copy template files')
    templates_dir = bits.templates.gas_dir
    if template_base is not None:
        templates_dir = templates_dir.get_subdir(template_base.split('/'))
    assert templates_dir is not None, 'templates dir not found'
    regular_dir = templates_dir.get_subdir('regular')
    assert regular_dir is not None, 'regular dir not found'
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        wl_dir = templates_dir.get_or_create_subdir(wl)
        wl_dir.save()  # create veteran/elite dir if it doesn't exist
        for template_sub in TEMPLATE_SUBS:
            subdir_path = template_sub.split('/')
            regular_subdir = regular_dir.get_subdir(subdir_path)
            assert regular_subdir is not None and os.path.exists(regular_subdir.path) or template_base is not None
            if regular_subdir is None or not os.path.exists(regular_subdir.path):
                continue
            wl_subdir = wl_dir.get_or_create_subdir(subdir_path)
            os.makedirs(wl_subdir.path, exist_ok=True)  # create real dir if it doesn't exist
            print(f'{wl} {os.path.join(*subdir_path)}')
            for current_dir, subdirs, files in os.walk(regular_subdir.path):
                current_rel = str(os.path.relpath(current_dir, regular_subdir.path))
                for file_name in files:
                    if not file_name.endswith('.gas'):
                        continue
                    if no_wl_filename:
                        wl_file_name = file_name
                    else:
                        wl_file_name = f'{wl_prefix.lower()}_{file_name}'
                        if file_name == 'dsx_generators.gas':
                            wl_file_name = f'{wl_prefix.lower()}_dsx_generator.gas'  # how could they
                    os.makedirs(os.path.join(wl_subdir.path, current_rel), exist_ok=True)
                    src = str(os.path.join(regular_subdir.path, current_rel, file_name))
                    dst = str(os.path.join(wl_subdir.path, current_rel, wl_file_name))
                    shutil.copy(src, dst)
            time.sleep(0.1)  # shutil...


def adapt_wl_template_name(section: Section, wl_prefix: str):
    assert section.has_t_n_header()
    t, n = section.get_t_n_header()
    assert t == 'template'
    n = f'{wl_prefix}_{n}'
    section.set_t_n_header(t, n)


STAT_ATTRS = [
    'aspect:experience_value',
    'defend:defense', 'attack:damage_min', 'attack:damage_max',
    'aspect:life', 'aspect:max_life', 'aspect:mana', 'aspect:max_mana',
    'actor:skills:strength', 'actor:skills:dexterity', 'actor:skills:intelligence',
    'actor:skills:melee', 'actor:skills:ranged', 'actor:skills:combat_magic', 'actor:skills:nature_magic'
]
PCONTENT_CATS = ['spell', 'armor', 'jewelry', 'weapon', 'spellbook', '*']


WL_SCALERS = {
    'veteran': WLScaler('veteran'),
    'elite': WLScaler('elite'),
}


def scale_wl_stat_attr(attr: Attribute, wl_scaler: WLScaler):
    regular_value = attr.value
    suffix = None
    if isinstance(regular_value, str):
        if ',' in regular_value:
            regular_value, suffix = regular_value.split(',', 1)
        regular_value = float(regular_value.split()[0])  # discard garbage after missing semicolon
    wl_value = wl_scaler.scale_stat(attr.name.lower(), regular_value)
    wl_value = str(int(wl_value))
    if suffix is not None:
        wl_value += ',' + suffix
    attr.set_value(wl_value)


def find_attrs_by_path(section: Section, *attr_path: str) -> list[Attribute]:
    sub_name = attr_path[0]
    if len(attr_path) == 1:
        return section.get_attrs(sub_name)
    attrs = list()
    sub_sections = section.get_sections(sub_name)
    for s in sub_sections:
        attrs.extend(find_attrs_by_path(s, *attr_path[1:]))  # recurse
    return attrs


def scale_wl_stats(section: Section, wl_scaler: WLScaler):
    for attr_path_str in STAT_ATTRS:
        attr_path = attr_path_str.split(':')
        for attr in find_attrs_by_path(section, *attr_path):
            scale_wl_stat_attr(attr, wl_scaler)


def scale_wl_inventories(section: Section, wl_scaler: WLScaler):
    # gold
    for gold_section in section.find_sections_recursive('gold*'):
        wl_min = wl_max = 0  # just so python doesn't complain about uninitialized vars
        min_attr = gold_section.get_attr('min')
        if min_attr is not None:
            regular_min = int(min_attr.value)
            wl_min = wl_scaler.scale_gold('min', regular_min)
        max_attr = gold_section.get_attr('max')
        if max_attr is not None:
            regular_max = int(max_attr.value)
            wl_max = wl_scaler.scale_gold('max', regular_max)
        if min_attr is not None and max_attr is not None:
            if wl_min > wl_max:
                temp = wl_max
                wl_max = wl_min
                wl_min = temp
        if min_attr is not None:
            min_attr.set_value(str(int(wl_min)))
        if max_attr is not None:
            max_attr.set_value(str(int(wl_max)))

    # potions
    for attr in section.find_attrs_recursive('il_main'):
        if attr.value.startswith('potion_'):
            potion_str, potion_type, potion_size = attr.value.split('_')
            assert potion_str == 'potion'
            assert potion_type in ['health', 'mana', 'rejuvenation'], potion_type
            assert potion_size in ['small', 'medium', 'large', 'super'], potion_size
            potion_size = wl_scaler.scale_potion(potion_size)
            attr.set_value('_'.join([potion_str, potion_type, potion_size]))

    # pcontent ranges
    for attr in section.find_attrs_recursive('il_main'):
        if attr.value.startswith('#'):
            pcs_str = attr.value.split()[0]  # discard garbage behind missing semicolon
            pcs = PContentSelector.parse(pcs_str)
            if pcs.power is None:
                continue
            pc_cat = get_pcontent_category(pcs.item_type)
            if pc_cat not in PCONTENT_CATS:
                continue
            if isinstance(pcs.power, int):
                pcs.power = int(wl_scaler.scale_pcontent_power(pc_cat, pcs.power))
            else:
                pcs.power = (int(wl_scaler.scale_pcontent_power(pc_cat, pcs.power[0])), int(wl_scaler.scale_pcontent_power(pc_cat, pcs.power[1])))
            attr.set_value(str(pcs))


def adapt_wl_template_names_rec(section: Section, wl_prefix: str):
    if section.has_t_n_header('template'):
        adapt_wl_template_name(section, wl_prefix)
    # templates inside templates - looking at you, dsx_scorpion.gas!
    for subsection in section.get_sections():
        adapt_wl_template_names_rec(subsection, wl_prefix)  # recurse


def adapt_wl_template_section(section: Section, wl: str, wl_prefix: str, static_template_names: list[str], prefix_doc=True, prefix_category=True):
    # template name
    adapt_wl_template_names_rec(section, wl_prefix)

    # base template name
    specializes_attrs = section.find_attrs_recursive('specializes')
    for specializes_attr in specializes_attrs:
        base_template_name = specializes_attr.value.strip('"')
        if base_template_name.lower() not in static_template_names:
            specializes_attr.set_value(f'{wl_prefix}_{base_template_name}')
    # child template name
    child_template_name_attrs = section.find_attrs_recursive('child_template_name')
    for child_template_name_attr in child_template_name_attrs:
        if child_template_name_attr.value.lower() not in static_template_names:
            child_template_name_attr.set_value(f'{wl_prefix}_{child_template_name_attr.value}')

    # doc & category_name
    if prefix_doc:
        doc_attrs = section.find_attrs_recursive('doc')
        for doc_attr in doc_attrs:
            doc = doc_attr.value.strip('"')
            if doc.lower().startswith('1w_'):
                doc = doc[3:]
            doc = f'"{wl_prefix}_{doc}"'
            doc_attr.set_value(doc)
    if prefix_category:
        category_attrs = section.find_attrs_recursive('category_name')
        for category_attr in category_attrs:
            category = category_attr.value.strip('"')
            if category == 'emitter':
                continue  # these don't have sub-folders in SE and the templates would vanish from view
            if category.lower().startswith('1w_'):
                category = category[3:]
            category_prefix = wl_prefix if prefix_category != 'lower' else wl_prefix.lower()
            category = f'"{category_prefix}_{category}"'
            category_attr.set_value(category)

    # scale up inventories
    scale_wl_inventories(section, WL_SCALERS[wl])


def adapt_wl_template_file(gas_file: GasFile, wl: str, wl_prefix: str, static_template_names: list[str], prefix_doc: bool, prefix_category: bool | str):
    print(f'{wl} ({wl_prefix}): {gas_file.path}')

    # first pass, iterating dumbly over gas sections
    for section in gas_file.get_gas().items:
        adapt_wl_template_section(section, wl, wl_prefix, static_template_names, prefix_doc, prefix_category)

    # second pass, with template intelligence
    wl_templates = Templates.do_load_templates_gas(gas_file.get_gas())  # list of templates, not connected
    for wl_template in wl_templates:
        scale_wl_stats(wl_template.section, WL_SCALERS[wl])

    gas_file.save()


def lowers(strs: list[str]) -> list[str]:
    return [s.lower() for s in strs]


def do_adapt_wl_templates(wl_dir: GasDir, wl: str, wl_prefix: str, static_template_names: list[str], prefix_doc: bool, prefix_category: bool | str):
    if wl_dir is None:
        return
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


def get_all_static_template_names(bits: Bits) -> list[str]:
    names_dict = get_static_template_names(bits)
    names_list = list()
    for names in names_dict.values():
        names_list.extend(names)
    names_list.extend(['base_pm_fb', 'base_pm_fg', 'base_pm_dwarf', 'base_pm_giant'])  # actors
    names_list.extend(['base_breakable_wood'])  # generators
    return names_list


def adapt_wl_templates(bits: Bits, template_base: str = None):
    static_template_names = get_all_static_template_names(bits)
    templates_dir = bits.templates.gas_dir
    if template_base is not None:
        templates_dir = templates_dir.get_subdir(template_base.split('/'))
    assert templates_dir is not None, 'templates dir not found'
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        print(f'adapt {wl} templates')
        wl_dir = templates_dir.get_subdir(wl)
        for template_sub, wl_gen_opts in TEMPLATE_SUBS.items():
            subdir_path = template_sub.split('/')
            do_adapt_wl_templates(wl_dir.get_subdir(subdir_path), wl, wl_prefix, static_template_names, wl_gen_opts.prefix_doc, wl_gen_opts.prefix_category)


def world_level_templates(bits_dir=None, template_base=None, no_wl_filename=False):
    bits = Bits(bits_dir)
    copy_template_files(bits, template_base, no_wl_filename)
    adapt_wl_templates(bits, template_base)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world level templates')
    parser.add_argument('--template-base', help='template base subdir where regular, veteran & elite folders are')
    parser.add_argument('--no-wl-filename', action='store_true')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    world_level_templates(args.bits, args.template_base, args.no_wl_filename)


if __name__ == '__main__':
    main(sys.argv[1:])
