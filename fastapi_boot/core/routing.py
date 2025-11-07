from collections.abc import Callable, Sequence
from enum import Enum
from functools import reduce, wraps
from inspect import Parameter, getmembers, iscoroutinefunction, signature
from typing import Any, TypeVar

from fastapi import APIRouter, Response, params, WebSocket as FastAPIWebSocket
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from .const import (
    CONTROLLER_ROUTE_RECORD,
    REQ_DEP_PLACEHOLDER,
    USE_DEP_PREFIX_IN_ENDPOINT,
    USE_MIDDLEWARE_FIELD_PLACEHOLDER,
    BlankPlaceholder,
    app_store,
    dep_store,
    task_store
)
from .DI import inject_init_deps_and_get_instance
from .model import (
    AppRecord,
    BaseHttpRouteItem,
    BaseHttpRouteItemWithoutEndpoint,
    EndpointRouteRecord,
    LowerHttpMethod,
    PrefixRouteRecord,
    UseMiddlewareRecord,
)
from .model import SpecificHttpRouteItemWithoutEndpointAndMethods as SM
from .model import WebSocketRouteItem, WebSocketRouteItemWithoutEndpoint
from .util import get_call_filename


T = TypeVar('T', bound=Callable)
RouterCls = TypeVar('RouterCls')


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

def get_use_result(cls: type[RouterCls]):
    use_dep_dict = {}
    cls_anno: dict = cls.__dict__.get('__annotations__', {})
    use_middleware_records: list[UseMiddlewareRecord] = []
    for k, v in getmembers(cls):
        # use_dep
        if hasattr(v, REQ_DEP_PLACEHOLDER):
            use_dep_dict.update({k: (cls_anno.get(k), v)})
        # collect use_middleware's value
        elif (
                isinstance(v, BlankPlaceholder)
                and (attr := getattr(v, USE_MIDDLEWARE_FIELD_PLACEHOLDER))
                and isinstance(attr, UseMiddlewareRecord)
        ):
            use_middleware_records.append(attr)
    return use_dep_dict, use_middleware_records


def trans_endpoint(
        instance: Any,
        endpoint: Callable,
        use_dep_dict: dict,
        use_middleware_records: list[UseMiddlewareRecord]
):
    """trans endpoint
    1. change `self` param's default ===> Depends(lambda: instance). set kind ===> 'KEYWORD_ONLY';
    2. add use_dep params. replace params. replace signature.
    > or
    1. new function(without 'self' param) extend endpoint(need add 'self' when call it);
    2. add use_dep params. replace params. replace signature.


    add middleware to WebSocket instance of websocket endpoint'params if is_websocket
    """
    params: list[Parameter] = list(signature(endpoint).parameters.values())
    has_self = params[0].name == 'self' if params else False
    if has_self:
        params.pop(0)

    # add use_dep's deps
    for k, v in use_dep_dict.items():
        req_name = f'{USE_DEP_PREFIX_IN_ENDPOINT}_{k}'
        params.append(Parameter(
            name=req_name, kind=Parameter.KEYWORD_ONLY, annotation=v[0], default=v[1]))
    # replace endpoint

    @wraps(endpoint)
    async def new_endpoint(*args, **kwargs):
        for k, v in use_dep_dict.items():
            req_name = f'{USE_DEP_PREFIX_IN_ENDPOINT}_{k}'
            setattr(instance, k, kwargs.pop(req_name))
            kwargs.get(req_name)  # auto call use_dep result
        for k, v in kwargs.items():
            # add websocket middleware for this endpoint
            if isinstance(v, FastAPIWebSocket):
                for record in use_middleware_records:
                    record.add_ws_middleware(v)
        new_args = (instance, *args) if has_self else args
        if iscoroutinefunction(endpoint):
            return await endpoint(*new_args, **kwargs)
        else:
            return endpoint(*new_args, **kwargs)

    setattr(new_endpoint, '__signature__', signature(
        new_endpoint).replace(parameters=params))

    return new_endpoint


def resolve_endpoint(
        anchor: APIRouter,
        api_route: EndpointRouteRecord,
        instance: Any,
        use_deps_dict: dict,
        prefix: str,
        use_middleware_records: list[UseMiddlewareRecord],
):
    """
    1. trans_endpoint
    2. add websocket middleware to websocket endpoint
    3. mount endpoint to anchor and add middleware"""
    path = anchor.prefix + api_route.record.path
    # if http, add to use_middleware_records
    if isinstance(api_route.record, BaseHttpRouteItem):
        urls_methods = [(path, method.upper())
                        for method in api_route.record.methods]
        # only first can do well actually
        for r in use_middleware_records:
            r.http_urls_methods.extend(urls_methods)
    new_endpoint = trans_endpoint(
        instance, api_route.record.endpoint, use_deps_dict, use_middleware_records
    )
    api_route.record.replace_endpoint(
        new_endpoint).add_prefix(prefix).mount_to(anchor)


