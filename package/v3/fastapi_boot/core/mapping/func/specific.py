from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Any, Optional, Sequence, Union
from fastapi import Response, routing
from fastapi.params import Depends
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.responses import JSONResponse
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.constants import ORI_OBJ, ROUTE_TYPE
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.enums.scan_enum import RouteType
from fastapi_boot.model.route_model import (
    RouteRecordItem,
    RouteRecordItemParams,
    Symbol,
)
from fastapi_boot.utils.judger import is_top_level
from fastapi_boot.utils.transformer import trans_path
from fastapi_boot.utils import validator as Validator
from .base import Req
from ..match_route import match_route


def Get(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.GET],
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
        )(obj)

    return decorator


def Post(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.POST],
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
        )(obj)

    return decorator


def Put(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.PUT],
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
        )(obj)

    return decorator


def Delete(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.DELETE],
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
        )(obj)

    return decorator


def Options(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.OPTIONS],
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
        )(obj)

    return decorator


def Head(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.HEAD],
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
        )(obj)

    return decorator


def Patch(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.PATCH],
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
        )(obj)

    return decorator


def Trace(
    path: str = "",
    response_model: Any = Default(None),
    status_code: int | None = None,
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[Depends] | None = None,
    summary: str | None = None,
    description: str | None = None,
    response_description: str = "Successful Response",
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: Optional[bool] = None,
    operation_id: str | None = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    name: str | None = None,
    openapi_extra: Optional[dict[str, Any]] = None,
    generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(generate_unique_id),
):
    def decorator(obj: Callable):
        Validator.validate_specific_mapping(obj)
        return Req(
            path=trans_path(path),
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            methods=[RequestMethodEnum.TRACE],
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
        )(obj)

    return decorator


def WebSocket(
    path: str = "",
    name: str | None = None,
    dependencies: Sequence[Depends] | None = None,
):

    def decorator(obj: Callable):
        @wraps(obj)
        def effect(*args, **kwargs): ...

        symbol = Symbol.from_obj(obj)
        Validator.validate_specific_mapping(obj)

        setattr(effect, ORI_OBJ, obj)
        setattr(
            obj,
            ROUTE_TYPE,
            RouteType.FBV if is_top_level(obj) else RouteType.ENDPOINT,
        )
        item = RouteRecordItem(
            symbol=symbol,
            path=trans_path(path),
            methods=[RequestMethodEnum.WEBSOCKET.value],
            endpoint_name=obj.__name__,
            endpoint=obj,
            params=RouteRecordItemParams(name=name, dependencies=dependencies),
        )
        match_route(2, item)
        return effect

    return decorator
