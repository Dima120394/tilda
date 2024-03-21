import json
import logging
import typing
import uuid
from dataclasses import asdict
from functools import wraps
from http import HTTPStatus

import flask
from flask import Flask, current_app, g, jsonify, request
from flask_cors import CORS, cross_origin

from .config import Config
from .decorators import auth_required
from .ext import db
from .models import (Order, OrderEntry, OrderEntryState, Providers,
                     RequestLogEntry, ServiceDescription)
from .order_parser import parse_raw_orders
from .parser import OrderProductDetails, parse_order
from .providers import get_provider, is_valid_row, resolve_provider
from .providers.dummy import DummyProvider


def create_app() -> Flask:
    '''Flask app factory'''
    config = Config()
    app = Flask(__name__)
    app.config.from_object(config)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = app.debug

    # app.logger.info(config.tokens)
    db.init_app(app)
    # Configure logger
    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers.extend(gunicorn_error_logger.handlers)
    # app.logger.setLevel(logging.DEBUG)

    with app.app_context() as ctx:
        db.create_all()

    # Configure CORS headers
    # Restrict access
    cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

    @app.get('/favicon.ico')
    def favicon_handler():
        return '', HTTPStatus.NO_CONTENT

    @app.get('/')
    def index_page():
        return jsonify({'status': 'ok'}), HTTPStatus.OK

    @app.post('/api/v1/webhook')
    def api_v1_webhook():
        # Handle platform test request
        # TODO: fix state problem: 1624284557
        #
        # Log each request
        if config.is_requests_colleced:
            current_app.logger.info('Storing raw request data')
            db.session.add(RequestLogEntry(
                raw_data=request.get_data(as_text=True),
                content_type=request.headers.get('content-type')
            ))
            db.session.commit()

        # Handle test webhook invokation
        if 'test' in request.json:
            current_app.logger.info('Got test callback')
            return jsonify({'status': 'ok'}), HTTPStatus.OK

        current_app.logger.info(
            json.dumps(request.json, indent=2, ensure_ascii=False)
        )

        payment = request.json.get('payment')
        order_id = payment.get('orderid', 'dummy_' + str(uuid.uuid4()))
        if app.debug:
            import pathlib
            sink_dir = pathlib.Path('/tmp/dumps/')
            sink_dir.mkdir(parents=True, exist_ok=True)
            with open(sink_dir / f'{order_id}.json', 'wb') as fp:
                fp.write(request.data)

        # Skip if order already commited;
        order = db.session.execute(
            db.select(Order).filter_by(order_id=order_id)
        ).first()
        if order is not None:
            return jsonify({
                'status': 'error',
                'message': 'Already exists',
                'orderId': order_id,
            }), HTTPStatus.CONFLICT

        # Store Order record
        try:
            # freekassa's transaction id == '0'
            # TODO: this is quick fix
            _systranid = payment.get('systranid')
            _systranid = '_' + str(uuid.uuid4()) if _systranid == '0' else _systranid
            order = Order(
                order_id=payment.get('orderid'),
                email=request.json.get('email'),
                payment_system=payment.get('sys'),
                systran_id=_systranid,
                orders_amount=len(payment.get('products', [])),
                raw_data=request.get_data(as_text=True),
            )
            db.session.add(order)
            db.session.commit()
        except Exception as exc:
            current_app.logger.error('Unable to commit order: %s', exc, exc_info=exc)
            return flask.jsonify({
                'status': 'error',
                'message': 'Unable to commit order',
                'details': str(exc),
                'orderId': order_id,
            }), HTTPStatus.BAD_REQUEST

        # And Order Entries (Products. 1 or more)
        order_products = []
        try:
            for n, _raw_product in enumerate(payment.get('products')):
                _product = parse_order(_raw_product)
                _order_entry = OrderEntry(
                    order=order,
                    entry_id=f'{order.order_id}-{n}',
                    state=_product.state,
                    is_payed=_product.is_payed,
                    **asdict(_product)
                )
                order_products.append(_order_entry)
                db.session.add(_order_entry)
            db.session.commit()

        except Exception as exc:
            current_app.logger.error('Unable to commit order entries: %s', exc, exc_info=exc)
            db.session.rollback()

            return flask.jsonify({
                'status': 'error',
                'message': 'Unable to commit order entries',
                'details': str(exc),
                'orderId': order_id,
            }), HTTPStatus.BAD_REQUEST

        # Process order entries
        # Invoke service provider
        providers_index = ServiceDescription.get_index()
        _product: OrderEntry
        for _product in order_products:
            # Normally not payed requests should be skipped asap
            # if _product.state != OrderEntryState.created:
            #    current_app.logger.info('Skipping product: %s', _product.entry_id)
            #    continue
            commited_id = None
            state = _product.state
            try:
                provider_details = resolve_provider(str(_product.service_name).lower(), providers_index)
                _product.service_id = provider_details.service_id
                _product.provider_id = provider_details.provider_id
                current_app.logger.info('Order=%s provider=%s', _product.entry_id, provider_details)
                Provider = get_provider(provider_details.provider_id)
                provider = Provider(config.get_provider_config(provider_details.provider_id))
                notifier = DummyProvider(config.get_provider_config(Providers.dummy))
                notifier.describe(_product)

                # Process if product payed
                if _product.is_payed:
                    commited_id = provider.make_order(_product)
                # Mark as fulfiled if payed and executed (commited_id received)
                if _product.is_payed and commited_id is not None:
                    state = OrderEntryState.fulfilled
                current_app.logger.info('Commited ID: %s', commited_id)
            except Exception as exc:
                if 'Invalid API key' in str(exc):
                    current_app.logger.error('API KEY REQUIRED')
                else:
                    current_app.logger.error('Unable to commit order: %s', exc, exc_info=exc)
                current_app.logger.error('Details: %s', _product)
                state = OrderEntryState.failed
                _product.error_hint = str(exc)
            _product.state = state
            _product.provider_order_id = commited_id

            db.session.add(_product)
        db.session.commit()

        return jsonify({
            'status': 'ok',
            'result': {
                'orderId': order_id,
            },
        }), HTTPStatus.OK

    @app.post('/api/v1/status')
    def api_v1_status():
        '''Check order status'''
        data = request.json
        order_id = data.get('orderId')
        if order_id is None:
            return jsonify({
                'status': 'error',
                'message': 'Bad request. orderId missing',
            }), HTTPStatus.BAD_REQUEST

        order = db.session.execute(
            db.select(Order)
            .filter_by(order_id=str(order_id))
            .options(db.lazyload(Order.orders))
        ).first()
        if order is None:
            return jsonify({
                'status': 'ok',
                'result': 'Not found'
            }), HTTPStatus.NOT_FOUND

        order = order[0]

        return jsonify({
            'status': 'ok',
            'result': {
                'orderId': order.order_id,
                'entries': [
                    {
                        'entryId': _product.entry_id,
                        'state': str(_product.state.name),
                        'message': str(_product.error_hint or ''),
                    }
                    for _product in order.orders
                ],
                'createdAt': order.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'total': order.orders_amount
            }
        }), HTTPStatus.OK

    @auth_required(config.tokens)
    @app.post('/api/v1/updateServices')
    def api_v1_update_services():
        '''Handle service configurations from Google Sheets'''
        data = request.json
        _index = {}
        updates = []
        for row in data:
            if is_valid_row(row):
                _service_name = str(row[0]).lower()
                if _service_name not in updates:
                    updates.append(row)
                    _index[_service_name] = 1
        try:
            ServiceDescription.query.delete()
            for service_name, service_id, provider_id in updates:
                db.session.add(ServiceDescription(
                    service_name=str(service_name).lower().strip(),
                    service_id=service_id,
                    provider_id=Providers[provider_id]))
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error('Unable to commit: %s', exc, exc_info=exc)
            return jsonify({
                'status': 'error',
                'message': f'Unable to commit changes: {exc}'
            }), HTTPStatus.BAD_REQUEST
        return jsonify({
            'status': 'ok'
        }), HTTPStatus.OK

    return app
