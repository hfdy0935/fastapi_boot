from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Union, Type

from fastapi import APIRouter, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from overrides import overrides
from starlette.routing import BaseRoute
from starlette.types import Lifespan, ASGIApp

from fastapi_boot.core.application.main import MainApplication
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.model.scan_model import ControllerItem
from fastapi_boot.utils.add_task import handle_task
from fastapi_boot.utils.generator import get_stack_path
from fastapi_boot.utils.transformer import trans_path
from fastapi_boot.utils.validator import validate_controller


def wired_controller(router: APIRouter, obj: Callable):
    stack_path = get_stack_path(2)
    item = ControllerItem(symbol=Symbol.from_obj(obj), router=router)
    setattr(item, CommonVar.ORI_OBJ, obj)

    def task():
        app: MainApplication = CommonVar.get_application(stack_path)
        app.get_sv().add_controller(item)

    handle_task(stack_path, task)


class Controller(APIRouter):
    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        routes: Optional[List[BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        dependency_overrides_provider: Optional[Any] = None,
        route_class: Type[APIRoute] = APIRoute,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        lifespan: Optional[Lifespan[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
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

    @overrides
    def __call__(self, obj: Type[Any]):
        validate_controller(obj)
        wired_controller(self, obj)

    def __getattribute__(self, name: str):
        attr = super().__getattribute__(name)
        if name.upper() in RequestMethodEnum.get_strs():
            wired_controller(self, attr)
        return attr
