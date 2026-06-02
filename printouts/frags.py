import argparse

import sys

from bits.bits import Bits
from bits.templates import Template
from gas.gas_parser import GasParser
from printouts.common import parse_bool_value, parse_value


# TODO greenlight mucosa re-use
# TODO greenlight rock-beast frag sizes
# TODO find cobbleman texture mismatch via other frag actors & known default textures & --unsure option


GENERIC_TEXTURES = [
    'b_w_weapons',  # e.g. spikes on spiked dwellers
    'b_i_glb_frag-generic',  # flesh
    'b_i_glb_frag-generic-02',  # darker flesh
]

DEFAULT_TEXTURES = {
    'm_c_ebb_grs_flamethrower_1': 'b_c_ebb_grs',
    'm_c_ebb_grs_lightninggun_1': 'b_c_ebb_grs',
    'm_c_ebb_grs_minigun_1': 'b_c_ebb_grs',
    'm_c_ebb_grs_torso_1': 'b_c_ebb_grs',

    'm_c_ecm_sk_pos_2': 'b_c_ecm_skg',

    'm_c_edm_au2': 'b_c_edm_au-03',
    'm_c_edm_au': 'b_c_edm_au',
    'm_c_edm_aw': 'b_c_edm_au-04',
    'm_c_edm_sa': 'b_c_edm_au-05',
    'm_c_edm_st_pos_1': 'b_c_edm_ph-02',
    'm_c_edm_twmu_pos_1': 'b_c_edm_twisted_mucosa',

    'm_i_gob_tesla-coil-01': 'b_i_gob_tesla-coil-01',
    'm_i_gob_tesla-coil-03': 'b_i_gob_tesla-coil-01',
}


def get_default_texture(model: str) -> str:
    assert model.startswith('m_')
    if model in DEFAULT_TEXTURES:
        return DEFAULT_TEXTURES[model]
    if model.endswith('_pos_1'):
        return 'b_' + model[2:-6]
    assert False, model


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


class Mismatches:
    def __init__(self, texture: str, scale: str):
        self.texture = texture
        self.scale = scale

    def has_mismatch(self, unsure=False):
        bad_values = ['mismatch']
        if unsure:
            bad_values.append('unsure')
        return self.texture in bad_values or self.scale in bad_values


def evaluate_actor_frag_texture(actor: Actor, frag: Frag) -> str:
    if actor.info.texture is None:
        return 'unsure'
    if frag.info.texture is None:
        return 'unsure'
    if frag.info.texture in GENERIC_TEXTURES:
        return 'generic'
    return 'match' if actor.info.texture == frag.info.texture else 'mismatch'


def evaluate_actor_frag_scale(actor: Actor, frag: Frag) -> str:
    assert actor.info.scale is not None and frag.info.scale is not None
    return 'match' if actor.info.scale == frag.info.scale else 'mismatch'


def evaluate_actor_frag(actor: Actor, frag: Frag) -> Mismatches:
    texture = evaluate_actor_frag_texture(actor, frag)
    scale = evaluate_actor_frag_scale(actor, frag)
    return Mismatches(texture, scale)


RESULTS = ['mismatch', 'unsure', 'generic', 'match']


def get_worst(evals: list[str]) -> str:
    for r in RESULTS:
        if r in evals:
            return r
    assert False, evals


def evaluate_actor(actor: Actor) -> Mismatches:
    frag_evals = [evaluate_actor_frag(actor, frag) for frag in actor.frags]
    textures = get_worst([frag_eval.texture for frag_eval in frag_evals])
    scales = get_worst([frag_eval.scale for frag_eval in frag_evals])
    return Mismatches(textures, scales)


def run_printout_frags(bits_path: str, unsure=False):
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
        if actor_info.texture is None:
            actor_info.texture = get_default_texture(actor_info.model)
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
        actor_mismatches = evaluate_actor(actor)

        if actor_mismatches.texture == 'mismatch' or (unsure and actor_mismatches.texture == 'unsure'):
            frag_textures = set([f.info.texture for f in actor.frags])
            frag_textures_str = ', '.join([str(t) for t in frag_textures])
            print(f'{actor_name}: texture mismatch: {actor.info.texture} - {frag_textures_str}')
        if actor_mismatches.scale == 'mismatch' or (unsure and actor_mismatches.scale == 'unsure'):
            frag_scales = set([f.info.scale for f in actor.frags])
            frag_scales_str = ', '.join([str(s) for s in frag_scales])
            print(f'{actor_name}: scale mismatch: {actor.info.scale} - {frag_scales_str}')

        if actor_mismatches.has_mismatch(unsure):
            num_enemies_with_mismatches += 1

    print(f'num enemies with mismatches: {num_enemies_with_mismatches}')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Printout Frags')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--unsure', action='store_true')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    run_printout_frags(args.bits, args.unsure)


if __name__ == '__main__':
    main(sys.argv[1:])
