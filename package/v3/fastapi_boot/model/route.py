from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Annotated, Any
from fastapi import Response
from fastapi.datastructures import Default
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id

from fastapi_boot.enums import RequestMethodEnum, RequestMethodStrEnum


# ------------------------------------------------------- 请求参数 ------------------------------------------------------- #


@dataclass
class SpecificHttpRouteItemWithoutEndpointAndMethods:
    """具体请求参数，没有endpoint和methods"""

    path: Annotated[str, "路径"] = ""
    response_model: Annotated[Any, "响应类型"] = None
    status_code: Annotated[int | None, "响应状态码"] = None
    tags: Annotated[list[str | Enum] | None, "路由标签，自定义"] = field(default_factory=list)
    dependencies: Annotated[Sequence[Any] | None, "依赖"] = None
    summary: Annotated[str | None, "路由概要，自定义"] = None
    description: Annotated[str | None, "路由描述，自定义"] = None
    response_description: Annotated[str, "响应结果描述"] = "Successful Response"
    responses: Annotated[dict[int | str, dict[str, Any]] | None, "响应"] = None
    deprecated: Annotated[bool | None, "是否已弃用"] = None
    operation_id: Annotated[str | None, "处理id"] = None
    response_model_include: Annotated[IncEx | None, "包括的响应类型"] = None
    response_model_exclude: Annotated[IncEx | None, "排除的响应类型"] = None
    response_model_by_alias: Annotated[bool, "别名响应类型"] = True
    response_model_exclude_unset: Annotated[bool, "是否排除非默认响应类型"] = False
    response_model_exclude_defaults: Annotated[bool, "是否排除默认响应类型"] = False
    response_model_exclude_none: Annotated[bool, "是否排除空的响应类型"] = False
    include_in_schema: Annotated[bool, ""] = True
    response_class: Annotated[type[Response] | Any, "返回响应的类型"] = field(
        default_factory=lambda: Default(JSONResponse)
    )
    name: Annotated[str | None, "名"] = None
    route_class_override: Annotated[type[APIRoute], ""] | None = None
    openapi_extra: Annotated[dict[str, Any] | None, ""] = None
    generate_unique_id_function: Annotated[Any, "路由处理函数唯一id的生成函数"] = field(
        default_factory=lambda: Default(generate_unique_id)
    )

    @property
    def dict(self):
        return asdict(self)


@dataclass
class SpecificHttpRouteItem:
    """具体请求参数，没有methods"""

    path: Annotated[str, "路径"]
    endpoint: Annotated[Callable, "路由映射方法"]
    response_model: Annotated[Any, "响应类型"] = None
    status_code: Annotated[int | None, "响应状态码"] = None
    tags: Annotated[list[str | Enum] | None, "路由标签，自定义"] = field(default_factory=list)
    dependencies: Annotated[Sequence[Any] | None, "依赖"] = None
    summary: Annotated[str | None, "路由概要，自定义"] = None
    description: Annotated[str | None, "路由描述，自定义"] = None
    response_description: Annotated[str, "响应结果描述"] = "Successful Response"
    responses: Annotated[dict[int | str, dict[str, Any]] | None, "响应"] = None
    deprecated: Annotated[bool | None, "是否已弃用"] = None
    operation_id: Annotated[str | None, "处理id"] = None
    response_model_include: Annotated[IncEx | None, "包括的响应类型"] = None
    response_model_exclude: Annotated[IncEx | None, "排除的响应类型"] = None
    response_model_by_alias: Annotated[bool, "别名响应类型"] = True
    response_model_exclude_unset: Annotated[bool, "是否排除非默认响应类型"] = False
    response_model_exclude_defaults: Annotated[bool, "是否排除默认响应类型"] = False
    response_model_exclude_none: Annotated[bool, "是否排除空的响应类型"] = False
    include_in_schema: Annotated[bool, ""] = True
    response_class: Annotated[type[Response] | Any, "返回响应的类型"] = field(
        default_factory=lambda: Default(JSONResponse)
    )
    name: Annotated[str | None, "名"] = None
    route_class_override: Annotated[type[APIRoute], ""] | None = None
    openapi_extra: Annotated[dict[str, Any] | None, ""] = None
    generate_unique_id_function: Annotated[Any, "路由处理函数唯一id的生成函数"] = field(
        default_factory=lambda: Default(generate_unique_id)
    )

    @property
    def dict(self):
        return asdict(self)


