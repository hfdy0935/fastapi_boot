from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from fastapi_boot.constants import ROUTE_RECORD
from fastapi_boot.enums import RouteTypeEnum
from fastapi_boot.model.route import (
    BaseHttpRouteItem,
    BaseHttpRouteItemWithoutEndpoint,
    SpecificHttpRouteItemWithoutEndpointAndMethods as SM,
    EndpointRouteRecord,
    WebSocketRouteItem,
    WebSocketRouteItemWithoutEndpoint,
)
from fastapi_boot.utils import trans_path


class Req(BaseHttpRouteItemWithoutEndpoint):
    def __call__(self, endpoint: Callable) -> Any:
        # 处理前缀
        self.path = trans_path(self.path)
        with_endpoint = BaseHttpRouteItem(
            endpoint=endpoint,
            **self.dict,
        )

        route_record = EndpointRouteRecord(
            route_type=RouteTypeEnum.ENDPOINT,
            api_route=with_endpoint,
        )
        setattr(endpoint, ROUTE_RECORD, route_record)
        return endpoint


@dataclass
class Get(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict)(endpoint)


@dataclass
class Post(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["post"])(endpoint)


@dataclass
class Put(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["put"])(endpoint)


@dataclass
class Delete(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["delete"])(endpoint)


@dataclass
class Head(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["head"])(endpoint)


@dataclass
class Patch(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["patch"])(endpoint)


@dataclass
class Trace(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["options"])(endpoint)


@dataclass
class Options(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["trace"])(endpoint)


class WebSocket(WebSocketRouteItemWithoutEndpoint):
    def __call__(self, endpoint: Callable):
        self.path = trans_path(self.path)
        with_endpoint = WebSocketRouteItem(endpoint=endpoint, **self.dict)

        route_record = EndpointRouteRecord(
            route_type=RouteTypeEnum.ENDPOINT,
            api_route=with_endpoint,
        )
        setattr(self, ROUTE_RECORD, route_record)
        return endpoint
