from collections.abc import Callable, Sequence
from enum import Enum
from functools import wraps
from typing import Any
from fastapi import Response, routing
from fastapi.params import Depends
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.responses import JSONResponse
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id

from fastapi_boot.core.var.constants import ORI_OBJ, ROUTE_TYPE
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.enums.scan_enum import RouteType
from fastapi_boot.model.route_model import (
    RouteRecordItem,
    RouteRecordItemParams,
    Symbol,
)
from fastapi_boot.utils.judger import is_top_level
from fastapi_boot.utils.transformer import (
    trans_methods,
    trans_path,
)
from fastapi_boot.utils.validator import validate_request_mapping
from ..match_route import match_route


def Req(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: bool | None = None,
    methods: list[RequestMethodEnum | str] = [RequestMethodEnum.GET],
    operation_id: str | None = None,
    response_model_include: IncEx | None = None,
    response_model_exclude: IncEx | None = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: dict[str, Any] | None = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    _path: str = trans_path(path)

    def decorator(obj: Callable):
        symbol = Symbol.from_obj(obj)
        _methods = trans_methods(methods)
        validate_request_mapping(obj, _methods, symbol)

        # 声明式，没有手动调用过程
        # wraps包起来，不影响原函数名
        @wraps(obj)
        def effect(*args, **kwargs): ...

        setattr(effect, ORI_OBJ, obj)
        setattr(
            obj,
            ROUTE_TYPE,
            RouteType.FBV if is_top_level(obj) else RouteType.ENDPOINT,
        )
        # 插入最终路由，扫描时不激活，启动时才激活
        item = RouteRecordItem(
            symbol=symbol,
            path=_path,
            methods=_methods,
            endpoint_name=obj.__name__,
            endpoint=obj,
            params=RouteRecordItemParams(
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                dependencies=dependencies,
                summary=summary,
                description=description,
                response_description=response_description,
                deprecated=deprecated,
                responses=responses,
                operation_id=operation_id,
                response_model_include=response_model_include,
                response_model_exclude=response_model_exclude,
                response_model_by_alias=response_model_by_alias,
                response_model_exclude_unset=response_model_exclude_unset,
                response_model_exclude_defaults=response_model_exclude_defaults,
                response_model_exclude_none=response_model_exclude_none,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            ),
        )
        match_route(2, item)
        return effect

    return decorator
