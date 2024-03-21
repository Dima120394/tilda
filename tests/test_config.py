import logging
import os
import sys
import unittest
from http import HTTPStatus
from unittest import mock  # pylint: disable=unused-import

from webhook_api.config import Config
from webhook_api.providers import Providers

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestConfig(unittest.TestCase):
    '''Test common api routes'''

    @mock.patch.dict(os.environ, {'API_TOKENS': ''})
    def test_config_api_tokens_empty(self):
        config = Config()
        assert config.tokens == []

    @mock.patch.dict(os.environ, {'API_TOKENS': 'qwerty,other'})
    def test_config_api_tokens_set(self):
        config = Config()
        assert len(config.tokens) == 2
        assert 'qwerty' in config.tokens

    @mock.patch.dict(os.environ, {'COLLECT_REQUESTS': ''})
    def test_config_coolect_requests_not_set(self):
        config = Config()
        assert config.is_requests_colleced is False

    @mock.patch.dict(os.environ, {'COLLECT_REQUESTS': '1'})
    def test_config_coolect_requests_set(self):
        config = Config()
        assert config.is_requests_colleced is True

    @mock.patch.dict(os.environ, {
        'TELEGRAM_TOKEN': 'bot_token',
        'TELEGRAM_CHAT_ID': '123456',
        'SOCPROOF_TOKEN': 'socproof_token',
        'JUSTANOTHERPANEL_TOKEN': 'justanotherpanel_token',
    })
    def test_config_credentials(self):
        config = Config()
        assert len(config.providers) == 3
        assert 'random' not in config.providers
        assert 'dummy' in config.providers  # Telegram fallback
        assert 'socproof' in config.providers
        assert 'justanotherpanel' in config.providers

        sample = config.get_provider_config(Providers.socproof)
        assert sample['token'] == 'socproof_token'

        sample = config.get_provider_config(Providers.justanotherpanel)
        assert sample['token'] == 'justanotherpanel_token'

        sample = config.get_provider_config(Providers.dummy)
        assert sample['token'] == 'bot_token'
        assert sample['chat_id'] == '123456'


if __name__ == '__main__':
    unittest.main()
