import os
from functools import cached_property

__all__ = (
    'Config',
)


class Config:
    @cached_property
    def tokens(self) -> list[str]:
        _tokens = os.environ.get('API_TOKENS', '')
        return list(filter(None, [part.strip().lower() for part in _tokens.split(',')]))

    @cached_property
    def JSONIFY_PRETTYPRINT_REGULAR(self) -> bool:
        return True

    @cached_property
    def JSON_AS_ASCII(self) -> bool:
        return False

    @cached_property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return os.environ.get('SQLALCHEMY_DATABASE_URI') \
            or os.environ.get('DATABASE_URL') \
            or 'sqlite:///:memory:'

    @cached_property
    def SQLALCHEMY_COMMIT_ON_TEARDOWN(self) -> bool:
        return False

    @cached_property
    def is_requests_colleced(self) -> bool:
        _val = os.environ.get('COLLECT_REQUESTS', '').strip()
        return bool(_val)

    @cached_property
    def providers(self) -> dict:
        return {
            'dummy': {
                'token': os.environ.get('TELEGRAM_TOKEN'),
                'chat_id': os.environ.get('TELEGRAM_CHAT_ID'),
            },
            'socproof': {
                'token': os.environ.get('SOCPROOF_TOKEN'),
            },
            'justanotherpanel': {
                'token': os.environ.get('JUSTANOTHERPANEL_TOKEN'),
            },
            'prosmmstore': {
                'token': os.environ.get('PROSMMSTORE_TOKEN'),
            },
            'fxsmmsoc': {
                'token': os.environ.get('FXSMMSOC_TOKEN'),
            }
        }

    def get_provider_config(self, provider_id) -> dict:
        return self.providers.get(provider_id.name, {})
