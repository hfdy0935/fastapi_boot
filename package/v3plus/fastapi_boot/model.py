from collections.abc import Callable, Coroutine, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import wraps
from http import HTTPMethod
from typing import Any, Generic, Literal, Self, TypeVar

from fastapi import APIRouter, FastAPI, Response,Request,WebSocket
from fastapi.datastructures import Default
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute

T = TypeVar('T')
HttpStrMethod = Literal[
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'CONNECT',
    'HEAD',
    'OPTIONS',
    'TRACE',
    'PATCH',
]
LowerHttpMethod = [m.value.lower() for m in list(HTTPMethod)]


# -------------------------------------------------- request params -------------------------------------------------- #


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
    callbacks: list[BaseRoute] | None = None
    openapi_extra: dict[str, Any] | None = None
    generate_unique_id_function: Any = field(default_factory=lambda: Default(generate_unique_id))

    @property
    def dict(self):
        return asdict(self)


@dataclass
class BaseHttpRouteItemWithoutEndpoint(SpecificHttpRouteItemWithoutEndpointAndMethods):
    """Req params without endpoint"""

    methods: set[HTTPMethod | HttpStrMethod] | list[HTTPMethod | HttpStrMethod] = field(default_factory=lambda: ['GET'])


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
    callbacks: list[BaseRoute] | None = None
    openapi_extra: dict[str, Any] | None = None
    generate_unique_id_function: Callable[[APIRoute], str] = field(default_factory=lambda: Default(generate_unique_id))
    methods: set[str] | list[str] = field(default_factory=lambda: ['GET'])

    def format_methods(self):
        self.methods = [m.value if isinstance(m, HTTPMethod) else m.upper() for m in self.methods]
        return self

    def replace_endpoint(self, endpoint: Callable):
        self.endpoint = endpoint
        return self

    def add_prefix(self, prefix: str):
        self.path = prefix + self.path
        return self

    def mount_to(self, app: APIRouter):
        for method in self.methods:
            app.add_api_route(**{**asdict(self), 'methods': [method]})


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
        """no middleware"""
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


# ---------------------------------------------------- record ---------------------------------------------------- #
@dataclass
class AppRecord:
    """fastapi_record in store"""

    app: FastAPI
    inject_timeout: float
    inject_retry_step: float
    

@dataclass
class UseMiddlewareRecord:
    """use_middleware record in controller"""
    http_urls_methods:list[tuple[str, str]]=field(default_factory=list)
    http_dispatches:list[Callable[[Request,Callable[[Request],Coroutine[Any,Any,Response]]],Any]]=field(default_factory=list)
    ws_dispatches:list[Callable[[WebSocket,Callable[[WebSocket],Coroutine[Any,Any,None]]],None]]=field(default_factory=list)
    ws_only_message:bool=False # ws_dispatches only be called if ws_only_message and message's type == 'websocket.send' 
    
    def add_http_middleware(self,app:FastAPI):
        """add midleware to app"""
        if not self.http_dispatches:
            return
        async def wrapper(request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Any]]):
            if (request.url.path, request.method) in self.http_urls_methods:
                for func in self.http_dispatches:
                    # "call_next" default param ==> save call_next of each loop to avoid "maximum recursion depth exceeded".
                    # "func" default params ==> save "func" of each loop to avoid repeatation of last func.
                    async def temp1(request,call_next=call_next,func=func):
                        async def temp2(request):
                            return await call_next(request)
                        return await func(request,temp2)
                    call_next=temp1
            return await call_next(request) # if no matched middleware, just call original call_next, else call the accural call_next.
        app.middleware('http')(wrapper)
    
    
    def add_ws_middleware(self,websocket:WebSocket):
        if not self.ws_dispatches:
            return
        def wrapper(target: Callable):
            """target: method need to be replace"""
            async def wrapper2(*args,**kwargs):
                nonlocal target
                call_next=target
                for func in self.ws_dispatches:
                    # partial param websocket as placeholder
                    async def temp1(websocket=websocket,call_next=call_next,func=func):
                        async def temp2(websocket=websocket):
                            return await call_next(*args,**kwargs)
                        not_message=(args[0] or {}).get('type','')!='websocket.send'
                        return await temp2() if (not_message and self.ws_only_message) else await func(websocket,temp2)
                    call_next=temp1
                return await call_next()
            return wrapper2
        
        websocket.send=wraps(websocket.send.__func__)(wrapper(websocket.send))

        
    def __add__(self,other:'UseMiddlewareRecord')->Self:
        """merge http_dispatches in a controller or a prefix"""
        self.http_dispatches.extend(other.http_dispatches)
        return self


# ----------------------------------------------------- exception ---------------------------------------------------- #
class InjectFailException(Exception):
    """inject fail"""


class DependencyNotFoundException(Exception):
    """dependency not found"""


class DependencyDuplicatedException(Exception):
    """dependency duplicated"""


class AppNotFoundException(Exception):
    """app not found"""
