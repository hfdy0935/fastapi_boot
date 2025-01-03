from collections.abc import Callable
from typing import Any
from fastapi import Request


async def middleware_foo(request: Request, call_next: Callable[[Request], Any]):
    print('middleware_foo before')
    resp = await call_next(request)
    print('middleware_foo after')
    return resp


async def middleware_bar(request: Request, call_next: Callable[[Request], Any]):
    print('middleware_bar before')
    resp = await call_next(request)
    print('middleware_bar after')
    return resp
