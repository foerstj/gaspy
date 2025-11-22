import os
from pathlib import Path

from gas.gas import Section
from gas.gas_dir import GasDir
from gas.gas_file import GasFile

from .gas_dir_handler import GasDirHandler


class Template:
    def __init__(self, section: Section):
        self.section = section
        assert section.has_t_n_header('template')
        t, n = section.get_t_n_header()
        self.name: str = n

        specializes = None
        specializes_attr = section.get_attr('specializes')
        if specializes_attr is not None:
            specializes = specializes_attr.value
            if specializes.startswith('"') and specializes.endswith('"'):
                specializes = specializes[1:-1]
        self.specializes: str = specializes

        # these are set when connecting the template tree:
        self.parent_template = None
        self.child_templates = []

    @property
    def wl_prefix(self):
        if self.name.lower().startswith('2w_') or self.name.lower().startswith('3w_'):
            return self.name[:2].upper()
        return None

    @property
    def regular_name(self):
        if self.name.lower().startswith('2w_') or self.name.lower().startswith('3w_'):
            return self.name[3:]
        return self.name

    def base_templates(self, results=None) -> list['Template']:
        if results is None:
            results = []
        if self.specializes is not None:
            results.append(self.parent_template)
            self.parent_template.base_templates(results)  # recurse
        return results

    def is_descendant_of(self, template_name) -> bool:
        if self.name == template_name:
            return True
        if self.specializes is None:
            return False
        return self.parent_template.is_descendant_of(template_name)

    def is_leaf(self) -> bool:
        return len(self.child_templates) == 0

    def has_component(self, component_name) -> bool:
        if len(self.section.get_sections(component_name)) > 0:
            return True
        if self.specializes is None:
            return False
        return self.parent_template.has_component(component_name)

    def compute_value(self, *attr_path):
        if len(attr_path) <= 2:
            attr = self.section.resolve_attr(*attr_path)
            if attr is not None:
                return attr.value
        else:
            # template gas inheritance is not fully transparent, only up to the level of component-section properties
            section = self.section.resolve_section(*attr_path[:2])
            if section is not None:
                attr = section.resolve_attr(*attr_path[2:])
                if attr is not None:
                    return attr.value

        if self.specializes is not None:
            return self.parent_template.compute_value(*attr_path)
        return None

    def print(self, tree=None):
        if tree == 'base':
            tree_info_str = ' -> '.join([''] + [t.name for t in self.base_templates()])
        elif tree == 'children':
            tree_info_str = ' <- ' + ', '.join([t.name for t in self.child_templates]) if len(self.child_templates) > 0 else ''
        else:
            tree_info_str = ''
        print(self.name + tree_info_str)

    def is_plant(self):
        category_name = self.compute_value('category_name')
        if category_name is None:
            return False
        category_name = category_name.strip('"')
        return category_name in ['foliage', 'bushes', 'trees', 'logs', 'grass', 'flowers']


