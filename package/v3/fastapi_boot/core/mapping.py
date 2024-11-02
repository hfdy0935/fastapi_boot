from collections.abc import Callable
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
        print(self.path)
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


class Get(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict)(endpoint)


class Post(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["post"])(endpoint)


class Put(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["put"])(endpoint)


class Delete(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["delete"])(endpoint)


class Head(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["head"])(endpoint)


class Patch(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["patch"])(endpoint)


class Trace(SM):
    def __call__(self, endpoint: Callable):
        return Req(**self.dict, methods=["options"])(endpoint)


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
        setattr(endpoint, ROUTE_RECORD, route_record)
        return endpoint
