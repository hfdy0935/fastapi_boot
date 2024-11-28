from collections.abc import Callable, Sequence
from enum import Enum
from functools import wraps
from inspect import Parameter, iscoroutinefunction, signature
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, Depends, FastAPI, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from fastapi_boot.const import (
    CONTROLLER_ROUTE_RECORD,
    REQ_DEP_PLACEHOLDER,
    USE_DEP_PREFIX_IN_ENDPOINT,
    USE_MIDDLEWARE_PLACEHOLDER,
    TypeDepRecord,
    app_store,
    dep_store,
)
from fastapi_boot.di import inject_init_deps_and_get_instance
from fastapi_boot.model import (
    AppRecord,
    BaseHttpRouteItem,
    BaseHttpRouteItemWithoutEndpoint,
    EndpointRouteRecord,
    PrefixRouteRecord,
    RequestMethodEnum,
    RequestMethodStrEnum,
)
from fastapi_boot.model import SpecificHttpRouteItemWithoutEndpointAndMethods as SM
from fastapi_boot.model import WebSocketRouteItem, WebSocketRouteItemWithoutEndpoint
from fastapi_boot.util import get_call_filename

T = TypeVar('T', bound=Callable)


def trans_path(path: str) -> str:
    """
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res = '/' + path.lstrip('/')
    res = res.rstrip('/')
    return '' if res == '/' else res


# ---------------------------------------------------- Controller ---------------------------------------------------- #


def get_use_result(cls: type[T]):
    use_dep_dict = {}
    cls_anno: dict = cls.__dict__.get('__annotations__', {})
    use_middleware_list: list[Callable] = []
    for k, v in cls.__dict__.items():
        # use_dep
        if hasattr(v, REQ_DEP_PLACEHOLDER):
            use_dep_dict.update({k: (cls_anno.get(k), v)})
        # use_middleware
        if hasattr(v, USE_MIDDLEWARE_PLACEHOLDER) and callable(v):
            use_middleware_list.append(v)
    return use_dep_dict, use_middleware_list


def trans_endpoint(instance: Any, endpoint: Callable, use_dep_dict: dict):
    """trans endpoint
    1. add `self` param's default ===> Depends(lambda: instance). set the kind of other params 'KEYWORD_ONLY';
    2. add use_dep params. replace params. replace signature.
    > or
    1. new function(without 'self' param) extend endpoint(need add 'self' when call endpoint);
    2. add use_dep params. replace params. replace signature.
    """

    def handle_kwargs(self, kwargs: dict):
        for k in use_dep_dict.keys():
            req_name = USE_DEP_PREFIX_IN_ENDPOINT + k
            setattr(self, k, kwargs.pop(req_name))
            kwargs.get(req_name)  # auto call use_dep result

    @wraps(endpoint)
    async def async_new_endpoint(*args, **kwargs):
        handle_kwargs(instance, kwargs)
        return await endpoint(instance, *args, **kwargs)

    @wraps(endpoint)
    def sync_new_endpoint(*args, **kwargs):
        handle_kwargs(instance, kwargs)
        return endpoint(instance, *args, **kwargs)

    new_endpoint = async_new_endpoint if iscoroutinefunction(endpoint) else sync_new_endpoint
    params: list[Parameter] = list(signature(new_endpoint).parameters.values())
    # remove 'self'
    if params and params[0].name == 'self':
        params.pop(0)
    # add use_dep's deps
    for k, v in use_dep_dict.items():
        req_name = USE_DEP_PREFIX_IN_ENDPOINT + k
        params.append(Parameter(name=req_name, kind=Parameter.KEYWORD_ONLY, annotation=v[0], default=v[1]))

    setattr(new_endpoint, '__signature__', signature(new_endpoint).replace(parameters=params))
    return new_endpoint


def mount_endpoint_to_anchor(
    anchor: APIRouter,
    api_route: EndpointRouteRecord,
    instance: Any,
    use_deps_dict: dict,
    prefix: str,
    urls_methods: list[tuple[str, str]],
):
    """mount endpoint to anchor and add middleware"""
    new_endpoint = trans_endpoint(instance, api_route.record.endpoint, use_dep_dict=use_deps_dict)
    api_route.record.replace_endpoint(new_endpoint).add_prefix(prefix).mount_to(anchor)
    if isinstance(api_route.record, BaseHttpRouteItem):
        urls_methods.extend(
            [
                (anchor.prefix + api_route.record.path, method.upper() if isinstance(method, str) else method.value)
                for method in api_route.record.methods
            ]
        )


def resolve_class_based_view(
    app: FastAPI, anchor: APIRouter, route_record: PrefixRouteRecord[T], prefix: str, app_record: AppRecord
):
    """

    Args:
        app (FastAPI): FastAPI instance
        anchor (APIRouter): mount anchor
        route_record (PrefixRouteRecord[T])
        prefix (str): prefix of request path
        app_record (AppRecord): app record
    """
    cls: type[T] = route_record.cls
    use_deps_dict, use_middleware_list = get_use_result(cls)

    instance: T = inject_init_deps_and_get_instance(app_record, cls)
    urls_methods: list[tuple[str, str]] = []

    for v in cls.__dict__.values():
        if hasattr(v, CONTROLLER_ROUTE_RECORD) and (attr := getattr(v, CONTROLLER_ROUTE_RECORD)):
            new_prefix = prefix + route_record.prefix
            if isinstance(attr, EndpointRouteRecord):
                mount_endpoint_to_anchor(anchor, attr, instance, use_deps_dict, new_prefix, urls_methods)
            elif isinstance(attr, PrefixRouteRecord):
                resolve_class_based_view(app, anchor, attr, new_prefix, app_record)
    # add middleware
    for func in use_middleware_list:
        func(app, urls_methods)
    # collect controller as a type dependency
    dep_store.add_dep_by_type(TypeDepRecord(cls, instance))
    return instance


class Controller(APIRouter, Generic[T]):
    def __init__(
        self,
        prefix: str = "",
        *,
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
    ):
        self.prefix = trans_path(prefix)
        super().__init__(
            prefix=self.prefix,
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
        self.use_middleware_tasks: list[Callable] = []

    def __call__(self, cls: type[T]) -> T:
        app_record = app_store.get(get_call_filename())
        instance = resolve_class_based_view(app_record.app, self, PrefixRouteRecord(cls), '', app_record)
        app_record.app.include_router(self)
        return instance

    def __getattribute__(self, k: str):
        attr = super().__getattribute__(k)
        if k in [*RequestMethodStrEnum.__args__, 'api_route', 'websocket_route']:

            def decorator(*args, **kwds):
                def wrapper(endpoint):
                    # @Controller(...).websocket(...)  @Controller(...).websocket_route(...)
                    if k.upper() in [RequestMethodEnum.WEBSOCKET.value, 'WEBSOCKET_ROUTE']:
                        WebSocketRouteItem(endpoint, *args, **kwds).mount_to(self)
                    elif k == 'api_route':
                        BaseHttpRouteItem(endpoint, *args, **kwds).mount_to(self)
                    else:
                        BaseHttpRouteItem(endpoint, methods=[k], *args, **kwds).mount_to(self)
                    app_store.get(get_call_filename()).app.include_router(self)
                    return endpoint

                return wrapper

            return decorator
        return attr


# ------------------------------------------------------ Mapping ----------------------------------------------------- #


class Req(BaseHttpRouteItemWithoutEndpoint):
    def __call__(self, endpoint: T) -> T:
        """
        @Req()
        def _():
            ...
        """
        self.path = trans_path(self.path)
        route_record = EndpointRouteRecord(BaseHttpRouteItem(endpoint=endpoint, **self.dict))
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
        route_record = EndpointRouteRecord(WebSocketRouteItem(endpoint=endpoint, **self.dict))
        setattr(endpoint, CONTROLLER_ROUTE_RECORD, route_record)
        return endpoint


# ------------------------------------------------------ Prefix ------------------------------------------------------ #
C = TypeVar('C')


def Prefix(prefix: str = ""):
    """sub block in controller， can isolate inner deps and outer deps
    ```python
    def f1(p: str = Query()):
        return 'f1'
    def f2(q: int = Query()):
        return 'f2'

    @Controller()
    class UserController:
        p = use_dep(f1)

        @Prefix()
        class Foo:
            q = use_dep(f2)
            @Get()
            def get_user(self): # only need the query param 'q'
                return self.q
    ```
    """
    prefix = trans_path(prefix)

    def wrapper(cls: type[C]) -> type[C]:
        prefix_route_record = PrefixRouteRecord(cls=cls, prefix=prefix)
        setattr(cls, CONTROLLER_ROUTE_RECORD, prefix_route_record)
        return cls

    return wrapper
