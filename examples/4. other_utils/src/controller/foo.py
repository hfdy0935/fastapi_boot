from dataclasses import asdict, dataclass
from functools import lru_cache
import time
from typing import Any, Callable, Coroutine
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket
from fastapi_boot.core import (
    Controller,
    use_http_middleware,
    Get,
    use_ws_middleware,
    WS,
    Prefix,
    Post,
    Bean,
    inject_app,
    HTTPMiddleware,
    ExceptionHandler,
    use_dep,
    Lifespan,
    Lazy,
    Inject,
)


# ---------------------------------------------------- middleware ---------------------------------------------------- #
async def mid1(request: Request, call_next: Callable[[Request], Coroutine]):
    print('before mid1')
    resp = await call_next(request)
    print('after mid1')
    return resp


async def mid2(request: Request, call_next: Callable[[Request], Coroutine]):
    print('before mid2')
    resp = await call_next(request)
    print('after mid2')
    return resp


async def mid3(websocket: WebSocket, call_next: Callable[[WebSocket], Coroutine]):
    print('before mid3')
    await call_next(websocket)
    print('after mid3')


@HTTPMiddleware  # global http middleware
async def mid4(request: Request, call_next: Callable[[Request], Coroutine]):
    print('before mid4')
    resp = await call_next(request)
    print('after mid4')
    return resp


# ------------------------------------------------- ExceptionHandler ------------------------------------------------- #


@dataclass
class GuessException(Exception):
    code: int = 500
    msg: str = 'server error'


@ExceptionHandler(GuessException)
async def handle_exp_1(request: Request, exp: GuessException):
    print('guess exception 501')
    return {**asdict(exp), 'time': time.ctime()}


@ExceptionHandler(501)
async def handle_exp_2(request: Request, exp: HTTPException):
    print('guess exception 502')
    return {'status': exp.status_code, 'msg': exp.detail, 'time': time.ctime()}


def guess_dep(p: int = Query()):
    if p > 20:
        raise HTTPException(501, 'too large')


# ------------------------------------------------------- model ------------------------------------------------------ #
@dataclass
class DBData:
    conn: Any = None
    db_info: str = ''


# ---------------------------------------------------- Controller ---------------------------------------------------- #


@Controller('/otehr-decorators', tags=['6. other decorators'])
class _:
    # we don't care the result which is a placeholder as identity for fastapi-boot, just use the middleware
    # only has effect to http method
    _ = use_http_middleware(mid1, mid2)

    @Get()
    def f(self):
        print('endpoint')
        # The output should be  before mid5 > before mid1 > before mid2 > before mid4 > endpoint > before mid4 > after mid2 > after mid1 > before mid5
        return True

    @Prefix()
    class prefix:
        _ = use_http_middleware(mid2, mid1)

        @Post()
        def f(self):
            print('endpoint')
            # The output should be  before mid5 > before mid2 > before mid1 > before mid4 > endpoint > before mid4 > after mid1 > after mid2 > before mid5
            return True

    @Prefix('/ws')
    class ws:  # frontend: resource/single-websocket.html
        # default False, any message avent can emit `mid3`. If True, only message event will emit `mid3`
        # only has effect to websocket
        _ = use_ws_middleware(mid3, only_message=True)

        @WS()
        async def f(self, websocket: WebSocket):
            try:
                await websocket.accept()
                while True:
                    data = await websocket.receive_json()
                    # before mid3
                    await websocket.send_json(data)
                    # after mid3
            except:
                pass

    @Prefix('/exp-handler-demo')
    class ExpHandlerDemo:
        _ = use_dep(guess_dep)

        @Get()
        def f(self, p: int = Query(description='guess a number')):
            if p < 10:
                raise GuessException(600, 'too small')
            return dict(code=200, msg='success', data=p)

    @Prefix('/lifespan-bean')
    class LefespaBean:
        # late inject, equals peoperty and lru_cache
        db_data = Lazy(lambda: Inject(DBData))

        @property
        @lru_cache(None)
        def db_data1(self):
            return Inject(DBData)

        @Get('query-db', response_model=dict)
        def f(self):
            result = self.db_data.db_info + ' query result'
            assert self.db_data == self.db_data1
            return dict(code=200, msg='success', data=result)


@HTTPMiddleware  # global http middleware, after Controller
class Mid5Middleware:
    async def dispatch(self, request: Request, call_next: Callable):
        print('before mid5')
        res = await call_next(request)
        print('after mid5')
        return res


# ---------------------------------------------------- Lifespan ---------------------------------------------------- #
class DB:
    async def connect(self, app: FastAPI): ...
    async def disconnect(self): ...

    @property
    def some_data(self):
        return DBData('db connected')


@Lifespan
async def lifespan(app: FastAPI):
    assert app == inject_app()

    db = DB()
    await db.connect(app)
    # Bean created after scanning and before app starting

    @Bean
    def f() -> DBData:
        return db.some_data

    yield
    await db.disconnect()


@inject_app().post('/inject-app-router', tags=['6. other decorators'])
async def inject_app_router():
    return 'ok'
