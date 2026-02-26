import unittest

from jinja import jinja


class TestJinja(unittest.TestCase):
    def test_jinja(self):
        jinja('test_jinja', 'input', 'output', None, 'each', None, dict())


if __name__ == '__main__':
    unittest.main()
