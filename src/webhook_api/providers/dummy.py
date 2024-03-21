import requests

from ..models import OrderEntry


class TelegramClient:
    BASE_URL = 'https://partner.soc-proof.su/api/v2'

    def __init__(self, token: str):
        self._token = token

    def send_message(self, chat_id, text):
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
        }
        resp = requests.post(f'https://api.telegram.org/bot{self._token}/sendMessage', json=payload)
        return resp.json()


class DummyProvider:
    '''Dummy provider. Used as fallback with echo to Telegram'''

    def __init__(self, config) -> None:
        self._config = config
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = TelegramClient(self.token)
        return self._client

    @property
    def token(self):
        return self._config.get('token')

    @property
    def chat_id(self):
        return self._config.get('chat_id')

    def describe(self, details: OrderEntry):
        text = f'''
<b>Order entry:</b> {details.entry_id}
<b>Service name:</b> <code>{details.service_name}</code> ({details.provider_id.name}:{details.service_id})
<b>Is payed:</b> {details.is_payed} ; <b>Is package:</b> {details.is_package}

<b>Invokation details:</b>
<pre>provider={details.provider_id.name}
service_id={details.service_id}
quantity={round(details.quantity * details.units_amount)} ({str(details.quantity) + ' * ' + str(details.units_amount)})
link={details.url}
</pre>
---
<pre>{details.name}</pre>
#{details.provider_id.name} #{details.order.payment_system.replace('.', '_')} {'#payed' if details.is_payed else '#not_payed'} #service_id{details.service_id} {'#package' if details.is_package else ''}
'''
        data = self.client.send_message(self.chat_id, text)

    def make_order(self, details: OrderEntry):
        text = f'''
<b>Service name:</b> <code>{details.service_name}</code>

-----
<b>Is package</b>: {details.is_package}
<b>Is payed</b>: {details.is_payed}
<b>OrderID</b>: {details.entry_id}
<b>URL</b>: {details.url}
<b>Price per unit</b>: {details.price_per_unit}


-----
<pre>{details.name}</pre>
            '''

        data = self.client.send_message(self.chat_id, text)
        return data.get('result', {}).get('message_id')
