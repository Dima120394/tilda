import time
from functools import wraps

from ..log import logger

__all__ = (
    'retry_on_failure',
)


def retry_on_failure(attempts: int = 2, delay: float = 0.2):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            message = ''
            for _ in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if 'Invalid API key' in str(exc):
                        logger.error('>>> Invalid API key: %s', exc)
                        raise exc
                    logger.warning('exc: %s', exc, exc_info=exc)
                    message = str(exc)
                    time.sleep(delay)
            raise Exception(f'Attempts limit exceeded: {message}')
        return wrapped
    return wrapper
