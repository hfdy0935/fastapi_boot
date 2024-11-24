from collections.abc import Callable, Sequence
from enum import Enum
from inspect import Parameter, signature
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, Depends, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from fastapi_boot.constants import (
    API_ROUTER_KEY_IN_CONTROLLER,
    CONTROLLER_ROUTE_RECORD,
    REQ_DEP_PLACEHOLDER,
    USE_DEP_PREFIX_IN_ENDPOINT,
)
from fastapi_boot.enums import RequestMethodEnum, RequestMethodStrEnum
from fastapi_boot.model import BaseHttpRouteItem, EndpointRouteRecord, PrefixRouteRecord, WebSocketRouteItem
from fastapi_boot.util import inject_dependency_init_deps, trans_path
from fastapi_boot.vars import TypeDepRecord, dep_store

T = TypeVar('T')


def update_default_value_of_param(p: Parameter, default: Any):
    """set default value for param p"""
    return p.replace(default=Depends(lambda: default), kind=Parameter.KEYWORD_ONLY)


def get_use_deps(cls: type[T]):
    use_dep_dict = {}
    cls_anno: dict = cls.__dict__.get('__annotations__', {})
    for k, v in cls.__dict__.items():
        if hasattr(v, REQ_DEP_PLACEHOLDER):
            use_dep_dict.update({k: (cls_anno.get(k), v)})
    return use_dep_dict


def trans_endpoint(instance: Any, endpoint: Callable, use_dep_dict: dict):
    """trans endpoint
    1. add `self` param's default ===> Depends(lambda: instance)
    2. add the dependencies of `use_dep` to endpoint, return the new endpoint
    """
    params: list[Parameter] = list(signature(endpoint).parameters.values())
    # 1. all to keyword_only，replace self
    for idx, p in enumerate(params):
        if idx == 0 and p.name == 'self':
            params[0] = params[0].replace(default=Depends(lambda: instance), kind=Parameter.KEYWORD_ONLY)
        else:
            params[idx] = params[idx].replace(kind=Parameter.KEYWORD_ONLY)
    # 2. add use_dep's deps
    for k, v in use_dep_dict.items():
        req_name = USE_DEP_PREFIX_IN_ENDPOINT + k
        params.append(Parameter(name=req_name, kind=Parameter.KEYWORD_ONLY, annotation=v[0], default=v[1]))
    # 3. replace old endpoint

    def new_endpoint(self, *args, **kwargs):
        for k in use_dep_dict.keys():
            req_name = USE_DEP_PREFIX_IN_ENDPOINT + k
            setattr(self, k, kwargs.pop(req_name))
        return endpoint(self, *args, **kwargs)

    setattr(new_endpoint, '__signature__', signature(endpoint).replace(parameters=params))
    return new_endpoint


def mount_endpoint_to_anchor(
    anchor: APIRouter, api_route: EndpointRouteRecord, instance: Any, use_deps_dict: dict, prefix: str
):
    """mount endpoint to anchor"""
    new_endpoint = trans_endpoint(instance, api_route.record.endpoint, use_dep_dict=use_deps_dict)
    api_route.record.replace_endpoint(new_endpoint).add_prefix(prefix).mount_to(anchor)


def resolve_class_based_view(anchor: APIRouter, super_instance: Any, route_record: PrefixRouteRecord[T], prefix: str):
    """

    Args:
        anchor (APIRouter): mount anchor
        super_instance (Any): class's instance of route_record.cls
        route_record (PrefixRouteRecord[T])
        prefix (str): prefix of request path
    """
    cls: type[T] = route_record.cls
    use_deps_dict = get_use_deps(cls)
    instance: T = inject_dependency_init_deps(cls)

    for v in cls.__dict__.values():
        if hasattr(v, CONTROLLER_ROUTE_RECORD) and (attr := getattr(v, CONTROLLER_ROUTE_RECORD)):
            new_prefix = prefix + route_record.prefix
            if isinstance(attr, EndpointRouteRecord):
                mount_endpoint_to_anchor(anchor, attr, instance, use_deps_dict, new_prefix)
            elif isinstance(attr, PrefixRouteRecord):
                resolve_class_based_view(anchor, instance, attr, new_prefix)
    # collect controller as a type dependency
    dep_store.add_dep_by_type(TypeDepRecord(cls, instance))
    return instance


# -------------------------------------------------------- 控制器 ------------------------------------------------------- #


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

    def __call__(self, cls: type[T]) -> T:
        instance = resolve_class_based_view(self, lambda: ..., PrefixRouteRecord(cls), '')
        setattr(cls, API_ROUTER_KEY_IN_CONTROLLER, self)
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
                    setattr(endpoint, API_ROUTER_KEY_IN_CONTROLLER, self)
                    return endpoint

                return wrapper

            return decorator
        return attr
