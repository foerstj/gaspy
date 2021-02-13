from gas_dir import GasDir
from gas_dir_handler import GasDirHandler


class Template:
    def __init__(self, section):
        self.section = section
        [t, n] = section.header.split(',')
        assert t.startswith('t:')
        assert n.startswith('n:')
        gas_obj_type = t[2:]
        assert gas_obj_type == 'template'
        self.name = n[2:]
        specializes_attr = section.get_attr('specializes')
        self.specializes = specializes_attr.value if specializes_attr is not None else None
        self.parent_template = None
        self.child_templates = []

    def base_templates(self, results=None):
        if results is None:
            results = []
        if self.specializes is not None:
            results.append(self.parent_template)
            self.parent_template.base_templates(results)  # recurse
        return results

    def is_descendant_of(self, template_name):
        if self.name == template_name:
            return True
        if self.specializes is None:
            return False
        return self.parent_template.is_descendant_of(template_name)

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

    def load_templates(self, gas_dir: GasDir):
        if self.templates is None:
            self.templates = {}
        for gas_file in gas_dir.get_gas_files().values():
            sections = gas_file.get_gas().items
            template_sections = [s for s in sections if s.header.startswith('t:template,')]
            templates = [Template(ts) for ts in template_sections]
            for template in templates:
                assert template.name not in self.templates, 'duplicate template name'
                self.templates[template.name] = template
        # recurse
        for name, subdir in gas_dir.get_subdirs().items():
            if name in ['veteran', 'elite']:
                continue  # deal with multiple worlds another time
            self.load_templates(subdir)

    def connect_template_tree(self):
        for name, template in self.templates.items():
            if template.specializes is not None:
                parent_template = self.templates.get(template.specializes)
                template.parent_template = parent_template
                parent_template.child_templates.append(template)

    def get_templates(self):
        if self.templates is None:
            self.load_templates(self.gas_dir)
            self.connect_template_tree()
        return self.templates
