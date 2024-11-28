import concurrent
import concurrent.futures
import os
from asyncio import iscoroutinefunction
from collections.abc import Callable, Coroutine
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, TypeVar

from fastapi import Depends, FastAPI, Request, Response, WebSocket
from starlette.routing import BaseRoute

from fastapi_boot.const import REQ_DEP_PLACEHOLDER, USE_MIDDLEWARE_PLACEHOLDER, app_store, task_store
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


def use_middleware(*func: Callable[[Request, Callable[[Request], Any]], Any]):
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
        for f in func:
            # closure
            async def wrapper(request: Request, call_next: Callable[[Request], Any], f=f):
                if (request.url.path, request.method) in urls_methods:
                    return await f(request, call_next)
                return await call_next(request)  # no matched middleware

            app.middleware('http')(wrapper)

    setattr(task, USE_MIDDLEWARE_PLACEHOLDER, True)
    return task


# avoid empty routes when using uvicorn.run('main:app', reload=True)
app_routes_cache: dict[str, list[BaseRoute]] = {}


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
    provide_filepath = get_call_filename()
    app_root_dir = os.path.dirname(provide_filepath)
    app_record = AppRecord(app, inject_timeout, inject_retry_step)
    app_store.add(os.path.dirname(provide_filepath), app_record)
    # app's prefix in project
    proj_root_dir = os.getcwd()
    app_parts = Path(app_root_dir).parts
    proj_parts = Path(proj_root_dir).parts
    prefix_parts = app_parts[min(len(app_parts), len(proj_parts)) :]
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
    futures: list[Future] = []
    with ThreadPoolExecutor(max_workers) as executor:
        for dot_path in dot_paths:
            future = executor.submit(__import__, dot_path)
            futures.append(future)
        concurrent.futures.wait(futures)
        # wait all future finished
        for future in futures:
            future.result()

    # add routes cache
    if cache := app_routes_cache.get(provide_filepath):
        app.routes.clear()
        app.routes.extend(cache)
    else:
        # update routes cache
        app_routes_cache.update({provide_filepath: app.routes})

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

    def wrapper(func: Callable[[FastAPI], None] | Callable[[], None]):
        task_store.add_late_task(get_call_filename(), func, priority)
        return func

    return wrapper


# -------------------------------------------------------------------------------------------------------------------- #
E = TypeVar('E', bound=Exception)

HttpHandler = Callable[[Request, E], Response] | Callable[[Request, E], Coroutine[Any, Any, Response]]
WsHandler = Callable[[WebSocket, E], None] | Callable[[WebSocket, E], Coroutine[Any, Any, None]]


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
        # adjust params num
        async def wrapper(*args):
            if iscoroutinefunction(handler):
                return await handler(*args)
            else:
                return handler(*args)

        task_store.add_late_task(get_call_filename(), lambda app: app.add_exception_handler(exp, wrapper), 1)
        return handler

    return decorator
