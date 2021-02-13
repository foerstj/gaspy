import os

from gas_dir_handler import GasDirHandler


class GameObject:
    def __init__(self, section, bits):
        self._bits = bits
        self.section = section
        [t, n] = section.header.split(',')
        assert t.startswith('t:')
        assert n.startswith('n:')
        self.template_name = t[2:]
        self.object_id = n[2:]

    def get_template(self):
        template = self._bits.templates.get_templates().get(self.template_name)
        assert template is not None, self.template_name
        return template


class Region(GasDirHandler):
    def __init__(self, gas_dir, bits):
        super().__init__(gas_dir)
        self._bits = bits

    def get_actors(self):
        objects_dir = self.gas_dir.get_subdir('objects')
        if objects_dir is None:
            return []
        if 'regular' in objects_dir.get_subdirs():
            objects_dir = objects_dir.get_subdir('regular')  # deal with multiple worlds another time
        actor_file = objects_dir.get_gas_file('actor')
        if actor_file is None:
            return []
        actor_sections = actor_file.get_gas().items
        return [GameObject(s, self._bits) for s in actor_sections]

    def get_stitches(self):
        stitch_helper_file = self.gas_dir.get_subdir('editor').get_gas_file('stitch_helper')
        if stitch_helper_file is None:
            return []
        stitch_sections = stitch_helper_file.get_gas().get_section('stitch_helper_data').get_sections()
        return [s.get_attr('dest_region').value for s in stitch_sections]

    def get_xp(self):
        actors = self.get_actors()
        evil_actors = [a for a in actors if a.get_template().is_descendant_of('actor_evil')]
        xps = [int(ea.get_template().section.get_section('aspect').get_attr('experience_value').value) for ea in evil_actors]
        return sum(xps)

    def actors_str(self):
        actors = self.get_actors()
        actor_templates = [a.template_name for a in actors]
        counts_by_template = {t: 0 for t in set(actor_templates)}
        for t in actor_templates:
            counts_by_template[t] += 1
        actor_templates_str = ': ' + ', '.join([str(count) + ' ' + t for t, count in counts_by_template.items()]) if len(actors) > 0 else ''
        return str(len(actors)) + ' actors' + actor_templates_str

    def stitches_str(self):
        stitches = self.get_stitches()
        return ', '.join(stitches)

    def print(self, indent='', info='xp'):
        if info == 'actors':
            info = self.actors_str()
        elif info == 'stitches':
            info = self.stitches_str()
        elif info == 'xp':
            info = str(self.get_xp()) + ' XP'
        else:
            info = False
        print(indent + os.path.basename(self.gas_dir.path) + (' - ' + info if isinstance(info, str) else ''))


class Map(GasDirHandler):
    def __init__(self, gas_dir, bits):
        super().__init__(gas_dir)
        self._bits = bits

    def get_regions(self):
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        return {name: Region(gas_dir, self._bits) for name, gas_dir in regions.items()}

    def print(self, print_regions='stitches'):
        main_file = self.gas_dir.get_gas_file('main')
        assert main_file is not None
        main = main_file.get_gas()
        map_main = main.get_section('t:map,n:map')
        name = map_main.get_attr('name')
        screen_name = map_main.get_attr('screen_name').value
        name_str = name.value + ' ' + screen_name if name is not None else screen_name
        description = map_main.get_attr('description').value
        regions = self.get_regions()
        print('Map: ' + name_str + ' (' + str(len(regions)) + ' regions) - ' + description)
        if print_regions:
            for region in regions.values():
                region.print('  ', print_regions)