class Templates(GasDirHandler):
    def __init__(self, gas_dir):
        super().__init__(gas_dir)
        self.templates = None
        self.ignore_duplicate_template_names = False

    def load_templates_rec_gas(self, section: Section, templates: dict):
        if section.has_t_n_header('template'):
            template = Template(section)
            template_name = template.name.lower()
            if template_name in templates:
                if not self.ignore_duplicate_template_names:
                    assert template_name not in templates, 'duplicate template name: ' + template.name
                else:
                    print('duplicate template name: ' + template.name)
            templates[template_name] = template
        for subsection in section.get_sections():
            self.load_templates_rec_gas(subsection, templates)

    def load_templates_file(self, gas_file: GasFile, templates: dict):
        sections = gas_file.get_gas().items
        for section in sections:
            self.load_templates_rec_gas(section, templates)  # recurse into subsections

    def load_templates_rec_files(self, gas_dir: GasDir, templates: dict):
        for gas_file in gas_dir.get_gas_files().values():
            self.load_templates_file(gas_file, templates)
        # recurse into subdirs
        for name, subdir in gas_dir.get_subdirs().items():
            self.load_templates_rec_files(subdir, templates)

    def load_templates(self, gas_dir: GasDir):
        self.templates = {}
        self.load_templates_rec_files(gas_dir, self.templates)

    def connect_template_tree(self):
        for name, template in self.templates.items():
            if template.specializes is not None:
                parent_template = self.templates.get(template.specializes.lower())
                assert parent_template is not None, name + ' -> ' + template.specializes
                template.parent_template = parent_template
                parent_template.child_templates.append(template)

    def get_templates(self) -> dict[str, Template]:
        if self.templates is None:
            self.load_templates(self.gas_dir)
            self.connect_template_tree()
        return self.templates

    def get_actor_templates(self, leaf_only=True) -> dict[str, Template]:
        actor_templates = dict()
        for n, t in self.get_templates().items():
            # goblin templates are actually subclassed by dsx (albeit unused) but it somehow still works for the existing objects placed in map_world/gi_r3
            # dsx_utraean_townfolk_male_03 is also subclassed, by ilorn, and both are used, wtf were they doing
            if not leaf_only or t.is_leaf() or t.regular_name in ['goblin_inventor', 'goblin_robo_suit', 'dsx_utraean_townfolk_male_03']:
                if t.is_descendant_of('actor') or t.has_component('actor'):  # dsx_darkgenerator_clockroom has [actor] but is derived from prop
                    actor_templates[n] = t
        return actor_templates

    def get_enemy_templates(self) -> dict[str, Template]:
        enemy_templates = dict()
        for n, t in self.get_actor_templates().items():
            if t.is_descendant_of('actor_evil') and t.compute_value('actor', 'alignment') == 'aa_evil':
                enemy_templates[n] = t
            # dragon & goblin_robo_suit are actor_custom; gom is initially aa_good
            elif t.is_descendant_of('actor_custom') or t.regular_name == 'gom':
                enemy_templates[n] = t
        return enemy_templates

    def get_core_template_names(self, template_base: str = None) -> list[str]:
        core_templates = {}
        template_base_dir = self.gas_dir if not template_base else self.gas_dir.get_subdir(template_base.split('/'))
        self.load_templates_rec_files(template_base_dir.get_subdir(['regular', '_core']), core_templates)
        # templates are unconnected but we only return the names anyway
        return list(core_templates.keys())

    def get_decorative_container_template_names(self, template_base: str = None) -> list[str]:
        templates = {}
        template_base_dir = self.gas_dir if not template_base else self.gas_dir.get_subdir(template_base.split('/'))
        interactive_dir = template_base_dir.get_subdir(['regular', 'interactive'])
        self.load_templates_file(interactive_dir.get_gas_file('ctn_container'), templates)
        self.load_templates_file(interactive_dir.get_gas_file('ctn_chest'), templates)
        # templates are unconnected but we only return the names anyway
        return list(templates.keys())

    def get_nonblocking_template_names(self, template_base: str = None) -> list[str]:
        templates = {}
        template_base_dir = self.gas_dir if not template_base else self.gas_dir.get_subdir(template_base.split('/'))
        path_list = Path(template_base_dir.get_subdir('regular').path).rglob('*nonblocking*.gas')
        for path in path_list:
            rel_path = os.path.relpath(path, template_base_dir.path).split('\\')
            gas_file = template_base_dir.get_subdir(rel_path[:-1]).get_gas_file(rel_path[-1][:-4])
            self.load_templates_file(gas_file, templates)
        # templates are unconnected but we only return the names anyway
        return list(templates.keys())

    def get_leaf_templates(self, ancestor: str = None):
        templates = dict()
        for n, t in self.get_templates().items():
            if t.is_leaf():
                if ancestor is None or t.is_descendant_of(ancestor):
                    templates[n] = t
        return templates

    def filter_templates(self, leaf_only=True, ancestor: str = None):
        templates = dict()
        for n, t in self.get_templates().items():
            if not leaf_only or t.is_leaf():
                if ancestor is None or t.is_descendant_of(ancestor):
                    templates[n] = t
        return templates

    def get_container_templates(self, leaf_only=True) -> dict[str, Template]:
        return self.filter_templates(leaf_only, 'container')

    def get_generator_templates(self, leaf_only=True) -> dict[str, Template]:
        return self.filter_templates(leaf_only, 'generator')
