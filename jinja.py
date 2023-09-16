import sys
from jinja2 import Environment, select_autoescape, FileSystemLoader


def main(argv):
    env = Environment(
        loader=FileSystemLoader('input'),
        autoescape=select_autoescape()
    )
    template = env.get_template('jinja-test.txt.jinja')
    print(template.render(foo='bar', jinja='bazinga'))


if __name__ == '__main__':
    main(sys.argv[1:])