@dataclass
class BaseHttpRouteItemWithoutEndpoint(SpecificHttpRouteItemWithoutEndpointAndMethods):
    """Req请求参数，没有endpoint"""

    methods: Annotated[
        set[RequestMethodEnum | RequestMethodStrEnum] | list[RequestMethodEnum | RequestMethodStrEnum], "请求方法"
    ] = field(default_factory=lambda: ["get"])


@dataclass
class BaseHttpRouteItem:
    """Req请求参数"""

    endpoint: Annotated[Callable, "路由映射方法"]
    path: Annotated[str, "路径"] = ""
    response_model: Annotated[Any, "响应类型"] = None
    status_code: Annotated[int | None, "响应状态码"] = None
    tags: Annotated[list[str | Enum] | None, "路由标签，自定义"] = field(default_factory=list)
    dependencies: Annotated[Sequence[Any] | None, "依赖"] = None
    summary: Annotated[str | None, "路由概要，自定义"] = None
    description: Annotated[str | None, "路由描述，自定义"] = None
    response_description: Annotated[str, "响应结果描述"] = "Successful Response"
    responses: Annotated[dict[int | str, dict[str, Any]] | None, "响应"] = None
    deprecated: Annotated[bool | None, "是否已弃用"] = None
    methods: Annotated[
        set[RequestMethodEnum | RequestMethodStrEnum] | list[RequestMethodEnum | RequestMethodStrEnum], "请求方法"
    ] = field(default_factory=lambda: ["get"])
    operation_id: Annotated[str | None, "处理id"] = None
    response_model_include: Annotated[IncEx | None, "包括的响应类型"] = None
    response_model_exclude: Annotated[IncEx | None, "排除的响应类型"] = None
    response_model_by_alias: Annotated[bool, "别名响应类型"] = True
    response_model_exclude_unset: Annotated[bool, "是否排除非默认响应类型"] = False
    response_model_exclude_defaults: Annotated[bool, "是否排除默认响应类型"] = False
    response_model_exclude_none: Annotated[bool, "是否排除空的响应类型"] = False
    include_in_schema: Annotated[bool, ""] = True
    response_class: Annotated[type[Response] | Any, "返回响应的类型"] = field(
        default_factory=lambda: Default(JSONResponse)
    )
    name: Annotated[str | None, "名"] = None
    route_class_override: Annotated[type[APIRoute], ""] | None = None
    openapi_extra: Annotated[dict[str, Any] | None, ""] = None
    generate_unique_id_function: Annotated[Any, "路由处理函数唯一id的生成函数"] = field(
        default_factory=lambda: Default(generate_unique_id)
    )

    @property
    def dict(self):
        return asdict(self)


@dataclass
class WebSocketRouteItemWithoutEndpoint:
    """没有endpoint的websocket请求参数"""

    path: str = ""
    name: str | None = None
    dependencies: Sequence[Depends] | None = None

    @property
    def dict(self):
        return asdict(self)


@dataclass
class WebSocketRouteItem:
    """websocket请求参数"""

    path: str
    endpoint: Annotated[Callable, "路由映射方法"]
    name: str | None = None
    dependencies: Sequence[Depends] | None = None

    @property
    def dict(self):
        return asdict(self)


# --------------------------------------------------- 控制器中传递的每层路由记录 -------------------------------------------------- #


@dataclass
class EndpointRouteRecord:
    """endpoint的路由记录

    Args:
        api_route (BaseHttpRouteItem  |  WebSocketRouteItem): 路由
    """

    api_route: BaseHttpRouteItem | WebSocketRouteItem


@dataclass
class PrefixReoutRecord:
    """prefix的路由记录

    Args:
        api_routes (list[BaseHttpRouteItem  |  WebSocketRouteItem | &#39;PrefixReoutRecord&#39;]): 子路由
        cls (type): 装饰的类
    """

    api_routes: list["EndpointRouteRecord| PrefixReoutRecord"]
    cls: type
    prefix: str = ""
