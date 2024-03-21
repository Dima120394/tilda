# pylint: disable=no-self-use
import logging
import os
import sys
import typing  # pylint: disable=unused-import
import unittest
from unittest import mock  # pylint: disable=unused-import

from webhook_api.order_parser import (OrderDetails, parse_order,
                                      parse_raw_orders, unescape_url)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class TestOrderParser(unittest.TestCase):
    '''This is legacy code. Initial order info parser'''

    def test_url_unescape(self):
        samples = [
            ('рах', '%@='),
            ('https://vk.com/club12345678?wхwall-12345678_755', 'https://vk.com/club12345678?w=wall-12345678_755'),
            ('https://www.tiktok.com/аus_er.666', 'https://www.tiktok.com/@us_er.666'),
        ]
        for escaped_url, expected_url in samples:
            assert unescape_url(escaped_url) == expected_url

    def test_package_order(self):
        sample = 'Услуга Telegram: Премиум 1000 подп: 720 руб. 0.72/шт вместо 0.8/шт   Ссылка: https://t.me/Fonbetdo1000000  Количество: 1 пакет - 1x720 = 720'
        orders = parse_raw_orders(sample)
        assert len(orders) == 1
        order = orders[0]
        assert order.is_payed is True
        assert order.is_package is True
        assert order.price_total >= order.calculated_price

    def test_parse_incorrect(self):
        samples = [
            (1, 'Услуга Telegram: Подписчики Премиум: 0.8 руб. / 1 шт   Ссылка: https://t.me/+zrlFadQFbnw0M2Fk  Количество: 550 - 1x286 = 286'),
        ]
        for expected_amount, sample in samples:
            orders: list[OrderDetails] = parse_raw_orders(sample)
            assert len(orders) == expected_amount
            logger.info('%s = %s', orders[0].price_total, orders[0].calculated_price)
            assert orders[0].is_payed is False

    def test_parse_valid_order(self):
        order = parse_order('Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_3  Количество: 95 - 1x48 = 48')
        logger.info(order)
        assert order.is_payed is True
        assert order.is_package is False

    def test_parse_emoji(self):
        sample = 'Услуга Telegram: Случайные, позитив  : 0.35 руб. / 1 шт   Ссылка: https://t.me/Raim_Sneakers_Shop/75  Количество: 50 - 1x17.5 = 17.5'
        order = parse_order(sample)
        assert order.is_package is False
        logger.info(order)

    def test_parse_multiline(self):
        sample = ' '.join('''Услуга ВК: Подписчики Премиум: 1.68 руб. / 1 шт   Ссылка: https://vk.com/public217057222  Количество: 575 - 1x966 = 966;
Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_11  Количество: 95 - 1x95 = 95;
Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_10  Количество: 70 - 1x70 = 70;
Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_9  Количество: 145 - 1x73 = 73;
Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_8  Количество: 95 - 1x48 = 48;
Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_7  Количество: 95 - 1x48 = 48;
Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_6  Количество: 120 - 1x60 = 60;
Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_5  Количество: 145 - 1x73 = 73;
Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_4  Количество: 120 - 1x60 = 60;
Услуга ВК: Лайки Стандарт: 0.5 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_3  Количество: 95 - 1x48 = 48;
Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_2  Количество: 120 - 1x120 = 120;
Услуга ВК: Лайки Премиум: 1 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_1  Количество: 120 - 1x120 = 120;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_11  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_10  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_9  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_8  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_7  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_6  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_5  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_4  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_3  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_2  Количество: 150 - 1x26 = 26;
Услуга ВК: Просмотры записи: 0.17 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_1  Количество: 150 - 1x26 = 26;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_11  Количество: 21 - 1x39.9 = 39.9;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_10  Количество: 16 - 1x30.4 = 30.4;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_9  Количество: 15 - 1x28.5 = 28.5;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_8  Количество: 12 - 1x22.8 = 22.8;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_7  Количество: 11 - 1x20.9 = 20.9;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_6  Количество: 13 - 1x24.7 = 24.7;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_5  Количество: 14 - 1x26.6 = 26.6;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_4  Количество: 10 - 1x19 = 19;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_3  Количество: 11 - 1x20.9 = 20.9;
Услуга ВК: Живые репосты: 1.9 руб. / 1 шт   Ссылка: https://vk.com/wall-217057222_2  Количество: 16 - 1x30.4 = 30.4
'''.split('\n'))

        orders = parse_raw_orders(sample)
        assert len(orders) == 33
        assert all([order.is_payed and not order.is_package for order in orders])


if __name__ == '__main__':
    unittest.main()
