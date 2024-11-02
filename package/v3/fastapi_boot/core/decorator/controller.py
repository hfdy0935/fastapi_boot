from collections import OrderedDict
from collections.abc import Callable, Sequence
from enum import Enum
import inspect
from inspect import Parameter
from typing import Any, get_type_hints
import typing
from fastapi import APIRouter, Depends, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import Lifespan, ASGIApp

from fastapi_boot.core.inject import find_dependency
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.constants import (
    DEP_PLACEHOLDER,
    ROUTE_RECORD,
    DepsPlaceholder,
)
from fastapi_boot.enums import InjectType, RequestMethodEnum
from fastapi_boot.exception import InjectFailException
from fastapi_boot.model.route import EndpointRouteRecord, PrefixReoutRecord, WebSocketRouteItem
from fastapi_boot.model.scan import Symbol
from fastapi_boot.utils import get_stack_path
from fastapi_boot.utils import trans_path


# ----------------------------------------------- 处理endpoint的self以及挂载路由 ---------------------------------------------- #


def resolve_endpoint_self(func: Callable, dep: type):
    """处理endpoint的self，dep是被装饰的类，所以控制器在每次有请求时就会重新实例化..."""
    old_params = list(inspect.signature(func).parameters.values())
    # 如果第一个参数不是self，不需要处理
    if (not (osn := [i.name for i in old_params])) or (osn and osn[0] != "self"):
        return func
    old_sign = inspect.signature(func)
    old_first_param = old_params[0]
    new_first_param = old_first_param.replace(default=Depends(dep))
    new_params = [new_first_param] + [p.replace(kind=inspect.Parameter.KEYWORD_ONLY) for p in old_params[1:]]
    new_sign = old_sign.replace(parameters=new_params)
    setattr(func, "__signature__", new_sign)


def resolve_endpoint(ctrl: "Controller", route_record: EndpointRouteRecord, cls: type, prefix: str = ""):
    """处理endpoint"""
    api_route = route_record.api_route
    # 处理self
    resolve_endpoint_self(api_route.endpoint, cls)
    # 处理前缀
    route_record.api_route.path = prefix + route_record.api_route.path
    # 挂载路由
    if isinstance(api_route, WebSocketRouteItem):
        ctrl.add_api_websocket_route(**api_route.dict)
    else:
        for method in api_route.methods:
            dic = api_route.dict
            dic.update({"methods": [method]})
            ctrl.add_api_route(**dic)


# ------------------------------------------------------- 处理依赖 ------------------------------------------------------- #
def __replace_init_params_to_depends(params_list: list[Parameter], k: str, v: Parameter, value: Any = None):
    """
    - 替换参数列表中对应参数为Depends(xxx)的依赖项，以便依赖注入，防止fastapi把它作为请求参数
    - 参数类型都改成KEYWORD_ONLY，防止顺序错误
    """
    for idx, p in enumerate(params_list):
        # 如果找到了就替换
        if p.name == k:
            new_parameter = Parameter(
                name=k, kind=Parameter.KEYWORD_ONLY, default=Depends(lambda: v), annotation=v.annotation
            )
            params_list[idx] = new_parameter
            return
    # 没找到就直接加到最后
    params_list.append(
        Parameter(name=k, kind=Parameter.KEYWORD_ONLY, default=Depends(lambda: value), annotation=v.annotation)
    )


