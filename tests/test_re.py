import unittest
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).absolute().parent
sys.path.append(str(HERE.parent / 'src'))


class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        from canoe.client import ANCHORE_PATTERN
        m = ANCHORE_PATTERN.search(' class:anchor class:_0 ')
        self.assertIsNotNone(m)


if __name__ == '__main__':
    unittest.main()
