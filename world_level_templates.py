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
from gas.molecules import PContentSelector
from printouts.world_level_pcontent import get_pcontent_category


def copy_template_files(bits: Bits, subdir: str = None):
    print('copy template files')
    templates_dir = bits.templates.gas_dir
    if subdir is not None:
        templates_dir = templates_dir.get_subdir(subdir)
    assert templates_dir is not None, 'templates dir not found'
    regular_dir = templates_dir.get_subdir('regular')
    assert regular_dir is not None, 'regular dir not found'
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        wl_dir = templates_dir.get_or_create_subdir(wl)
        for subdir_path in [['actors', 'ambient'], ['actors', 'evil'], ['actors', 'good', 'npc'], 'generators', ['interactive', 'containers']]:
            regular_subdir = regular_dir.get_subdir(subdir_path)
            assert regular_subdir is not None and os.path.exists(regular_subdir.path) or subdir is not None
            if regular_subdir is None or not os.path.exists(regular_subdir.path):
                continue
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


def adapt_wl_template_name(section: Section, wl_prefix: str):
    assert section.has_t_n_header()
    t, n = section.get_t_n_header()
    assert t == 'template'
    n = f'{wl_prefix}_{n}'
    section.set_t_n_header(t, n)


# Linear interpolation: y = m*x + c
# These values were interpolated from the original templates with help of stats.py
STATS_SCALES = {
    'experience_value': {
        'veteran': {'m': 2.771, 'c': 42530},
        'elite': {'m': 86.08, 'c': 1122000}
    },
    'defense': {
        'veteran': {'m': 1.265, 'c': 496},
        'elite': {'m': 1.509, 'c': 814.7}
    },
    'damage_min': {
        'veteran': {'m': 1.281, 'c': 142.2},
        'elite': {'m': 1.616, 'c': 235.5}
    },
    'damage_max': {
        'veteran': {'m': 1.405, 'c': 222.4},
        'elite': {'m': 1.716, 'c': 365.5}
    },
    'life': {
        'veteran': {'m': 1.154, 'c': 794.5},
        'elite': {'m': 1.307, 'c': 1336}
    },
    'max_life': {
        'veteran': {'m': 1.153, 'c': 817.4},
        'elite': {'m': 1.304, 'c': 1375}
    },
    'mana': {
        'veteran': {'m': 3.335, 'c': 104.5},
        'elite': {'m': 4.88, 'c': 186.7}
    },
    'max_mana': {
        'veteran': {'m': 3.335, 'c': 107},
        'elite': {'m': 4.88, 'c': 190.9}
    },
    'strength': {
        'veteran': {'m': 1.716, 'c': 7.6},
        'elite': {'m': 2.276, 'c': 11.71}
    },
    'dexterity': {
        'veteran': {'m': 1.565, 'c': 1.846},
        'elite': {'m': 1.997, 'c': 2.656}
    },
    'intelligence': {
        'veteran': {'m': 1.231, 'c': 0.773},
        'elite': {'m': 1.404, 'c': 1.215}
    },
    'melee': {
        'veteran': {'m': 0.844, 'c': 46.28},
        'elite': {'m': 0.848, 'c': 76.26}
    },
    'ranged': {
        'veteran': {'m': 0.876, 'c': 45.57},
        'elite': {'m': 0.924, 'c': 74.99}
    },
    'combat_magic': {
        'veteran': {'m': 0.919, 'c': 43.28},
        'elite': {'m': 0.995, 'c': 71.14}
    },
    'nature_magic': {
        'veteran': {'m': 1.002, 'c': 43.3},
        'elite': {'m': 1.034, 'c': 71.95}
    },
}
GOLD_SCALES = {
    'min': {
        'veteran': {'m': 4.38, 'c': 34480},
        'elite': {'m': 10.89, 'c': 155600}
    },
    'max': {
        'veteran': {'m': 2.134, 'c': 61520},
        'elite': {'m': 4.027, 'c': 256600}
    },
}
PCONTENT_POWER_SCALES = {
    'spell': {
        'veteran': {'m': 1.26, 'c': 28.71},
        'elite': {'m': 1.401, 'c': 46.86}
    },
    'armor': {
        'veteran': {'m': 1.483, 'c': 197.2},
        'elite': {'m': 1.766, 'c': 324.4}
    },
    'jewelry': {
        'veteran': {'m': 0.772, 'c': 106.3},
        'elite': {'m': 0.65, 'c': 171.4}
    },
    'weapon': {
        'veteran': {'m': 1.046, 'c': 115.4},
        'elite': {'m': 1.062, 'c': 188.4}
    },
    '*': {
        'veteran': {'m': 1.03, 'c': 114.5},
        'elite': {'m': 1.054, 'c': 186}
    },
}


def scale_value(value, scale):
    if not value:
        return value  # keep zero values
    m, c = scale['m'], scale['c']
    return m * value + c


POTION_MAPPING = {
    'veteran': {
        'small': 'medium',
        'medium': 'large',
        'large': 'super'
    },
    'elite': {
        'small': 'large',
        'medium': 'super',
        'large': 'super'
    }
}