def resolve_dependencies(cls: type[Any], stack_path: str):
    """处理依赖包括请求映射方法的依赖和依赖注入的依赖"""
    # 1. 获得新的init方法签名
    old_init = cls.__init__
    old_sign = inspect.signature(cls)
    old_params = list(old_sign.parameters.values())
    new_params = [i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)]
    dep_names = []
    for name, value in cls.__dict__.items():
        hint = get_type_hints(cls).get(name)
        if hasattr(value, DEP_PLACEHOLDER) and getattr(value, DEP_PLACEHOLDER) == DepsPlaceholder:
            dep_names.append(name)
            new_params.append(Parameter(name, Parameter.KEYWORD_ONLY, annotation=hint, default=value))

    # 新的初始化参数
    params = OrderedDict()
    for k, v in old_sign.parameters.items():
        if k == "self":  # 排除self
            continue
        elif (default_value := v.default) != inspect._empty:  # 有默认值
            params.update({k: default_value})
            __replace_init_params_to_depends(new_params, k, v)
        elif (v.annotation) == inspect._empty:  # 无类型无默认值，这里直接报错，不作为请求参数了
            raise InjectFailException(
                f"{InjectFailException.msg}，参数 {k} 没有写类型也没有默认值，位置：{Symbol.from_obj(cls).pos}"
            )
        else:
            # 有类型
            symbol = Symbol.from_obj(cls)
            # 如果是Annotated且第二个参数是name，则按依赖名注入
            if typing.get_origin(anno := v.annotation) == typing.Annotated:
                args = typing.get_args(anno)
                DepType, name, *_ = args
                # 第二个参数是字符串且不为''，默认作为依赖名
                if isinstance(name, str) and name:
                    instance = find_dependency(InjectType.NAME, symbol.stack_path, name=name)
                else:
                    # 按第一个类型注入依赖
                    instance = find_dependency(InjectType.TYPE, symbol.stack_path, DepType=DepType)
            elif isinstance(anno, str):
                # 如果是字符串，则默认为ForwardRef，按类型名注入
                instance = find_dependency(InjectType.NAME_OF_TYPE, symbol.stack_path, dep_type_name=v.annotation)
            else:
                # 按类型注入
                instance = find_dependency(InjectType.TYPE, symbol.stack_path, DepType=v.annotation)

            __replace_init_params_to_depends(new_params, k, v, instance)
            params.update({k: instance})

    # 新方法的签名
    new_sign = old_sign.replace(parameters=new_params)

    # 3。 得到新的init
    def new_init(self, *args, **kwargs):
        # 删除usedep变量名，并设置到self上
        for name in dep_names:
            value = kwargs.pop(name)
            setattr(self, name, value)
        old_init(self, **params)

    setattr(cls, "__signature__", new_sign)
    setattr(cls, "__init__", new_init)


def resolve_prefix(ctrl: "Controller", route_record: PrefixReoutRecord, stack_path: str, prefix: str = ""):
    """处理prefix类下的路由"""
    cls = route_record.cls
    # 处理依赖包括请求映射方法的依赖和依赖注入的依赖
    resolve_dependencies(route_record.cls, stack_path)
    # 更新前缀
    new_prefix = prefix + route_record.prefix
    # 挂载路由
    for api_route in route_record.api_routes:
        if isinstance(api_route, EndpointRouteRecord):
            resolve_endpoint(ctrl, api_route, cls, new_prefix)
        elif isinstance(api_route, PrefixReoutRecord):
            # 把该prefix下的子endpoint路由的self挂载到它装饰的类的实例
            resolve_prefix(ctrl, api_route, stack_path, new_prefix)


# -------------------------------------------------------- 控制器 ------------------------------------------------------- #
class Controller(APIRouter):
    def __init__(
        self,
        prefix: str = "",  # 为了把prefix改成位置参数，就重写了一个init...
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
    ) -> None:
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

    def __call__(self, cls: type[Any]):
        symbol = Symbol.from_obj(cls)
        application = GlobalVar.get_app(symbol.stack_path)

        # 处理依赖包括请求映射方法的依赖和依赖注入的依赖
        resolve_dependencies(cls, symbol.stack_path)
        # 遍历，挂载，处理self
        for v in cls.__dict__.values():
            if hasattr(v, ROUTE_RECORD) and (attr := getattr(v, ROUTE_RECORD)):
                if isinstance(attr, EndpointRouteRecord):
                    resolve_endpoint(self, attr, cls)
                elif isinstance(attr, PrefixReoutRecord):
                    # prefix内的endpoint的self指向prefix装饰的类的实例
                    resolve_prefix(self, attr, symbol.stack_path)
        application.app.include_router(self)

    def __getattribute__(self, k: str):
        attr = super().__getattribute__(k)
        stack_path = get_stack_path(1)
        if RequestMethodEnum.contains(k) or k == "api_route":
            # include_router的时候，如果self没有routes，添加不了
            # 所以外面再包两层，等self里面有路由了再挂载到app
            def decorator(*args, **kwargs):
                def wrapper(endpoint):
                    if k.upper() == RequestMethodEnum.WEBSOCKET:
                        self.add_api_websocket_route(*args, **kwargs, endpoint=endpoint)
                    else:
                        self.add_api_route(*args, **kwargs, methods=[k], endpoint=endpoint)
                    GlobalVar.get_app(stack_path).app.include_router(self)
                    return endpoint

                return wrapper

            return decorator
        return attr
