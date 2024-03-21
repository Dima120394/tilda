from functools import wraps
from http import HTTPStatus
from typing import Callable

from flask import current_app, jsonify, request

__all__ = (
    'auth_required',
)


def auth_required(_tokens) -> Callable:
    def _wrapper(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_app.logger.info(request.headers)
            _raw = request.headers.get('Authorization', '')
            try:
                scheme, token = [part.strip().lower() for part in f'{_raw} '.split(' ', 1)]
                if scheme != 'bearer' \
                        or not token or token not in _tokens:
                    raise Exception('Auth REQUIRED')
            except Exception:
                return jsonify({
                    'status': 'error',
                    'message': 'auth REQUIRED',
                }), HTTPStatus.BAD_REQUEST
            return f(*args, **kwargs)
        return decorated_function
    return _wrapper
