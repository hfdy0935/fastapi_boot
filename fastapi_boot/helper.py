import concurrent
import concurrent.futures
from dataclasses import asdict, is_dataclass
import os
from collections.abc import  Callable, Coroutine
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
import sys
from typing import Any, TypeVar
from inspect import iscoroutinefunction
from pydantic import BaseModel

from fastapi import Depends, FastAPI, Request, Response, WebSocket

from fastapi.responses import JSONResponse
from fastapi_boot.const import REQ_DEP_PLACEHOLDER, USE_MIDDLEWARE_FIELD_PLACEHOLDER,EXCEPTION_HANDLER_PRIORITY, BlankPlaceholder, app_store, task_store,dep_store
from fastapi_boot.model import AppRecord,UseMiddlewareRecord
from fastapi_boot.util import get_call_filename
T = TypeVar('T')


def use_dep(dependency: Callable[..., T|Coroutine[Any,Any,T]] | None, use_cache: bool = True) -> T:
    """Depends of FastAPI with type hint
    - use it as value of a controller's classvar

    # Example
    ```python
    def get_ua(request: Request):
        return request.headers.get('user-agent','')

    @Controller('/foo')
    class Foo:
        ua = use_dep(get_ua)

        @Get('/ua')
        def foo(self):
            return self.ua

    ```
    """
    value: T = Depends(dependency=dependency, use_cache=use_cache)
    setattr(value, REQ_DEP_PLACEHOLDER, True)
    return value



def _create_bp_from_record(record:UseMiddlewareRecord):
    bp=BlankPlaceholder()
    setattr(bp, USE_MIDDLEWARE_FIELD_PLACEHOLDER, record)
    return bp

