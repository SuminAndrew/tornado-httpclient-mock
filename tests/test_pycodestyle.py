# coding=utf-8

from functools import partial
import os.path
import unittest

import pycodestyle

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


class TestPycodestyle(unittest.TestCase):
    CHECKED_PATHS = ('tornado_mock', 'tests', 'setup.py')

    def test_pycodestyle(self):
        style_guide = pycodestyle.StyleGuide(
            show_pep8=False,
            show_source=True,
            max_line_length=120
        )
        result = style_guide.check_files(map(partial(os.path.join, PROJECT_ROOT), TestPycodestyle.CHECKED_PATHS))
        self.assertEqual(result.total_errors, 0, 'Pycodestyle found code style errors or warnings')
