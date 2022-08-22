import sys
import random

from bits.bits import Bits
from bits.templates import Template
from gas.gas import Section, Attribute


def scale_enemy(template: Template):
    scale_base = float(template.compute_value('aspect', 'scale_base') or 1)
    veteran_factor = 2 ** (1 / 3)  # double volume
    elite_factor = 4 ** (1 / 3)  # double volume again
    if template.name.lower().startswith('2w_'):
        scale_base *= veteran_factor
    elif template.name.lower().startswith('3w_'):
        scale_base *= elite_factor
    template.section.get_or_create_section('aspect').set_attr_value('scale_base', scale_base)


def get_own_template_triggers(template: Template):
    template_triggers = None
    for common in template.section.get_sections('common'):
        tts = common.get_section('template_triggers')
        if tts is not None:
            template_triggers = tts  # last one wins
    return template_triggers


def get_template_triggers(template: Template):
    template_triggers = get_own_template_triggers(template)
    if template_triggers is not None:
        return template_triggers
    if template.parent_template is not None:
        return get_template_triggers(template.parent_template)
    return None


def bling_enemy(template: Template):
    name = template.name.lower()
    if name.startswith('2w_') or name.startswith('3w_'):
        template_triggers = get_template_triggers(template)
        own_template_triggers = get_own_template_triggers(template)
        commons = template.section.get_sections('common')
        common = commons[0] if len(commons) > 0 else template.section.get_or_create_section('common')
        if own_template_triggers is None:
            if template_triggers is None:
                own_template_triggers = Section('template_triggers')
            else:
                own_template_triggers = template_triggers.copy()  # copy base template's triggers if necessary
            common.insert_item(own_template_triggers)

        random.seed(name)  # random but reproducible
        color = random.choice(['red', 'green', 'blue', 'yellow', 'cyan', 'purple'])
        sfxs = ['unique_light_'+color]
        if name.startswith('3w_'):
            sfxs.append('unique_ray_'+color)
        for sfx in sfxs:
            trigger = Section('*', [
                Attribute('condition*', 'receive_world_message("WE_ENTERED_WORLD")'),
                Attribute('action*', f'call_sfx_script("{sfx}(sgx)")'),
                Attribute('no_trig_bits', True),
                Attribute('single_shot', True)
            ])
            own_template_triggers.insert_item(trigger)


def pimp_enemy(template: Template):
    print(template.name)
    scale_enemy(template)
    bling_enemy(template)


def valhalla(bits: Bits):
    for name, template in bits.templates.get_enemy_templates().items():
        pimp_enemy(template)
    bits.templates.gas_dir.get_subdir('veteran').save()
    bits.templates.gas_dir.get_subdir('elite').save()


def main(argv):
    bits_path = argv[0] if len(argv) > 0 else None
    bits = Bits(bits_path)
    valhalla(bits)


if __name__ == '__main__':
    main(sys.argv[1:])
