from bits.bits import Bits
from bits.templates import Template
from gas.gas import Section
from gas.molecules import PContentSelector
from printouts.common import get_wl_templates, none_empty
from printouts.csv import write_csv


WLS = ['regular', 'veteran', 'elite']
PCONTENT_CATEGORIES = {
    'spell': ['spell', 'cmagic', 'nmagic', 'combat_magic', 'nature_magic'],
    'armor': ['armor', 'body', 'gloves', 'boots', 'shield', 'helm'],
    'jewelry': ['amulet', 'ring'],
    'weapon': ['weapon', 'melee', 'ranged', 'axe', 'club', 'dagger', 'hammer', 'mace', 'staff', 'sword', 'bow', 'minigun'],
    'spellbook': ['spellbook'],
    '*': ['*'],
}


def get_pcontent_category(pcontent_type):
    for cat, types in PCONTENT_CATEGORIES.items():
        if pcontent_type in types:
            return cat
    if pcontent_type in ['spellbook']:
        return 'other'
    print(f'Warning: missing pcontent categorization for {pcontent_type}')
    return None


class PContentWls:
    def __init__(self, regular_template_name: str, pcontent_category: str, wl_powers: list[int]):
        self.regular_template_name = regular_template_name
        self.pcontent_category = pcontent_category
        self.wl_powers = wl_powers


def collect_data_from_template(regular_template_name: str, wl_templates: dict[str, Template]) -> list[PContentWls]:
    data: list[PContentWls] = list()
    wls_pcontent_sections = {
        wl: (template.section.find_sections_recursive('pcontent') + template.section.find_sections_recursive('store_pcontent')) if template is not None else list()
        for wl, template in wl_templates.items()
    }
    section_counts = [len(sections) for sections in wls_pcontent_sections.values()]
    if len(set(section_counts)) != 1:
        print('Warning: differing numbers of pcontent sections in ' + regular_template_name)
        return data
    for i in range(section_counts[0]):
        wl_pcontent_sections: list[Section] = [wls_pcontent_sections[wl][i] for wl in WLS]
        wls_il_main_attrs = [s.find_attrs_recursive('il_main') for s in wl_pcontent_sections]
        attr_counts = [len(attrs) for attrs in wls_il_main_attrs]
        if len(set(attr_counts)) != 1:
            print('Warning: differing numbers of pcontent il_main attrs in ' + regular_template_name)
            continue
        for j in range(attr_counts[0]):
            wl_il_main_attrs = [attrs[j] for attrs in wls_il_main_attrs]
            if any([not a.value.startswith('#') for a in wl_il_main_attrs]):
                continue
            wl_selector_strs = [attr.value.split()[0] for attr in wl_il_main_attrs]  # remove garbage behind missing semicolon
            wl_selectors = [PContentSelector.parse(pcs_str) for pcs_str in wl_selector_strs]
            wl_item_types = [pcs.item_type for pcs in wl_selectors]
            if len(set(wl_item_types)) != 1:
                print(f'Warning: different pcontent types in {regular_template_name}: {wl_item_types}')
                continue
            pc_cat = get_pcontent_category(wl_item_types[0])
            if pc_cat not in PCONTENT_CATEGORIES:
                continue  # unhandled pcontent category
            wl_powers = [pcs.power for pcs in wl_selectors]
            wl_range_segs = [list(p) if isinstance(p, tuple) else [p] for p in wl_powers]
            if len(set([len(segs) for segs in wl_range_segs])) != 1:
                print(f'Warning: different pcontent range defs in {regular_template_name}')
                continue
            for k in range(len(wl_range_segs[0])):
                wl_pcontent_powers = [r[k] for r in wl_range_segs]
                data.append(PContentWls(regular_template_name, pc_cat, wl_pcontent_powers))
    return data


def collect_world_level_pcontent_data(bits: Bits) -> list[PContentWls]:
    templates = bits.templates.get_actor_templates(False)
    templates.update(bits.templates.get_container_templates(False))
    wls_templates = get_wl_templates(templates)  # map from regular template name to regular, veteran & elite templates
    data: list[PContentWls] = list()
    for name, wl_templates in wls_templates.items():
        print(name)
        data.extend(collect_data_from_template(name, wl_templates))
    return data


def do_write_world_level_pcontent_csv(data: list[PContentWls]):
    csv = [['template'] + [f'{wl} {pc_cat}' for pc_cat in PCONTENT_CATEGORIES for wl in WLS]]
    for d in data:
        csv_line = [d.regular_template_name]
        for iter_pc_cat in PCONTENT_CATEGORIES:
            if iter_pc_cat == d.pcontent_category:
                csv_line.extend(d.wl_powers)
            else:
                csv_line.extend([None for _ in WLS])
        csv.append(none_empty(csv_line))
    write_csv('World-Level PContent', csv)


def write_world_level_pcontent_csv(bits: Bits):
    data = collect_world_level_pcontent_data(bits)
    do_write_world_level_pcontent_csv(data)
