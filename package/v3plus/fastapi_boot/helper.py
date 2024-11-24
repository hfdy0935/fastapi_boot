from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, Depends

from fastapi_boot.constants import API_ROUTER_KEY_IN_CONTROLLER, REQ_DEP_PLACEHOLDER
from fastapi_boot.exception import InValidControllerException

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
        def _(self):
            return self.ua

    ```
    """
    value: T = Depends(dependency=dependency, use_cache=use_cache)
    setattr(value, REQ_DEP_PLACEHOLDER, True)
    return value


def get_router(ctrl: Callable) -> APIRouter:
    """get router from controller"""
    if hasattr(ctrl, API_ROUTER_KEY_IN_CONTROLLER):
        return getattr(ctrl, API_ROUTER_KEY_IN_CONTROLLER)
    raise InValidControllerException(f'"{ctrl}" is not a valid controller')
