import argparse

import sys

from bits.bits import Bits
from bits.templates import Template


def printout_template_texture_mismatch(template: Template, bits: Bits):
    if not template.is_leaf():
        return  # not interested
    if not template.is_descendant_of('actor'):
        return  # not interested right now
    if template.wl_prefix is not None:
        return  # just redundant
    if template.has_component('aspect') and template.has_component('physics'):
        main_texture = template.compute_value('aspect', 'textures', '0')
        break_particulate_section = template.resolve_section('physics', 'break_particulate')
        if main_texture is not None and break_particulate_section is not None:
            frag_template_names = [attr.name for attr in break_particulate_section.items]
            frag_textures = set()
            for frag_template_name in frag_template_names:
                frag_template = bits.templates.templates[frag_template_name]
                assert frag_template.has_component('aspect')
                frag_texture = frag_template.compute_value('aspect', 'textures', '0')
                if frag_texture is not None:
                    frag_textures.add(frag_texture)
            for frag_texture in frag_textures:
                if frag_texture.startswith('b_i_glb_frag-generic-'):
                    continue
                if frag_texture != main_texture:
                    print(f'Texture mismatch in {template.name}: {main_texture} != {frag_texture}')


def printout_texture_mismatch(bits: Bits):
    templates = bits.templates.get_templates()
    for template in templates.values():
        printout_template_texture_mismatch(template, bits)
    print('Note: can only check explicitly defined textures')


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printouts texture_mismatch')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    bits = Bits(args.bits)
    printout_texture_mismatch(bits)


if __name__ == '__main__':
    main(sys.argv[1:])
