import os

from gas_dir_handler import GasDirHandler


class GameObject:
    def __init__(self, section):
        self.section = section
        [t, n] = section.header.split(',')
        assert t.startswith('t:')
        assert n.startswith('n:')
        self.template_name = t[2:]
        self.object_id = n[2:]


class Region(GasDirHandler):
    def get_actors(self):
        objects_dir = self.gas_dir.get_subdir('objects')
        if objects_dir is None:
            return []
        if 'regular' in objects_dir.get_subdirs():
            objects_dir = objects_dir.get_subdir('regular')
        actor_file = objects_dir.get_gas_file('actor')
        if actor_file is None:
            return []
        actor_sections = actor_file.get_gas().items
        return [GameObject(s) for s in actor_sections]

    def print(self, indent=''):
        actors = self.get_actors()
        actor_templates = [a.template_name for a in actors]
        counts_by_template = {t: 0 for t in set(actor_templates)}
        for t in actor_templates:
            counts_by_template[t] += 1
        actor_templates_str = ': ' + ', '.join([str(count) + ' ' + t for t, count in counts_by_template.items()]) if len(actors) > 0 else ''
        print(indent + os.path.basename(self.gas_dir.path) + ' - ' + str(len(actors)) + ' actors' + actor_templates_str)


class Map(GasDirHandler):
    def get_regions(self):
        regions = self.gas_dir.get_subdir('regions').get_subdirs()
        return {name: Region(gas_dir) for name, gas_dir in regions.items()}

    def print(self, print_regions=True):
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
                region.print('  ')
