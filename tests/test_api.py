import logging
import sys
import unittest
from http import HTTPStatus
from unittest import mock  # pylint: disable=unused-import

import flask

from webhook_api.app_factory import create_app

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestAPIRoutes(unittest.TestCase):
    '''Test common api routes'''

    def setUp(self):
        self.app: flask.Flask = create_app()
        self.app_context: flask.ctx.RequestContext = self.app.test_request_context()
        self.app_context.push()
        self.client: flask.testing.FlaskClient = self.app.test_client()

    def test_favicon(self):
        rv: flask.Response = self.client.get('/favicon.ico')
        assert rv.status_code == HTTPStatus.NO_CONTENT, 'Should return 204 - No Content'


if __name__ == '__main__':
    unittest.main()
