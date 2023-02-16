from bits.bits import Bits
from printouts.csv import write_csv


def write_spells_csv(bits: Bits):
    spell_templates = bits.templates.get_leaf_templates('spell')
    csv_header = ['Template', 'Name', 'Scroll', 'P/M', 'N/C']
    csv = [csv_header]
    for spell_template in spell_templates.values():
        template_name = spell_template.name
        screen_name = spell_template.compute_value('common', 'screen_name')
        spell_name = '' if not screen_name else screen_name.strip('"')
        one_use = spell_template.compute_value('magic', 'one_use')
        is_scroll = one_use and one_use.lower() == 'true'
        is_monster = spell_template.is_descendant_of('base_spell_monster')
        pm = 'P' if not is_monster else 'M'
        magic_class = spell_template.compute_value('magic', 'magic_class')
        assert magic_class in ['mc_nature_magic', 'mc_combat_magic']
        nc = 'N' if magic_class == 'mc_nature_magic' else 'C'
        csv.append([template_name, spell_name, 'SCROLL' if is_scroll else '', pm, nc])
    write_csv('Spells', csv)
