import unittest

from mapgen.heightmap.save_image import save_image


class TestMapgenHeightmap(unittest.TestCase):

    def test_save_image(self):
        dummy_pic = [[1, 0], [0.3, 0.7]]
        save_image(dummy_pic, 'test_save_image')  # runs matplotlib


if __name__ == '__main__':
    unittest.main()
