from collections.abc import Callable
from typing import TypeVar

from fastapi_boot.constants import CONTROLLER_ROUTE_RECORD
from fastapi_boot.model import BaseHttpRouteItem, BaseHttpRouteItemWithoutEndpoint, EndpointRouteRecord, SpecificHttpRouteItemWithoutEndpointAndMethods as SM, WebSocketRouteItem, WebSocketRouteItemWithoutEndpoint
from fastapi_boot.util import trans_path

T = TypeVar('T', bound=Callable)


class Req(BaseHttpRouteItemWithoutEndpoint):
    def __call__(self, endpoint: T) -> T:
        """
        @Req()
        def _():
            ...
        """
        self.path = trans_path(self.path)
        route_record = EndpointRouteRecord(
            BaseHttpRouteItem(endpoint=endpoint, **self.dict))
        setattr(endpoint, CONTROLLER_ROUTE_RECORD, route_record)
        return endpoint


class Get(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict)(endpoint)


class Post(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['post'])(endpoint)


class Put(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['put'])(endpoint)


class Delete(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['delete'])(endpoint)


class Head(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['head'])(endpoint)


class Patch(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['patch'])(endpoint)


class Trace(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['options'])(endpoint)


class Options(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['trace'])(endpoint)


class WebSocket(WebSocketRouteItemWithoutEndpoint):
    def __call__(self, endpoint: T) -> T:
        self.path = trans_path(self.path)
        route_record = EndpointRouteRecord(
            WebSocketRouteItem(endpoint=endpoint, **self.dict))
        setattr(endpoint, CONTROLLER_ROUTE_RECORD, route_record)
        return endpoint
