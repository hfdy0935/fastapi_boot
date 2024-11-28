import concurrent
import concurrent.futures
import os
from collections.abc import Awaitable, Callable, Coroutine
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
import sys
from typing import Any, TypeVar

from fastapi import Depends, FastAPI, Request, Response, WebSocket

from fastapi_boot.const import REQ_DEP_PLACEHOLDER, USE_MIDDLEWARE_TASK_PLACEHOLDER,EXCEPTION_HANDLER_PRIORITY, BlankPlaceholder, app_store, task_store,dep_store
from fastapi_boot.model import AppRecord
from fastapi_boot.util import get_call_filename
T = TypeVar('T')


def use_dep(dependency: Callable[..., T] | None, use_cache: bool = True) -> T:
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


def use_middleware(*dispatches: Callable[[Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any]):
    """add middlewares for current Controller or Prefix, exclude inner Prefix

    ```python
    from collections.abc import Callable
    from typing import Any
    from fastapi import Request
    from fastapi_boot import Controller, use_middleware


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
        _ = use_middleware(middleware_foo, middleware_bar)
        # 1. middleware_bar before
        # 2. middleware_foo before
        # 3. call endpoint
        # 4. middleware_foo after
        # 5. middleware_bar after

        # ...
    ```

    """
    def task(app: FastAPI, urls_methods: list[tuple[str, str]]):
        async def wrapper(request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Any]]):
            if (request.url.path, request.method) in urls_methods:
                for func in dispatches:
                    # "call_next" default param ==> save call_next of each loop to avoid "maximum recursion depth exceeded".
                    # "func" default params ==> save "func" of each loop to avoid repeatation of last func.
                    async def temp1(request,call_next=call_next,func=func):
                        async def temp2(request):
                            return await call_next(request)
                        return await func(request,temp2)
                    call_next=temp1
            return await call_next(request) # if no matched middleware, just call original call_next, else call the accural call_next.
        app.middleware('http')(wrapper)
    
    bp=BlankPlaceholder()
    setattr(bp, USE_MIDDLEWARE_TASK_PLACEHOLDER, task)
    return bp


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

HttpHandler = Callable[[Request, E], Response|Awaitable[Response]]
WsHandler = Callable[[WebSocket, E],Any]


def ExceptionHandler(exp: int | type[E]):
    """
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
        task_store.add_late_task(get_call_filename(), lambda app: app.add_exception_handler(exp, handler), EXCEPTION_HANDLER_PRIORITY)
        return handler

    return decorator