def use_http_middleware(*dispatches: Callable[[Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any]):
    """add http middlewares for current Controller or Prefix with http endpoint, exclude inner Prefix

    ```python
    
    from collections.abc import Callable
    from typing import Any
    from fastapi import Request
    from fastapi_boot import Controller, use_http_middleware


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

    @Controller('/foo')
    class FooController:
        _ = use_http_middleware(middleware_foo, middleware_bar)
        
        # 1. middleware_bar before
        # 2. middleware_foo before
        # 3. call endpoint
        # 4. middleware_foo after
        # 5. middleware_bar after

        # ...
    ```

    """
    record=UseMiddlewareRecord(http_dispatches=list(dispatches))
    return _create_bp_from_record(record)

def use_ws_middleware(*dispatches: Callable[[WebSocket,Callable[[WebSocket],Coroutine[Any,Any,None]]],Any],only_message:bool=False):
    """add websocket middlewares for current Controller or Prefix with websocket endpoint, exclude inner Prefix
    - if `only_message` and message's type != 'websocket.senf': will ignore dispatches
    
    ```python 
    
    from collections.abc import Callable
    from typing import Any
    from fastapi import Request, WebSocket
    from fastapi_boot import Controller, use_http_middleware, middleware_ws_foo
    
    async def middleware_ws_foo(websocket: WebSocket, call_next: Callable):
        print('before ws send data foo') # as pos a
        res = await call_next(websocket)
        print('after ws send data foo') # as pos b
        return res

    async def middleware_ws_bar(websocket: WebSocket, call_next: Callable):
        print('before ws send data bar') # as pso c
        res = await call_next()
        print('after ws send data bar') # as pso d
        return res
    
    async def middleware_bar(request: Request, call_next: Callable[[Request], Any]):
        print('middleware_bar before') # as pos e
        resp = await call_next(request)
        print('middleware_bar after') # as pos f
        return resp
     
     
    @Controller('/chat')
    class WsController:
        _ = use_http_middleware(middleware_bar)
        ___ = use_ws_middleware(middleware_ws_bar, middleware_ws_foo, only_message=True)
        
        @Socket('/chat')
        async def chat(self, websocket: WebSocket):
            try:
                await websocket.accept()
                while True:
                    message = await websocket.receive_text()
                    # a c
                    await self.send_text(message)
                    # d b
            except:
                ...

        
        # e a c d b f
        @Post('/broadcast')
        async def send_broadcast_msg(self, msg: str = Query()):
            await self.broadcast(msg)
            return 'ok'
    ```
    
    """
    record=UseMiddlewareRecord(ws_dispatches=list(dispatches),ws_only_message=only_message)
    return _create_bp_from_record(record)


def HTTPMiddleware(dispatch:Callable[[Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any]):
    """Add global http middleware

    Args:
        dispatch (Callable[[Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any]): middleware handler
    Example:
    ```python
    from collections.abc import Callable
    from fastapi import Request
    from fastapi_boot import HTTPMiddleware

    @HTTPMiddleware
    async def barMiddleware(request: Request, call_next: Callable):
        print("before")
        res = await call_next(request)
        print("after")
        return res

    ```
    """
    task_store.add_late_task(get_call_filename(),lambda app:app.middleware('http')(dispatch),1)
    return dispatch

def provide_app(app: FastAPI, max_workers: int = 20, inject_timeout: float = 20, inject_retry_step: float = 0.05):
    """enable scan project to collect dependencies which can't been collected automatically

    Args:
        app (FastAPI): FastAPI instance
        max_workers (int, optional): workers' num to scan project. Defaults to 20.
        inject_timeout (float, optional): will raise DependencyNotFoundException if time > inject_timeout. Defaults to 20.
        inject_pause_step (float, optional): Retry interval after failing to find a dependency . Defaults to 0.05.

    Returns:
        _type_: original app
    """
    # clear store before init
    app_store.clear()
    dep_store.clear()
    task_store.clear()
    
    provide_filepath = get_call_filename()
    # the file which provides app
    app_root_dir = os.path.dirname(provide_filepath)
    app_record = AppRecord(app, inject_timeout, inject_retry_step)
    app_store.add(os.path.dirname(provide_filepath), app_record)
    # app's prefix in project
    proj_root_dir = os.getcwd()
    app_parts = Path(app_root_dir).parts
    proj_parts = Path(proj_root_dir).parts
    prefix_parts = app_parts[len(proj_parts) :]
    # scan
    dot_paths = []
    for root, _, files in os.walk(app_root_dir):
        for file in files:
            if file.endswith('.py'):
                fullpath = os.path.join(root, file)
                if fullpath == provide_filepath:
                    continue
                dot_path = '.'.join(
                    prefix_parts + Path(fullpath.replace('.py', '').replace(app_root_dir, '')).parts[1:]
                )
                dot_paths.append(dot_path)
                # clear module cache if exists
                if dot_path in sys.modules:
                    sys.modules.pop(dot_path)
    
    futures: list[Future] = []
    with ThreadPoolExecutor(max_workers) as executor:
        for dot_path in dot_paths:
            future = executor.submit(__import__,dot_path)
            futures.append(future)
        concurrent.futures.wait(futures)
        # wait all future finished
        for future in futures:
            future.result()
    # before return , run tasks
    task_store.run_late_tasks()
    return app


def OnAppProvided(priority: int = 1):
    """Methods to be executed after the app is provided
    - decorated function should be sync.
    ```python
    @OnAppProvided()
    def _(app:FastAPI):
        print('foo')

    @OnAppProvided(priority=10):
    def func():
        print('bar')

    # bar >> foo
    ```
    """

    def wrapper(func: Callable[[FastAPI], None]):
        task_store.add_late_task(get_call_filename(), func, priority)
        return func

    return wrapper


# -------------------------------------------------------------------------------------------------------------------- #
E = TypeVar('E', bound=Exception)

HttpHandler = Callable[[Request, E], Any]
WsHandler = Callable[[WebSocket, E],Any]


def ExceptionHandler(exp: int | type[E]):
    """The return value can be BaseModel instance、dataclass、dict or JSONResponse.
    ```python
    @ExceptionHandler(MyException)
    async def _(req: Request, exp: AException):
        ...
    ```
    Declarative style of the following code:
    ```python
    @app.exception_handler(AException)
    async def _(req: Request, exp: AException):
        ...
    @app.exception_handler(BException)
    def _(req: Request, exp: BException):
        ...

    @app.exception_handler(CException)
    async def _(req: WebSocket, exp: CException):
        ...
    @app.exception_handler(DException)
    def _(req: WebSocket, exp: DException):
        ...
    ```
    """

    def decorator(handler: HttpHandler | WsHandler):
        # wrap handler
        async def wrapper(*args,**kwds):
            resp=await handler(*args,**kwds) if iscoroutinefunction(handler) else handler(*args,**kwds)
            if isinstance(resp,BaseModel):
                resp=resp.model_dump()
            elif is_dataclass(resp):
                resp=asdict(resp)
            if isinstance(resp,dict):
                resp=JSONResponse(resp)
            return resp
        task_store.add_late_task(get_call_filename(), lambda app: app.add_exception_handler(exp, wrapper), EXCEPTION_HANDLER_PRIORITY)
        return handler

    return decorator
