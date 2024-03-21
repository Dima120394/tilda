# pylint: disable=no-self-use
import logging
import os
import sys
import typing  # pylint: disable=unused-import
import unittest
from unittest import mock  # pylint: disable=unused-import

#from .utils import load_assets

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class TestStub(unittest.TestCase):

    def test_stub(self):
        logger.debug('Test stub passed')
        assert True

    def test_failure(self):
        with self.assertRaises(TypeError):
            None / 1


if __name__ == '__main__':
    unittest.main()
