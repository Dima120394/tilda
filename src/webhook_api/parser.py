import dataclasses
import math
import re
from urllib.parse import unquote

__all__ = (
    'parse_order',
    'OrderProductDetails',
)
import functools

try:
    from .log import logger
    from .models import OrderEntryState
except ImportError:
    from webhook_api.log import logger
    from webhook_api.models import OrderEntryState

ESCAPE_MAPPING = [
    ('[', '%'),
    ('~', '@'),
    ('}', '='),
]

ESCAPE_MAPPING = [
    ('р', '%'),
    ('а', '@'),
    ('х', '='),
]


def unescape_url(raw_url: str) -> str:
    buff = raw_url.strip()
    for esc, unsec in ESCAPE_MAPPING:
        buff = buff.replace(esc, unsec)
    return unquote(buff)


PRODUCT_TYPES = {
    'service_name': lambda service: service.strip(':').strip(' '),
    'price_per_unit': float,
    'per_unit': float,
    'url': unescape_url,
    'amount': float,
    'order_amount': int,
    'order_price': float,
    'price_total': float,
    'is_package': bool,
    'quantity': float,
    'price': float,
    'units_amount': float,
}
# "Услуга ВК: Лайки Эконом: 0.33 руб. / 1 шт   Ссылка: https://vk.com/photo-217356953_457239069?access_keyх25abee02487126647c  Количество: 75",
# "Услуга Telegram: 300 шт позитивных  : 84 руб. 0.28/шт вместо 0.35/шт   Ссылка: https://t.me/atmanshopp  Количество: 1 пакет",

PRODUCT_RE = re.compile(
    r'^Услуга:? (?P<service_name>.+?): '
    r'('
    r'(?P<price_per_unit>[\d.]+) руб\. / (?P<per_unit>[\d.]+) шт[ ]*'
    r'|'
    r'(?P<price_per_unit1>[\d.]+) руб\.[ ]*(?P<per_unit1>[\d.]+)/шт вместо (?:[\d.]+)/шт[ ]*'
    r')'
    r'Ссылка: (?P<url>.+?)[ ]*'
    r'Количество: (?P<units_amount>[\d.]+)( пакет)?$'
)


@dataclasses.dataclass()
class OrderProductDetails:
    service_name: str
    name: str
    url: str
    price_per_unit: float
    per_unit: float
    units_amount: float
    quantity: float
    amount: float
    price: float
    is_package: bool

    @functools.cached_property
    def calculated_price(self) -> float:
        if self.is_package:
            price = self.price_per_unit * self.quantity
        else:
            price = self.price_per_unit * self.units_amount * self.quantity
        return round(price, 2)

    @functools.cached_property
    def is_payed(self) -> bool:
        '''Tilda's payment info fix ...'''
        return (self.amount >= self.calculated_price) \
            or math.floor(self.amount) == math.floor(self.calculated_price) \
            or (abs(self.amount - self.calculated_price) <= 1)

    @property
    def state(self) -> OrderEntryState:
        state = OrderEntryState.created
        if not self.is_payed:
            state = OrderEntryState.not_payed
        return state


def parse_order(_product) -> OrderProductDetails:
    m = PRODUCT_RE.search(_product.get('name'))
    if m is None:
        return None
    data = m.groupdict()
    # Handle package
    is_package = data.get('price_per_unit1') is not None
    price_per_unit = data.get('price_per_unit1') or data.get('price_per_unit')
    per_unit = data.get('per_unit1') or data.get('per_unit')
    data.update({
        'price_per_unit': price_per_unit,
        'per_unit': per_unit,
        'is_package': is_package,
    })
    data.update(_product)
    del data['price_per_unit1']
    del data['per_unit1']
    if data['is_package']:
        units_amount = re.search(r'(\d.)+', data.get('service_name', ''))[0]
        data['units_amount'] = units_amount
    try:
        for prop, value in data.items():
            data[prop] = PRODUCT_TYPES.get(prop, str)(value)
    except Exception as exc:
        logger.error('Unable to parse order entry: %s', exc, exc_info=exc)
        return None
    details = OrderProductDetails(**data)

    return details


def main():
    _product = {
        "name": "Услуга ВК: Лайки Эконом: 0.33 руб. / 1 шт   Ссылка: https://vk.com/photo-217356953_457239069?access_keyх25abee02487126647c  Количество: 75",
                "quantity": 1,
                "amount": 24.8,
                "price": "24.8"
    }
    order = parse_order(_product)

    print(order)
    print(f'{order.is_payed=}')
    print(f'{order.calculated_price=}')

    _product = {
        "name": "Услуга Telegram: 300 шт позитивных  : 84 руб. 0.28/шт вместо 0.35/шт   Ссылка: https://t.me/atmanshopp  Количество: 1 пакет",
        "quantity": 1,
        "amount": 84,
        "price": "84"
    }
    order = parse_order(_product)

    print(order)
    print(f'{order.is_payed=}')
    print(f'{order.is_package=}')
    print(f'{order.calculated_price=}')


if __name__ == '__main__':
    main()
