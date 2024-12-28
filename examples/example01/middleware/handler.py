from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request, Response, WebSocket

from fastapi_boot import HTTPMiddleware


async def middleware_foo(request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]):
    print('middleware_foo before')
    resp = await call_next(request)
    print('middleware_foo after')
    return resp


async def middleware_bar(request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]):
    print('middleware_bar before')
    resp = await call_next(request)
    print('middleware_bar after')
    return resp


async def middleware_ws_foo(websocket: WebSocket, call_next: Callable):
    print('before ws send data foo')
    res = await call_next(websocket)
    print('after ws send data foo')
    return res


async def middleware_ws_bar(websocket: WebSocket, call_next: Callable):
    print('before ws send data bar')
    res = await call_next()
    print('after ws send data bar')
    return res


@HTTPMiddleware
async def globalMiddleware(request: Request, call_next: Callable[..., Coroutine]):
    print('global middleware before')
    resp = await call_next(request)
    print('global middleware after')
    return resp