def adapt_wl_template(section: Section, wl: str, wl_prefix: str, file_name: str, static_template_names: list[str], prefix_doc=True, prefix_category=True):
    if not section.has_t_n_header():
        # ignore rogue components after template accidentally closed with one too many brackets
        print(f'Warning: non-template section [{section.header}] in file {file_name}')
        return

    adapt_wl_template_name(section, wl_prefix)
    # templates inside templates - looking at you, dsx_scorpion.gas!
    for subsection in section.get_sections():
        if subsection.has_t_n_header():
            adapt_wl_template_name(subsection, wl_prefix)

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

    # stats
    for attr_name, attr_scales in STATS_SCALES.items():
        scale = attr_scales[wl]
        m, c = scale['m'], scale['c']
        for attr in section.find_attrs_recursive(attr_name):
            regular_value = attr.value
            suffix = None
            if ',' in regular_value:
                regular_value, suffix = regular_value.split(',', 1)
            regular_value = float(regular_value.split()[0])  # discard garbage after missing semicolon
            if regular_value:
                wl_value = m * regular_value + c
            else:
                wl_value = regular_value  # keep zero values, e.g. xp of summons
            wl_value = str(int(wl_value))
            if suffix is not None:
                wl_value += ',' + suffix
            attr.set_value(wl_value)

    # gold
    for gold_section in section.find_sections_recursive('gold*'):
        wl_min = wl_max = 0  # just so python doesn't complain about uninitialized vars
        min_attr = gold_section.get_attr('min')
        if min_attr is not None:
            regular_min = int(min_attr.value)
            wl_min = scale_value(regular_min, GOLD_SCALES['min'][wl])
        max_attr = gold_section.get_attr('max')
        if max_attr is not None:
            regular_max = int(max_attr.value)
            wl_max = scale_value(regular_max, GOLD_SCALES['max'][wl])
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
            assert potion_type in ['health', 'mana', 'rejuvenation'], potion_type
            assert potion_size in ['small', 'medium', 'large', 'super'], potion_size
            if potion_size in POTION_MAPPING[wl]:
                potion_size = POTION_MAPPING[wl][potion_size]
            attr.set_value('_'.join([potion_str, potion_type, potion_size]))

    # pcontent ranges
    for attr in section.find_attrs_recursive('il_main'):
        if attr.value.startswith('#'):
            pcs_str = attr.value.split()[0]  # discard garbage behind missing semicolon
            pcs = PContentSelector.parse(pcs_str)
            if pcs.power is None:
                continue
            pc_cat = get_pcontent_category(pcs.item_type)
            if pc_cat not in PCONTENT_POWER_SCALES:
                continue
            scale = PCONTENT_POWER_SCALES[pc_cat][wl]
            if isinstance(pcs.power, int):
                pcs.power = int(scale_value(pcs.power, scale))
            else:
                pcs.power = (int(scale_value(pcs.power[0], scale)), int(scale_value(pcs.power[1], scale)))
            attr.set_value(str(pcs))


def adapt_wl_template_file(gas_file: GasFile, wl: str, wl_prefix: str, static_template_names: list[str], prefix_doc: bool, prefix_category: bool):
    print(f'{wl} ({wl_prefix}): {gas_file.path}')
    for section in gas_file.get_gas().items:
        adapt_wl_template(section, wl, wl_prefix, gas_file.path, static_template_names, prefix_doc, prefix_category)
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


def adapt_wl_templates(bits: Bits, subdir: str = None):
    static_template_names = get_static_template_names(bits)
    templates_dir = bits.templates.gas_dir
    if subdir is not None:
        templates_dir = templates_dir.get_subdir(subdir)
    assert templates_dir is not None, 'templates dir not found'
    wls = {'veteran': '2W', 'elite': '3W'}
    for wl, wl_prefix in wls.items():
        print(f'adapt {wl} templates')
        wl_dir = templates_dir.get_subdir(wl)
        do_adapt_wl_templates(wl_dir.get_subdir('actors'), wl, wl_prefix, static_template_names['core'] + ['base_pm_fb', 'base_pm_fg', 'base_pm_dwarf', 'base_pm_giant'], True, True)
        do_adapt_wl_templates(wl_dir.get_subdir('generators'), wl, wl_prefix, static_template_names['core'] + static_template_names['nonblocking'] + ['base_breakable_wood'], False, 'lower')
        do_adapt_wl_templates(wl_dir.get_subdir(['interactive', 'containers']), wl, wl_prefix, static_template_names['core'] + static_template_names['decorative_containers'], True, False)


def world_level_templates(bits_dir=None, subdir=None):
    bits = Bits(bits_dir)
    copy_template_files(bits, subdir)
    adapt_wl_templates(bits, subdir)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy world level templates')
    parser.add_argument('--subdir', help='template subdir to process')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    world_level_templates(args.bits, args.subdir)


if __name__ == '__main__':
    main(sys.argv[1:])
