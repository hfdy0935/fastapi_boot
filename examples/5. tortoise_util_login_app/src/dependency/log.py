import logging
import time

from fastapi import Request


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s  %(levelname)s  %(message)s')


def write_log(request: Request):
    message = {
        'url': request.url,
        'method': request.method,
        'time': time.time(),
        'user-agent': request.headers.get('user-agent'),
        'host': request.headers.get('host'),
    }
    logging.info(message)
