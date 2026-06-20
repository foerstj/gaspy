import argparse
import sys

from bits.bits import Bits
from bits.templates import Template


def unmod(template_path: str, bits_path: str):
    bits = Bits(bits_path)
    # bits.templates.get_templates()

    path_segs = template_path.split('/')
    gas_dir = bits.templates.gas_dir
    templates = dict()
    if len(path_segs) > 0:
        gas_dir = gas_dir.get_subdir(path_segs[:-1])
        last_seg = path_segs[-1]
        if gas_dir.has_subdir(last_seg):
            gas_dir = gas_dir.get_subdir(last_seg)
            bits.templates.load_templates_rec_files(gas_dir, templates)
        elif gas_dir.has_gas_file(last_seg):
            bits.templates.load_templates_file(gas_dir.get_gas_file(last_seg), templates)

    # templates = [bits.templates.templates[template_name] for template_name in templates]
    for name, template in templates.items():
        if template.specializes is not None:
            parent_template = templates.get(template.specializes.lower())
            if parent_template is None:
                continue
            template.parent_template = parent_template
            parent_template.child_templates.append(template)
    templates = templates.values()
    templates = [t for t in templates if t.is_leaf()]
    # templates = [t for t in templates if t.is_equipment()]

    for template in templates:
        assert isinstance(template, Template)
        existing = template.section.resolve_attr('common', 'is_pcontent_allowed')
        if existing is not None:
            existing.value = False
            continue

        commons = template.section.get_sections('common')
        if len(commons) > 0:
            common = commons[-1]
        else:
            common = template.section.get_or_create_section('common')
        common.set_attr_value('is_pcontent_allowed', False)
    gas_dir.save()


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description='GasPy Unmod')
    parser.add_argument('template_path', type=str)
    parser.add_argument('--bits')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    unmod(args.template_path, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
