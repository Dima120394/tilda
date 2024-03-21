import dataclasses
import re

from .log import logger

__all__ = (
    'unescape_url',
)


@dataclasses.dataclass()
class OrderDetails:
    raw_entry: str
    service_name: str
    price_per_unit: float
    per_unit: float
    url: str
    amount: int
    order_amount: int
    order_price: float
    price_total: float
    is_package: bool = False

    @property
    def calculated_price(self) -> float:
        return round(self.order_amount * self.price_per_unit * self.amount, 2)

    @property
    def is_payed(self) -> bool:
        return self.price_total >= self.calculated_price


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
    return buff


ORDER_TYPES = {
    'service_name': lambda service: service.strip(' :'),
    'price_per_unit': float,
    'per_unit': float,
    'url': unescape_url,
    'amount': int,
    'order_amount': int,
    'order_price': float,
    'price_total': float,
    'is_package': lambda x: x is not None
}

ORDER_RE = re.compile(r'^Услуга:? (?P<service_name>.+?) (?P<price_per_unit>[\d.]+) руб\. / (?P<per_unit>[\d.]+) шт[ ]*'
                      r'Ссылка: (?P<url>.+?)[ ]*'
                      r'Количество: (?P<amount>[\d.]+) - (?P<order_amount>\d+)x(?P<order_price>[\d.]+) = (?P<price_total>[\d.]+)$')

ORDER_RE = re.compile(r'^Услуга:? (?P<service_name>.+?) '
                      r'('
                      r'(?P<price_per_unit>[\d.]+) руб\. / (?P<per_unit>[\d.]+) шт[ ]*'
                      r'|'
                      r'(?P<price_per_unit1>[\d.]+) руб\..*(?P<per_unit1>[\d.]+)/шт вместо (?:[\d.]+)/шт[ ]*[ ]*'
                      r')'
                      r'Ссылка: (?P<url>.+?)[ ]*'
                      r'Количество: '
                      r'(?P<amount>[\d.]+) (?P<is_package>пакет )?- (?P<order_amount>\d+)x(?P<order_price>[\d.]+) = (?P<price_total>[\d.]+)$')


def parse_order(order_raw: str) -> OrderDetails:
    # Услуга: ВК: Подписчики Премиум: 1.68 руб. / 1 шт   Ссылка: https://vk.com/public217057222  Количество: 575 - 1x966 = 966;
    # data = re.search(r'^Услуга: (?P<service_name>.+?) (?P<price_per_unit>[\d.]+) руб\. / (?P<per_unit>[\d.]+) шт[ ]*Ссылка: (?P<url>.+?)[ ]*Количество: (?P<amount>[\d.]+) - (?P<order_amount>\d+)x(?P<order_price>[\d.]+) = (?P<price_total>[\d.]+)$', order_raw)
    m = ORDER_RE.search(order_raw)
    print(m)
    if m is None:
        return None
    # print(order_raw)
    # print(m.groupdict())
    data = m.groupdict()
    price_per_unit = data.get('price_per_unit1') or data.get('price_per_unit')
    per_unit = data.get('per_unit1') or data.get('per_unit')
    data.update({
        'price_per_unit': price_per_unit,
        'per_unit': per_unit,
    })
    del data['price_per_unit1']
    del data['per_unit1']
    print(data)
    try:
        for prop, value in data.items():
            data[prop] = ORDER_TYPES.get(prop, str)(value)
    except Exception as exc:
        logger.error('Unable to parse order entry: %s', exc, exc_info=exc)
        return None
    order = OrderDetails(raw_entry=order_raw, **data)
    return order


def parse_raw_orders(orders_raw: str) -> list[OrderDetails]:
    orders = []
    raw_orders = [f'Услуга:{line}'.strip() for line in re.split(r'(?:^Услуга|; Услуга)', orders_raw) if len(line)]

    for p in raw_orders:
        _order = parse_order(p)
        if _order is not None:
            orders.append(_order)
    # print(len(raw_orders))
    # assert len(raw_orders) == 33
    return orders


def main():
    sample = 'Услуга ВК: Подписчики Премиум: 1.68 руб. / 1 шт   Ссылка: https://vk.com/public217057222  Количество: 575 - 1x966 = 966; Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_11  Количество: 95 - 1x95 = 95; Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_10  Количество: 70 - 1x70 = 70; Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_9  Количество: 145 - 1x73 = 73; Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_8  Количество: 95 - 1x48 = 48; Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_7  Количество: 95 - 1x48 = 48; Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_6  Количество: 120 - 1x60 = 60; Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_5  Количество: 145 - 1x73 = 73; Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_4  Количество: 120 - 1x60 = 60; Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_3  Количество: 95 - 1x48 = 48; Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_2  Количество: 120 - 1x120 = 120; Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_1  Количество: 120 - 1x120 = 120; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_11  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_10  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_9  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_8  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_7  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_6  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_5  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_4  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_3  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_2  Количество: 150 - 1x26 = 26; Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_1  Количество: 150 - 1x26 = 26; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_11  Количество: 21 - 1x39.9 = 39.9; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_10  Количество: 16 - 1x30.4 = 30.4; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_9  Количество: 15 - 1x28.5 = 28.5; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_8  Количество: 12 - 1x22.8 = 22.8; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_7  Количество: 11 - 1x20.9 = 20.9; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_6  Количество: 13 - 1x24.7 = 24.7; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_5  Количество: 14 - 1x26.6 = 26.6; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_4  Количество: 10 - 1x19 = 19; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_3  Количество: 11 - 1x20.9 = 20.9; Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_2  Количество: 16 - 1x30.4 = 30.4'
    details = parse_raw_orders(sample)


if __name__ == '__main__':
    main()
