import concurrent
import concurrent.futures
import os
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TypeVar

from fastapi import Depends, FastAPI

from fastapi_boot.constants import REQ_DEP_PLACEHOLDER
from fastapi_boot.store import app_store
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


def provide_app(app: FastAPI, max_workers: int = 10, inject_timeout: float = 10):
    """enable scan project to collect dependencies which can't been collected automaticlly

    Args:
        app (FastAPI): FastAPI instance
        max_workers (int, optional): workers' num to scan project. Defaults to 10.
        inject_timeout (float, optional): will raise DependencyNotFoundException if time > inject_timeout. Defaults to 10.

    Returns:
        _type_: original app
    """
    path = get_call_filename()
    dir = os.path.dirname(path)
    app_store.add(dir, app, inject_timeout)
    # scan
    futures: list[Future] = []
    with ThreadPoolExecutor(max_workers) as executor:
        for root, _, files in os.walk(dir):
            for file in files:
                if file.endswith('.py'):
                    fullpath = os.path.join(root, file)
                    if fullpath == path:
                        continue
                    dot_path = '.'.join(
                        Path(fullpath.replace('.py', '').replace(dir, '').replace('__init__', '')).parts[1:]
                    )
                    future = executor.submit(__import__, dot_path)
                    futures.append(future)
        concurrent.futures.wait(futures)
        # wait all future finished
        for future in futures:
            future.result()

            # module_name = file.replace('.py', '')
            # spec = importlib.util.spec_from_file_location(module_name, fullpath)
            # assert spec
            # assert spec.loader
            # module = importlib.util.module_from_spec(spec)
            # spec.loader.exec_module(module)
    return app
