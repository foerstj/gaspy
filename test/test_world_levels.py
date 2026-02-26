import unittest

from test.files import Files
from world_levels.linear_regression import linear_regression


class TestWorldLevels(unittest.TestCase):
    files = Files()

    def test_linear_regression(self):
        linear_regression(self.files.logic_bits_dir, 'veteran', 'self')  # runs numpy


if __name__ == '__main__':
    unittest.main()
