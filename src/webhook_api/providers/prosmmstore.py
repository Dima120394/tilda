import json
from typing import List

import requests

from ..models import OrderEntry

__all__ = (
    'ProSMMStoreProvider',
    'ProSMMStoreAPI',
)

from ..log import logger
from .utils import retry_on_failure


class ProSMMStoreAPI:
    '''
    https://prosmm-store.com/api
    '''
    BASE_URL = 'https://prosmm-store.com/api/v2'

    def __init__(self, token):
        self._token = token

    def _invoke(self, payload):
        _payload = {
            'key': self._token
        }
        _payload.update(payload)
        resp = requests.post(
            self.BASE_URL,
            data=_payload,
            verify=False,
            timeout=5,
        )
        try:
            resp.raise_for_status()
            data = resp.json()
            if 'error' in data:
                raise Exception(data.get('error'))
            return resp.json()
        except Exception as exc:
            logger.error('ProSMMStore API error: %s', exc, exc_info=exc)
            raise exc

    def status(self, order_id: str):
        return self._invoke({
            'action': 'status',
            'order': str(order_id),
        })

    def multi_status(self, order_ids: List[str]):
        return self._invoke({
            'action': 'status',
            'orders': ','.join(str(order_id) for order_id in order_ids),
        })

    def services(self):
        return self._invoke({
            'action': 'services',
        })

    def balance(self):
        return self._invoke({
            'action': 'balance',
        })

    @retry_on_failure()
    def order(self, link: str, service_id: str, quantity: int):
        return self._invoke({
            'action': 'add',
            'service': service_id,
            'quantity': quantity,
            'link': link,
        })


class ProSMMStoreProvider:
    def __init__(self, config: str) -> None:
        self._config = config
        self._client = None

    @property
    def token(self) -> str:
        return self._config.get('token')

    @property
    def client(self):
        if self._client is None:
            self._client = ProSMMStoreAPI(self.token)
        return self._client

    def make_order(self, details: OrderEntry):
        logger.info(details)
        resp = self.client.order(
            link=details.url,
            service_id=details.service_id,
            quantity=round(details.units_amount * details.quantity),
        )
        order_id = resp.get('order')
        if order_id is None:
            logger.error(resp.get('error'))
        return resp.get('order')
