from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, Response
from fastapi.datastructures import Default
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id

from fastapi_boot.enums import RequestMethodEnum, RequestMethodStrEnum

T = TypeVar('T')


@dataclass
class SpecificHttpRouteItemWithoutEndpointAndMethods:
    """specific http params without endpoint and methods"""

    path: str = ''
    response_model: Any = None
    status_code: int | None = None
    tags: list[str | Enum] | None = field(default_factory=list)
    dependencies: Sequence[Any] | None = None
    summary: str | None = None
    description: str | None = None
    response_description: str = 'Successful Response'
    responses: dict[int | str, dict[str, Any]] | None = None
    deprecated: bool | None = None
    operation_id: str | None = None
    response_model_include: IncEx | None = None
    response_model_exclude: IncEx | None = None
    response_model_by_alias: bool = True
    response_model_exclude_unset: bool = False
    response_model_exclude_defaults: bool = False
    response_model_exclude_none: bool = False
    include_in_schema: bool = True
    response_class: type[Response] | Any = field(default_factory=lambda: Default(JSONResponse))
    name: str | None = None
    route_class_override: type[APIRoute] | None = None
    openapi_extra: dict[str, Any] | None = None
    generate_unique_id_function: Any = field(default_factory=lambda: Default(generate_unique_id))

    @property
    def dict(self):
        return asdict(self)


@dataclass
class BaseHttpRouteItemWithoutEndpoint(SpecificHttpRouteItemWithoutEndpointAndMethods):
    """Req params without endpoint"""

    methods: set[RequestMethodEnum | RequestMethodStrEnum] | list[RequestMethodEnum | RequestMethodStrEnum] = field(
        default_factory=lambda: ['get']
    )


@dataclass
class BaseHttpRouteItem:
    """req params"""

    endpoint: Callable
    path: str = ''
    response_model: Any = None
    status_code: int | None = None
    tags: list[str | Enum] | None = field(default_factory=list)
    dependencies: Sequence[Any] | None = None
    summary: str | None = None
    description: str | None = None
    response_description: str = 'Successful Response'
    responses: dict[int | str, dict[str, Any]] | None = None
    deprecated: bool | None = None
    operation_id: str | None = None
    response_model_include: IncEx | None = None
    response_model_exclude: IncEx | None = None
    response_model_by_alias: bool = True
    response_model_exclude_unset: bool = False
    response_model_exclude_defaults: bool = False
    response_model_exclude_none: bool = False
    include_in_schema: bool = True
    response_class: type[Response] | Any = field(default_factory=lambda: Default(JSONResponse))
    name: str | None = None
    route_class_override: type[APIRoute] | None = None
    openapi_extra: dict[str, Any] | None = None
    generate_unique_id_function: Any = field(default_factory=lambda: Default(generate_unique_id))
    methods: set[RequestMethodEnum | RequestMethodStrEnum] | list[RequestMethodEnum | RequestMethodStrEnum] = field(
        default_factory=lambda: ['get']
    )

    def replace_endpoint(self, endpoint: Callable):
        self.endpoint = endpoint
        return self

    def add_prefix(self, prefix: str):
        self.path = prefix + self.path
        return self

    def mount_to(self, anchor: APIRouter):
        for method in self.methods:
            anchor.add_api_route(**{**asdict(self), 'methods': [method]})


@dataclass
class WebSocketRouteItemWithoutEndpoint:
    """websocket params without endpoint"""

    path: str = ""
    name: str | None = None
    dependencies: Sequence[Depends] | None = None

    @property
    def dict(self):
        return asdict(self)


@dataclass
class WebSocketRouteItem:

    endpoint: Callable
    path: str
    name: str | None = None
    dependencies: Sequence[Depends] | None = None

    def replace_endpoint(self, endpoint: Callable):
        self.endpoint = endpoint
        return self

    def add_prefix(self, prefix: str):
        self.path = prefix + self.path
        return self

    def mount_to(self, anchor: APIRouter):
        anchor.add_api_websocket_route(**asdict(self))


# --------------------------------------------------- route record -------------------------------------------------- #
@dataclass
class EndpointRouteRecord:
    record: BaseHttpRouteItem | WebSocketRouteItem


@dataclass
class PrefixRouteRecord(Generic[T]):
    """prefix

    Args:
        cls (type): class decorated by Prefix
        prefix (str): prefix path
    """

    cls: type[T]
    prefix: str = ""