def resolve_class_based_view(
        anchor: APIRouter, route_record: PrefixRouteRecord[RouterCls], prefix: str, app_record: AppRecord
):
    """
    Args:
        anchor (APIRouter): mount anchor
        route_record (PrefixRouteRecord[RouterCls])
        prefix (str): prefix of request path
        app_record (AppRecord): app record
    """
    cls: type[RouterCls] = route_record.cls
    use_deps_dict, use_middleware_records = get_use_result(cls)
    instance: RouterCls = inject_init_deps_and_get_instance(cls)

    for v in cls.__dict__.values():
        if hasattr(v, CONTROLLER_ROUTE_RECORD) and (attr := getattr(v, CONTROLLER_ROUTE_RECORD)):
            new_prefix = prefix + route_record.prefix
            if isinstance(attr, EndpointRouteRecord):
                resolve_endpoint(anchor, attr, instance, use_deps_dict,
                                 new_prefix, use_middleware_records)
            elif isinstance(attr, PrefixRouteRecord):
                resolve_class_based_view(anchor, attr, new_prefix, app_record)
    # add middleware
    if use_middleware_records:
        reduce(lambda a, b: a + b,
               use_middleware_records).add_http_middleware(app_record.app)
    return instance


class Controller(APIRouter):
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
            generate_unique_id_function: Callable[[
                APIRoute], str] = Default(generate_unique_id),
            # 被导入后是否自动include到app下
            auto_include: bool = True,
            # 若不自动include，可通过 类型+名字 依赖注入的方式获取APIRouter实例，名字是什么，默认是被装饰的类/函数的__name__
            dep_name: str = ''
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
        self.auto_include = auto_include
        self.dep_name = dep_name

    def __call__(self, cls: type[RouterCls]) -> type[RouterCls]:
        def task(app_record: AppRecord):
            resolve_class_based_view(
                self, PrefixRouteRecord(cls), '', app_record)
            if self.auto_include:
                app_record.app.include_router(self)
            else:
                dep_name = self.dep_name or cls.__name__
                dep_store.add_dep_by_name(APIRouter, dep_name, self)
        task_store.schedule(get_call_filename(), task)
        return cls

    def __getattribute__(self, k: str):
        attr = super().__getattribute__(k)
        if k in [*LowerHttpMethod, 'api_route', 'websocket', 'websocket_route']:

            def decorator(*args, **kwds):
                def wrapper(endpoint):
                    # @Controller(...).websocket(...)  @Controller(...).websocket_route(...)
                    if k in ['websocket', 'websocket_route']:
                        WebSocketRouteItem(
                            endpoint, *args, **kwds).mount_to(self)
                    elif k == 'api_route':
                        BaseHttpRouteItem(endpoint, *args, **
                                          kwds).mount_to(self)
                    else:
                        BaseHttpRouteItem(endpoint, methods=[
                                          k], *args, **kwds).mount_to(self)

                    def task(app_record: AppRecord):
                        if self.auto_include:
                            app_record.app.include_router(self)
                        else:
                            dep_name = self.dep_name or endpoint.__name__
                            dep_store.add_dep_by_name(
                                APIRouter, dep_name, self)
                    task_store.schedule(get_call_filename(), task)
                    return endpoint
                return wrapper
            return decorator
        return attr


# ------------------------------------------------------Request Mapping ----------------------------------------------------- #


class Req(BaseHttpRouteItemWithoutEndpoint):
    def __call__(self, endpoint: T) -> T:
        route_item = BaseHttpRouteItem(
            endpoint=endpoint, **self.dict).format_methods()
        # 顶层
        if len(endpoint.__qualname__.split('.')) == 1:
            task_store.schedule(get_call_filename(
                2), lambda app_record: route_item.mount_to(app_record.app))
        else:
            # 作为Controller的方法
            self.path = trans_path(self.path)
            route_record = EndpointRouteRecord(route_item)
            setattr(endpoint, CONTROLLER_ROUTE_RECORD, route_record)
        return endpoint


class Get(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict)(endpoint)


class Post(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['POST'])(endpoint)


class Put(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['PUT'])(endpoint)


class Delete(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['DELETE'])(endpoint)


class Head(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['HEAD'])(endpoint)


class Patch(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['PATCH'])(endpoint)


class Trace(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['TRACE'])(endpoint)


class Options(SM):
    def __call__(self, endpoint: T) -> T:
        return Req(**self.dict, methods=['OPTIONS'])(endpoint)


class WebSocket(WebSocketRouteItemWithoutEndpoint):
    def __call__(self, endpoint: T) -> T:
        route_item = WebSocketRouteItem(endpoint=endpoint, **self.dict)
        # 顶层
        if len(endpoint.__qualname__.split('.')) == 1:
            task_store.schedule(
                get_call_filename(), lambda app_record: route_item.mount_to(app_record.app))
        else:
            # 作为Controller的方法
            self.path = trans_path(self.path)
            route_record = EndpointRouteRecord(route_item)
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
