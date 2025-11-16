from typing import Union

from bits.bits import Bits
from bits.templates import Template
from printouts.common import get_wl_templates, none_empty
from printouts.csv import write_csv


def wl_actor_skill(template: Template, skill_name: str):
    skill_value = template.compute_value('actor', 'skills', skill_name)
    if skill_value is None:
        return None
    return skill_value.split(',')[0]


def parse_value(value):
    if value is None:
        return value
    if isinstance(value, str):
        value = value.split()[0]  # dsx_zaurask_commander damage_max garbage after missing semicolon
        try:
            value = int(value)
        except:
            value = float(value)
    return value


def wl_actor_dict(template: Template) -> dict[str, Union[int, float]]:
    values = {
        'experience_value': template.compute_value('aspect', 'experience_value'),
        'defense': template.compute_value('defend', 'defense'),
        'damage_min': template.compute_value('attack', 'damage_min'),
        'damage_max': template.compute_value('attack', 'damage_max'),
        'life': template.compute_value('aspect', 'life'),
        'max_life': template.compute_value('aspect', 'max_life'),
        'mana': template.compute_value('aspect', 'mana'),
        'max_mana': template.compute_value('aspect', 'max_mana'),
        'strength': wl_actor_skill(template, 'strength'),
        'dexterity': wl_actor_skill(template, 'dexterity'),
        'intelligence': wl_actor_skill(template, 'intelligence'),
        'melee': wl_actor_skill(template, 'melee'),
        'ranged': wl_actor_skill(template, 'ranged'),
        'combat_magic': wl_actor_skill(template, 'combat_magic'),
        'nature_magic': wl_actor_skill(template, 'nature_magic'),
    }
    return {stat: parse_value(value) for stat, value in values.items()}


def write_world_level_stats_csv(bits: Bits):
    actors = bits.templates.get_actor_templates()
    wls_actors = get_wl_templates(actors)

    wls = ['regular', 'veteran', 'elite']
    skill_stats = ['strength', 'dexterity', 'intelligence', 'melee', 'ranged', 'combat_magic', 'nature_magic']
    other_stats = ['defense', 'damage_min', 'damage_max', 'life', 'max_life', 'mana', 'max_mana']
    stats = ['experience_value'] + other_stats + skill_stats
    csv = [['actor'] + [f'{wl} {stat}' for stat in stats for wl in wls]]
    for name, wl_actors in wls_actors.items():
        if None in wl_actors.values():
            continue  # e.g. molten_golem_summon_gom has no 2W/3W templates
        actors = [wl_actor_dict(wl_actors[wl]) for wl in wls]
        csv_line = [name]
        for stat in stats:
            wl_stats = [a[stat] for a in actors]
            csv_line += none_empty(wl_stats)
        csv.append(csv_line)
    write_csv('World-Level Stats', csv)
