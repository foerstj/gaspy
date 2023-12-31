from bits.bits import Bits
from gas.gas import Section
from gas.molecules import PContentSelector
from printouts.common import get_wl_templates, none_empty
from printouts.csv import write_csv

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


def write_world_level_pcontent_csv(bits: Bits):
    templates = bits.templates.get_actor_templates(False)
    templates.update(bits.templates.get_container_templates(False))
    wls_templates = get_wl_templates(templates)
    wls = ['regular', 'veteran', 'elite']
    csv = [['template'] + [f'{wl} {pc_cat}' for pc_cat in PCONTENT_CATEGORIES for wl in wls]]
    for name, wl_templates in wls_templates.items():
        print(name)
        wls_pcontent_sections = {
            wl: (template.section.find_sections_recursive('pcontent') + template.section.find_sections_recursive('store_pcontent')) if template is not None else list()
            for wl, template in wl_templates.items()
        }
        section_counts = [len(sections) for sections in wls_pcontent_sections.values()]
        if len(set(section_counts)) != 1:
            print('Warning: differing numbers of pcontent sections in ' + name)
            continue
        for i in range(section_counts[0]):
            wl_pcontent_sections: list[Section] = [wls_pcontent_sections[wl][i] for wl in wls]
            wls_il_main_attrs = [s.find_attrs_recursive('il_main') for s in wl_pcontent_sections]
            attr_counts = [len(attrs) for attrs in wls_il_main_attrs]
            if len(set(attr_counts)) != 1:
                print('Warning: differing numbers of pcontent il_main attrs in ' + name)
                continue
            for j in range(attr_counts[0]):
                wl_il_main_attrs = [attrs[j] for attrs in wls_il_main_attrs]
                if any([not a.value.startswith('#') for a in wl_il_main_attrs]):
                    continue
                wl_selector_strs = [attr.value.split()[0] for attr in wl_il_main_attrs]  # remove garbage behind missing semicolon
                wl_selectors = [PContentSelector.parse(pcs_str) for pcs_str in wl_selector_strs]
                wl_item_types = [pcs.item_type for pcs in wl_selectors]
                if len(set(wl_item_types)) != 1:
                    print(f'Warning: different pcontent types in {name}: {wl_item_types}')
                    continue
                pc_cat = get_pcontent_category(wl_item_types[0])
                if pc_cat not in PCONTENT_CATEGORIES:
                    continue  # unhandled pcontent category
                wl_powers = [pcs.power for pcs in wl_selectors]
                wl_range_segs = [list(p) if isinstance(p, tuple) else [p] for p in wl_powers]
                if len(set([len(segs) for segs in wl_range_segs])) != 1:
                    print(f'Warning: different pcontent range defs in {name}')
                    continue
                for k in range(len(wl_range_segs[0])):
                    wl_pcontent_powers = [r[k] for r in wl_range_segs]
                    csv_line = [name]
                    for iter_pc_cat in PCONTENT_CATEGORIES:
                        if iter_pc_cat == pc_cat:
                            csv_line.extend(wl_pcontent_powers)
                        else:
                            csv_line.extend([None for _ in wls])
                    csv.append(none_empty(csv_line))
    write_csv('World-Level PContent', csv)
