# pylint: disable=no-self-use
import json
import logging
import os
import sys
import typing  # pylint: disable=unused-import
import unittest
from unittest import mock  # pylint: disable=unused-import

from webhook_api.parser import parse_order, unescape_url

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class TestOrderParser(unittest.TestCase):

    def test_url_unescape(self):
        samples = [
            ('рах', '%@='),
            ('https://vk.com/club12345678?wхwall-12345678_755', 'https://vk.com/club12345678?w=wall-12345678_755'),
            ('https://www.tiktok.com/аus_er.666', 'https://www.tiktok.com/@us_er.666'),
            ('https://vk.com/southside261?zхphoto607809657_457251380р2Falbum607809657_0р2Frev', 'https://vk.com/southside261?z=photo607809657_457251380/album607809657_0/rev'),
        ]
        for escaped_url, expected_url in samples:
            assert unescape_url(escaped_url) == expected_url

    def test_problem_case(self):
        sample = '{"email":"username@gmail.com","paymentsystem":"yakassa","payment":{"sys":"yakassa","systranid":"2b2d447b-000f-5000-9999-999999999999","orderid":"1624284557","products":[{"name":"\u0423\u0441\u043b\u0443\u0433\u0430 \u0412\u041a: \u041b\u0430\u0439\u043a\u0438 \u042d\u043a\u043e\u043d\u043e\u043c: 0.33 \u0440\u0443\u0431. \/ 1 \u0448\u0442   \u0421\u0441\u044b\u043b\u043a\u0430: https:\/\/vk.com\/photo605824221_457243790  \u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e: 68","quantity":1,"amount":22.4,"price":"22.4"}],"amount":"22.4"},"formid":"form427055065","formname":"Cart","Authorization":"Bearer 16f488f0-7878-11ed-ae0a-3bffc393cabc"}'
        data = json.loads(sample)
        product = parse_order(data.get('payment').get('products')[0])
        logger.info(product)
        assert product.service_name == 'ВК: Лайки Эконом'
        assert product.price_per_unit == 0.33
        assert product.quantity == 1
        assert product.per_unit == 1
        assert product.units_amount == 68
        assert product.amount == 22.4
        assert product.is_package is False

        logger.info('Diff: %s', product.calculated_price - product.amount)
        assert product.is_payed is True

    def test_problem_case2(self):
        sample = '''{
  "email": "username@yandex.ru",
  "paymentsystem": "yakassa",
  "payment": {
    "sys": "yakassa",
    "systranid": "2b325be6-000f-5000-8000-103b4b1e435e",
    "orderid": "1613596433",
    "products": [
      {
        "name": "Услуга Telegram: 300 шт позитивных  : 84 руб. 0.28/шт вместо 0.35/шт   Ссылка: https://t.me/atmanshopp  Количество: 1 пакет",
        "quantity": 1,
        "amount": 84,
        "price": "84"
      }
    ],
    "amount": "84"
  },
  "formid": "form427055065",
  "formname": "Cart"
}'''
        data = json.loads(sample)
        product = parse_order(data.get('payment').get('products')[0])
        logger.info(product)
        assert product.service_name == 'Telegram: 300 шт позитивных'
        assert product.price_per_unit == 84
        assert product.quantity == 1
        assert product.per_unit == 0.28
        print('AMOUNT: %s', product)
        #assert product.units_amount == 1
        assert product.amount == 84
        assert product.is_package is True
        assert product.units_amount == 300

        assert product.is_payed is True, 'Actually payed'

        logger.info(product)

    def test_is_payed_case(self):
        _product = {
            "name": "Услуга ВК: Лайки Эконом: 0.33 руб. / 1 шт   Ссылка: https://vk.com/wall-215968286_46  Количество: 95",
            "quantity": 1,
            "amount": 31,
            "price": "31"
        }

        order = parse_order(_product)
        assert order.is_payed is True
        print(order)
        print(f'{order.is_payed=}')
        print(f'{order.is_package=}')
        print(f'{order.calculated_price=}')

    def test_not_payed_(self):
        _product = {
            "name": "Услуга Telegram: Подписчики Эконом: 0.52 руб. / 1 шт   Ссылка: https://t.me/napodbor_channel  Количество: 1200",
            "quantity": 1,
            "amount": 52,
            "price": "52"
        }
        order = parse_order(_product)
        assert order.is_payed is False

    def test_package_other(self):
        _product = {
            'name': 'Услуга Telegram: 1000 просм. на 10 посл. постов: 120 руб. 0.12/шт вместо 0.17/шт   Ссылка: https://t.me/medicinskoedelo  Количество: 1 пакет',
            'quantity': 1,
            'amount': 120,
            'price': '120'
        }

        order = parse_order(_product)
        assert order.is_payed is True
        assert order.is_package is True
        assert order.quantity == 1
        assert order.units_amount == 1000
        assert order.service_name == 'Telegram: 1000 просм. на 10 посл. постов'

    def test_package_other_2(self):
        _product = {
            'name': 'Услуга Telegram: Премиум 2000 подп: 1280 руб. 0.64/шт вместо 0.8/шт   Ссылка: https://t.me/medicinskoedelo  Количество: 1 пакет',
            'quantity': 1,
            'amount': 1280,
            'price': '1280'
        }
        order = parse_order(_product)
        assert order.is_payed is True
        assert order.is_package is True
        assert order.quantity == 1
        assert order.units_amount == 2000
        assert order.service_name == 'Telegram: Премиум 2000 подп'


if __name__ == '__main__':
    unittest.main()
