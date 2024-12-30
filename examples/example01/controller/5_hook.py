import logging
import time
from uuid import uuid4

from fastapi import Header, HTTPException, Request
from fastapi_boot.core import Controller, Get, Post, Prefix, use_dep, use_http_middleware
from middleware.handler import middleware_bar, middleware_foo

logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s  %(message)s')

white_list = ['1a2b3c', '4d5e6f']


def write_log(request: Request):
    message = {
        'url': request.url,
        'method': request.method,
        'time': time.time(),
        'user-agent': request.headers.get('user-agent'),
        'host': request.headers.get('host'),
    }
    logging.info(message)


SESSION_KEY = 'xxx'


def get_session(request: Request):
    return request.session


def need_login(token: str = Header()):
    if not token in white_list:
        raise HTTPException(status_code=401, detail='unAuthorization')
    return token


@Controller('/hook', tags=['5. hook'])
class _:
    session = use_dep(get_session)
    _ = use_dep(write_log)  # no return, use _ as a placeholder
    __ = use_http_middleware(middleware_foo, middleware_bar)
    # middleware_bar before  >>  middleware_foo before  >>  write_log  >>  middleware_foo after  >>  middleware_bar after

    @Get()
    def get(self):
        self.session.update({SESSION_KEY: str(uuid4())})

    @Post()
    def post(self):
        return self.session.get(SESSION_KEY)

    @Prefix()
    class NeedLoginPrefix:
        token = use_dep(need_login)
        __ = use_http_middleware(middleware_bar)

        @Post('/after-login')
        def post(self):
            return self.token
