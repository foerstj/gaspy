import os
import random
import shutil
import sys
import time

from bits.bits import Bits
from bits.templates import Template
from gas.gas import Section, Attribute


"""
Make Veteran & Elite Great Again!
Veteran should look like the Valhalla of Regular, and Elite should look like the Valhalla of Veteran.
"""


def compute_scale_base(template: Template) -> float:
    value = template.compute_value('aspect', 'scale_base')
    if value is None:
        return 1.0
    if isinstance(value, float):
        return value
    return float(value.split()[0])  # missing semicolon. dsx_chitterskrag_boss


def set_scale_base(template: Template, scale_base: float):
    attr = template.section.resolve_attr('aspect', 'scale_base')
    if attr is None:
        aspects = template.section.get_sections('aspect')
        aspect = aspects[0] if len(aspects) > 0 else template.section.get_or_create_section('aspect')
        aspect.set_attr_value('scale_base', scale_base)
    else:
        attr.set_value(scale_base)


def scale_enemy(template: Template, additional_upscales=0):
    if 'lostqueen' in template.name:
        return  # the lost queen and her tail are placed so that they fit together

    num_upscales = 0
    if template.name.lower().startswith('2w_'):
        num_upscales += 1  # veteran enemy is up-scaled once
    elif template.name.lower().startswith('3w_'):
        num_upscales += 2  # elite enemy is up-scaled twice
    num_upscales += additional_upscales  # to compensate for failed blings, enemy is up-scaled even more
    volume_factor = 2 ** num_upscales  # enemy volume is doubled for every up-scale
    scale_factor = volume_factor ** (1 / 3)  # scale factor is cubic root of volume factor

    scale_base = compute_scale_base(template)
    scale_base *= scale_factor
    set_scale_base(template, scale_base)


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
    num_failed_blings = 0
    name = template.name.lower()
    name_parts = name.split('_')
    if name_parts[0] == '2w' or name_parts[0] == '3w':
        has_unique_light = False
        has_unique_ray = False
        template_triggers = get_template_triggers(template)
        if template_triggers is not None:
            for template_trigger in template_triggers.get_sections('*'):
                for action_attr in template_trigger.get_attrs('action*'):
                    if action_attr.value.startswith('call_sfx_script("unique_light'):
                        has_unique_light = True
                    if action_attr.value.startswith('call_sfx_script("unique_ray'):
                        has_unique_ray = True

        sfxs = []
        if not has_unique_light:
            sfxs.append('unique_light')
        else:
            num_failed_blings += 1
        if name_parts[0] == '3w':
            if not has_unique_ray:
                sfxs.append('unique_ray')
            else:
                num_failed_blings += 1
        if len(sfxs) == 0:
            return num_failed_blings

        own_template_triggers = get_own_template_triggers(template)
        commons = template.section.get_sections('common')
        common: Section = commons[0] if len(commons) > 0 else template.section.get_or_create_section('common')
        if own_template_triggers is None:
            if template_triggers is None:
                own_template_triggers = Section('template_triggers')
            else:
                own_template_triggers = template_triggers.copy()  # copy base template's triggers if necessary
            common.insert_item(own_template_triggers)

        color = choose_color(name)
        for sfx in sfxs:
            trigger = Section('*', [
                Attribute('condition*', 'receive_world_message("WE_ENTERED_WORLD")'),
                Attribute('action*', f'call_sfx_script("{sfx}_{color}(sgx)")'),
                Attribute('no_trig_bits', True),
                Attribute('single_shot', True)
            ])
            own_template_triggers.insert_item(trigger)
    return num_failed_blings


def choose_color(template_name):
    color_choice = ['red', 'green', 'blue', 'yellow', 'cyan', 'purple']
    ignore_name_parts = {'2w', '3w', 'reveal', 'act', 'temp', 'poking', 'eating', 'r', 'q', 'summon', 'mp', 'lhaoc', 'ar'}  # ignore reveal effects and world-level
    name_parts = template_name.split('_')
    name_parts = [x for x in name_parts if x not in ignore_name_parts]
    base_name = '_'.join(name_parts)

    # shards
    for color in color_choice:
        if color in name_parts:
            return color
    if 'teal' in name_parts:
        return 'cyan'

    if 'ice' in name_parts:
        color_choice = ['green', 'blue', 'cyan', 'purple']  # no warm colors for ice enemies

    random.seed(base_name)  # random but reproducible
    return random.choice(color_choice)


def pimp_enemy(template: Template):
    print(template.name)
    num_failed_blings = bling_enemy(template)
    scale_enemy(template, num_failed_blings)


def copy_templates(bits: Bits):
    for wl in ['veteran', 'elite']:
        src = os.path.join(bits.gas_dir.path, 'world', 'contentdb', 'git-ignore', 'templates', wl)
        dst = os.path.join(bits.gas_dir.path, 'world', 'contentdb', 'templates', wl)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        time.sleep(0.1)  # shutil...


def valhalla(bits: Bits):
    copy_templates(bits)

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
