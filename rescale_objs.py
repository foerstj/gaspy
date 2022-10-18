# - Use rescaled versions of templates (using scale_base instead of scale_multiplier)
# - Adapt object scale_multiplier values so that size is unchanged
# Rescaled templates are defined in minibits: https://github.com/foerstj/minibits/tree/main/templates-rescaled

import sys

from bits.bits import Bits
from bits.maps.game_object import GameObject
from bits.maps.region import Region
from bits.templates import Template


def rescale_objs_region(region: Region, misscaled_templates: dict[str, Template]):
    print(region.get_name())
    region.objects.load_objects()
    num_rescaled = 0
    for gos in [region.objects.objects_actor, region.objects.objects_interactive, region.objects.objects_non_interactive]:
        for go in gos:
            assert isinstance(go, GameObject)
            if go.template_name in misscaled_templates:
                num_rescaled += 1
                rescaled_template_name = go.template_name + '_rescaled'
                go.section.set_t_n_header(rescaled_template_name, go.section.get_t_n_header()[1])
                scale_multiplier = misscaled_templates[go.template_name].compute_value('aspect', 'scale_multiplier')
                assert scale_multiplier is not None
                scale_multiplier = float(scale_multiplier)
                assert scale_multiplier > 0
                scale_multiplier = 1 / scale_multiplier
                scale_multiplier_attr = go.section.get_or_create_section('aspect').get_attr('scale_multiplier')
                if scale_multiplier_attr:
                    scale_multiplier *= float(scale_multiplier_attr.value)
                go.section.get_section('aspect').set_attr_value('scale_multiplier', scale_multiplier)
    if num_rescaled:
        print(f'  {num_rescaled} objects rescaled')
        region.save()
    return num_rescaled


def get_misscaled_templates(bits: Bits) -> dict[str, Template]:
    misscaled_templates = dict()
    for name, template in bits.templates.get_templates().items():
        scale_multiplier = template.compute_value('aspect', 'scale_multiplier')
        if scale_multiplier is not None and scale_multiplier != 1:
            misscaled_templates[name] = template
    return misscaled_templates


def rescale_objs(map_name: str, region_name: str):
    bits = Bits()
    m = bits.maps[map_name]
    misscaled_templates = get_misscaled_templates(bits)

    if region_name is not None:
        rescale_objs_region(m.get_region(region_name), misscaled_templates)
    else:
        num_rescaled = 0
        for region in m.get_regions().values():
            num_rescaled += rescale_objs_region(region, misscaled_templates)
        print(f'Altogether {num_rescaled} objects rescaled')


def main(argv):
    map_name = argv[0]
    region_name = argv[1] if len(argv) > 1 else None
    rescale_objs(map_name, region_name)


if __name__ == '__main__':
    main(sys.argv[1:])
