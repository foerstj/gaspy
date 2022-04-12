from gas.gas import Section
from gas.gas_dir import GasDir

from .gas_dir_handler import GasDirHandler


class Template:
    def __init__(self, section: Section):
        self.section = section
        [t, n] = section.header.split(',')
        assert t.startswith('t:')
        assert n.startswith('n:')
        gas_obj_type = t[2:]
        assert gas_obj_type.lower() == 'template'
        self.name: str = n[2:]
        specializes = None
        specializes_attr = section.get_attr('specializes')
        if specializes_attr is not None:
            specializes = specializes_attr.value
            if specializes.startswith('"') and specializes.endswith('"'):
                specializes = specializes[1:-1]
        self.specializes: str = specializes
        self.parent_template = None
        self.child_templates = []

    def base_templates(self, results=None):
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

    def compute_value(self, *attr_path):
        attr = self.section.resolve_attr(*attr_path)
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


class Templates(GasDirHandler):
    def __init__(self, gas_dir):
        super().__init__(gas_dir)
        self.templates = None

    def load_templates_rec(self, section: Section):
        if section.header.lower().startswith('t:template,'):
            template = Template(section)
            assert template.name.lower() not in self.templates, 'duplicate template name'
            self.templates[template.name.lower()] = template
        for subsection in section.get_sections():
            self.load_templates_rec(subsection)

    def load_templates(self, gas_dir: GasDir):
        if self.templates is None:
            self.templates = {}
        for gas_file in gas_dir.get_gas_files().values():
            sections = gas_file.get_gas().items
            for section in sections:
                self.load_templates_rec(section)  # recurse into sub-sections
        # recurse into subdirs
        for name, subdir in gas_dir.get_subdirs().items():
            self.load_templates(subdir)

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

    def get_enemy_templates(self) -> dict[str, Template]:
        enemy_templates = dict()
        for n, t in self.get_templates().items():
            if t.is_leaf():
                if t.is_descendant_of('actor_evil') and t.compute_value('actor', 'alignment') == 'aa_evil':
                    enemy_templates[n] = t
        return enemy_templates
