import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.common import parse_bool_value, parse_value


GENERIC_TEXTURES = ['b_w_weapons']


class TemplateInfo:
    def __init__(self, model: str, texture: str, scale: float):
        self.model = model
        self.texture = texture
        self.scale = scale

    @classmethod
    def from_template(cls, template: Template):
        model = template.compute_value('aspect', 'model')
        assert model, template.name
        texture = template.compute_value('aspect', 'textures', '0')
        scale = parse_value(template.compute_value('aspect', 'scale_base')) or 1.0
        return TemplateInfo(model, texture, scale)


class Actor:
    def __init__(self, info: TemplateInfo, frags: list['Frag']):
        self.info = info
        self.frags = frags


class Frag:
    def __init__(self, info: TemplateInfo, usages: list['Actor']):
        self.info = info
        self.actors = usages


def run_printout_frags(bits_path: str):
    print('parsing templates...')
    bits = Bits(bits_path)
    GasParser.get_instance().print_warnings = False
    bits.templates.get_templates()
    print('evaluating frags...')

    # first pass - build data structure of actors & frags
    actors: dict[str, Actor] = dict()
    frags: dict[str, Frag] = dict()
    all_enemies = bits.templates.get_enemy_templates()
    for actor_template in all_enemies.values():
        if actor_template.wl_prefix is not None:
            continue
        gib_gore_good = parse_bool_value(actor_template.compute_value('physics', 'gib_gore_good'))
        ewk_str = actor_template.compute_value('physics', 'explode_when_killed')
        explode_when_killed = False if ewk_str is None else parse_bool_value(ewk_str.split()[0])  # missing semicolon in krug_dog_skeleton
        if not gib_gore_good and not explode_when_killed:
            continue
        break_particulate = actor_template.resolve_section('physics', 'break_particulate')
        if break_particulate is None:
            continue

        assert actor_template.name not in actors
        actor_info = TemplateInfo.from_template(actor_template)
        actor = Actor(actor_info, list())
        actors[actor_template.name] = actor

        frag_names = [a.name for a in break_particulate.get_attrs()]
        for frag_name in frag_names:
            if frag_name.lower() not in frags:
                frag_template = bits.templates.templates[frag_name.lower()]
                frag_info = TemplateInfo.from_template(frag_template)
                frag = Frag(frag_info, list())
                frags[frag_name.lower()] = frag
            frag = frags[frag_name.lower()]
            frag.actors.append(actor)
            actor.frags.append(frag)

    # second pass - check for mismatches
    num_enemies_with_mismatches = 0
    for actor_name, actor in actors.items():
        frag_textures = set([f.info.texture for f in actor.frags])
        frag_scales = set([f.info.scale for f in actor.frags])
        texture_mismatch = None if actor.info.texture is None else any([t is not None and t not in GENERIC_TEXTURES and t != actor.info.texture for t in frag_textures])
        scale_mismatch = None if actor.info.scale is None else any([s is not None and s != actor.info.scale for s in frag_scales])
        if texture_mismatch:
            frag_textures_str = ', '.join([str(t) for t in frag_textures])
            print(f'{actor_name}: texture mismatch: {actor.info.texture} - {frag_textures_str}')
        if scale_mismatch:
            frag_scales_str = ', '.join([str(s) for s in frag_scales])
            print(f'{actor_name}: scale mismatch: {actor.info.scale} - {frag_scales_str}')
        if texture_mismatch or scale_mismatch:
            num_enemies_with_mismatches += 1
    print(f'num enemies with mismatches: {num_enemies_with_mismatches}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Frags')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    run_printout_frags(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
