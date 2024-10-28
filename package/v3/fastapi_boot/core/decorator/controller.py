from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any

from fastapi import APIRouter, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import Lifespan, ASGIApp

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.constants import ORI_OBJ
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.model.scan_model import ControllerItem
from fastapi_boot.utils.task import add_task, handle_task
from fastapi_boot.utils.get import get_stack_path
from fastapi_boot.utils.transformer import trans_path
from fastapi_boot.utils.validator import validate_controller


def wired_controller(router: APIRouter, obj: Callable):
    stack_path = get_stack_path(2)
    item = ControllerItem(symbol=Symbol.from_obj(obj), router=router)
    setattr(item, ORI_OBJ, obj)

    def task():
        if app := CommonVar.get_app(stack_path):
            app.sv.add_controller(item)

    add_task(stack_path, task)


class Controller(APIRouter):
    def __init__(
        self,
        prefix: str = "",
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: dict[int | str, dict[str, Any]] | None = None,
        callbacks: list[BaseRoute] | None = None,
        routes: list[BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: ASGIApp | None = None,
        dependency_overrides_provider: Any | None = None,
        route_class: type[APIRoute] = APIRoute,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        lifespan: Lifespan[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(generate_unique_id),
    ) -> None:
        super().__init__(
            prefix=trans_path(prefix),
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
        )

    def __call__(self, obj: type[Any]):
        validate_controller(obj)
        wired_controller(self, obj)

    def __getattribute__(self, name: str):
        attr = super().__getattribute__(name)
        if name.upper() in RequestMethodEnum.get_strs():
            wired_controller(self, attr)
        return attr
