from bits.bits import Bits
from printouts.common import get_wl_templates, none_empty
from printouts.csv import write_csv


def write_world_level_gold_csv(bits: Bits):
    templates = bits.templates.get_actor_templates(False)
    templates.update(bits.templates.get_container_templates(False))
    wls_templates = get_wl_templates(templates)
    wls = ['regular', 'veteran', 'elite']
    stats = ['min', 'max']
    csv = [['template'] + [f'{wl} {stat}' for stat in stats for wl in wls]]
    for name, wl_templates in wls_templates.items():
        wls_gold_sections = {wl: template.section.find_sections_recursive('gold*') for wl, template in wl_templates.items()}
        counts = [len(sections) for sections in wls_gold_sections.values()]
        if len(set(counts)) != 1:
            print('Warning: differing numbers of gold sections in ' + name)
            continue
        for i in range(counts[0]):
            wl_gold_sections = [wls_gold_sections[wl][i] for wl in wls]
            csv_line = [name]
            for stat in stats:
                wl_stats = [gs.get_attr_value(stat) for gs in wl_gold_sections]
                csv_line += none_empty(wl_stats)
            csv.append(csv_line)
    write_csv('World-Level Gold', csv)
