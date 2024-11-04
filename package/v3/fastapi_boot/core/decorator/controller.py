from collections.abc import Callable, Sequence
from enum import Enum
from functools import wraps
import inspect
from inspect import Parameter
from typing import Any, Generic, TypeVar, get_type_hints, no_type_check
from fastapi import APIRouter, Depends, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import Lifespan, ASGIApp


from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.constants import ControllerRoutePlaceholderContainer, REQ_DEP_PLACEHOLDER, CONTROLLER_ROUTE_RECORD
from fastapi_boot.enums import RequestMethodEnum
from fastapi_boot.model.route import BaseHttpRouteItem, EndpointRouteRecord, PrefixRouteRecord, WebSocketRouteItem
from fastapi_boot.model.scan import InjectParamsResult, MountedTask, Symbol
from fastapi_boot.utils.deps import try_resolve_controller_init_params
from fastapi_boot.utils.pure import trans_path

T = TypeVar("T")


# ----------------------------------------------- 处理endpoint的self以及挂载到控制器 ---------------------------------------------- #
def resolve_endpoint_self(func: Callable, dep: type):
    """处理endpoint的self，dep是被装饰的类，所以控制器在每次有请求时就会重新实例化...

    Args:
        func (Callable): 路由请求映射方法
        dep (type): 需要把这个方法的self变成谁的实例
    """
    old_params = list(inspect.signature(func).parameters.values())
    # 如果第一个参数不是self，不需要处理
    if not old_params or old_params[0].name != "self":
        return
    old_sign = inspect.signature(func)
    old_first_param = old_params[0]
    new_first_param = old_first_param.replace(default=Depends(dep))
    new_params = [new_first_param] + [p.replace(kind=inspect.Parameter.KEYWORD_ONLY) for p in old_params[1:]]
    new_sign = old_sign.replace(parameters=new_params)
    setattr(func, "__signature__", new_sign)


def add_single_api_route(api_route: BaseHttpRouteItem | WebSocketRouteItem, anchor: APIRouter):
    """挂载单个endpoint

    Args:
        api_route (BaseHttpRouteItem | WebSocketRouteItem): 基础路由或websocket路由
        anchor (APIRouter): 挂载点
    """
    if isinstance(api_route, WebSocketRouteItem):
        anchor.add_api_websocket_route(**api_route.dict)
    else:
        for method in api_route.methods:
            dic = api_route.dict
            dic.update({"methods": [method]})
            anchor.add_api_route(**dic)


def resolve_endpoint(
    ctrl: "Controller",
    route_record: EndpointRouteRecord,
    cls: type,
    total_route_list: list[BaseHttpRouteItem | WebSocketRouteItem],
    prefix: str = "",
):
    """把endpoint挂载到控制器上

    Args:
        ctrl (Controller): 控制器实例
        route_record (EndpointRouteRecord): 路由记录
        cls (type): 该endpoint所在的类，用于初始化它的self
        total_route_list (list[BaseHttpRouteItem | WebSocketRouteItem]): 控制器的所有请求记录
        prefix (str, optional): endpoint路径的前缀. Defaults to "".
    """
    api_route = route_record.api_route
    # 处理self
    resolve_endpoint_self(api_route.endpoint, cls)
    # 处理前缀
    api_route.path = prefix + route_record.api_route.path
    total_route_list.append(api_route)
    # 挂载路由
    add_single_api_route(api_route, ctrl)


# ------------------------------------------------------- 处理依赖 ------------------------------------------------------- #
def update_proj_deps_params_to_depends(params: list[Parameter], proj_deps_dict: dict[str, Any]):
    """
    1. 把参数params中项目依赖参数proj_deps_dict的默认值改为Depends()，避免被识别成查询参数；
    2. 把上面找到的参数类型改为关键字参数，避免顺序出现错误；

    Args:
        params (list[Parameter]): Controller或Prefix装饰类的__init__的参数
        proj_deps_dict (dict[str, Any]): 找到的项目依赖，key => 依赖名，value => 注入的依赖值
    """
    for idx, param in enumerate(params):
        if param.name in proj_deps_dict and (defaulr := proj_deps_dict.get(param.name)):
            params[idx] = param.replace(kind=Parameter.KEYWORD_ONLY, default=Depends(lambda: defaulr))


def resolve_req_dependencies(cls: type[Any], proj_deps_dict: dict[str, Any]):
    """处理请求方法的依赖，即使用了usedep的静态变量

    Args:
        cls (type[Any]): Controller或Prefix装饰的类
        proj_deps_dict (dict[str, Any]): 已经注入的__init__方法中的项目依赖
    """
    # 1. 获得新的init方法签名
    old_init = cls.__init__
    old_sign = inspect.signature(cls)
    old_params = list(old_sign.parameters.values())[1:]
    new_params: list[Parameter] = [
        i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]
    dep_names: list[str] = []
    for name, value in cls.__dict__.items():
        hint = get_type_hints(cls).get(name)
        if hasattr(value, REQ_DEP_PLACEHOLDER):
            dep_names.append(name)
            new_params.append(Parameter(name, Parameter.KEYWORD_ONLY, annotation=hint, default=value))
    # 用half_params替换new_params中的同名参数的kind和default属性
    update_proj_deps_params_to_depends(new_params, proj_deps_dict)
    # 新方法的签名
    new_sign = old_sign.replace(parameters=new_params)

    # 3。 得到新的init
    def new_init(self, *args, **kwargs):
        # 删除usedep变量名，并设置到self上
        for name in dep_names:
            value = kwargs.pop(name)
            setattr(self, name, value)
        # 旧的init只需要项目依赖
        old_init(self, **proj_deps_dict)

    setattr(cls, "__signature__", new_sign)
    setattr(cls, "__init__", new_init)


def resolve_proj_deps(cls: Any, stack_path: str) -> tuple[InjectParamsResult, Callable]:
    """注入项目中的依赖

    Args:
        cls (Any): 所在的类
        stack_path (str): 调用栈文件系统路径

    Returns:
        tuple[InjectParamsResult, Callable]: tuple(注入的结果，该类被wraps装饰后的函数)
    """

    @wraps(cls)
    def decorator(*args, **kwds):
        return cls(*args, **kwds)

    init_params = inspect.signature(cls.__init__).parameters
    init_params_dict = {k: v for k, v in init_params.items() if k != "self"}
    res = try_resolve_controller_init_params(decorator, init_params_dict, stack_path)
    return res, decorator


# ---------------------------------------------------- 递归处理Prefix ---------------------------------------------------- #
def resolve_prefix(
    ctrl: "Controller",
    route_record: PrefixRouteRecord,
    stack_path: str,
    total_route_list: list[BaseHttpRouteItem | WebSocketRouteItem],
    prefix: str = "",
):
    """处理Prefix装饰的类

    Args:
        ctrl (Controller): Controlelr实例
        route_record (PrefixRouteRecord): 路由记录
        stack_path (str): 调用栈文件系统路径
        total_route_list (list[BaseHttpRouteItem | WebSocketRouteItem]): 控制器的所有请求路径，每添加一个endpoint就累积
        prefix (str, optional): 路径前缀. Defaults to "".
    """
    cls = route_record.cls
    # 先注入项目的依赖
    res, decorator = resolve_proj_deps(cls, stack_path)
    # 再修__init__中项目依赖的参数的kind和default，以及处理请求的依赖
    resolve_req_dependencies(cls, res.params)
    # 更新前缀
    new_prefix = prefix + route_record.prefix
    # 挂载路由
    for api_route in route_record.api_routes:
        if isinstance(api_route, EndpointRouteRecord):
            resolve_endpoint(ctrl, api_route, cls, total_route_list, new_prefix)
        elif isinstance(api_route, PrefixRouteRecord):
            # 把该prefix下的子endpoint路由的self挂载到它装饰的类的实例
            resolve_prefix(ctrl, api_route, stack_path, total_route_list, new_prefix)


# ----------------------------------------------------- 控制器挂载到子应用 ---------------------------------------------------- #
def mount_controller_to_app(symbol: Symbol, ctrl: "Controller"):
    """把Controller挂载到应用

    Args:
        symbol (Symbol): 调用栈文件系统路径
        ctrl (Controller): 控制器实例
    """

    def task():
        app = GlobalVar.get_app(symbol.stack_path)
        if app.config.scan:
            app.app.include_router(ctrl)

    try:
        task()
    except:
        GlobalVar.add_app_task(MountedTask(symbol, task))


# -------------------------------------------------- 处理use_router的路径 ------------------------------------------------- #
def resolve_use_router_path(
    path_list: list[str],
    prefix: str,
    total_route_record: list[BaseHttpRouteItem | WebSocketRouteItem],
) -> APIRouter:
    """use_router的路由提取

    Args:
        path_list (list[str]): 要提取的请求路径列表
        prefix (str): 前缀，一般使用Controller的前缀
        total_route_record (list[BaseHttpRouteItem  |  WebSocketRouteItem]): 总的路由记录列表，已记录完整

    Returns:
        APIRouter:
    """
    res = APIRouter()
    # 如果是空就全挂载
    if len(path_list) == 0:
        for record in total_route_record:
            record.path = prefix + record.path
            add_single_api_route(record, res)
    else:
        # 提取出use_router的path内的路由
        for path in path_list:
            for record in total_route_record:
                if trans_path(path) == record.path:
                    record.path = prefix + record.path
                    add_single_api_route(record, res)
    return res


# -------------------------------------------------------- 控制器 ------------------------------------------------------- #
class Controller(APIRouter, Generic[T]):
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

    @no_type_check
    def __call__(self, cls: type[T]) -> T:
        symbol = Symbol.from_obj(cls)
        # 先注入项目的依赖
        res, decorator = resolve_proj_deps(cls, symbol.stack_path)
        # 再修__init__中项目依赖的参数的kind和default，以及处理请求的依赖
        resolve_req_dependencies(cls, res.params)
        # 总的路由记录列表，挂载过程中不断累积，用于匹配use_router的路径
        total_route_record: list[BaseHttpRouteItem | WebSocketRouteItem] = []
        # 需要替换的use_router静态属性名
        use_router_dict: dict[str, list[str]] = {}
        # 遍历，挂载，处理self
        for k, v in cls.__dict__.items():
            if isinstance(v, ControllerRoutePlaceholderContainer):
                # 路由占位符，更新decorator的就行了，最终返回的是decorator
                use_router_dict.update({k: v.paths})
            elif hasattr(v, CONTROLLER_ROUTE_RECORD) and (attr := getattr(v, CONTROLLER_ROUTE_RECORD)):
                if isinstance(attr, EndpointRouteRecord):
                    resolve_endpoint(self, attr, cls, total_route_record)
                elif isinstance(attr, PrefixRouteRecord):
                    # prefix内的endpoint的self指向prefix装饰的类的实例
                    resolve_prefix(self, attr, symbol.stack_path, total_route_record)
        # 替换use_router
        for k, v in use_router_dict.items():
            setattr(decorator, k, resolve_use_router_path(v, self.prefix, total_route_record))
        # 把控制器挂载到应用
        mount_controller_to_app(symbol, self)
        return decorator

    def __getattribute__(self, k: str):
        attr = super().__getattribute__(k)
        if RequestMethodEnum.contains(k) or k == "api_route":
            # include_router的时候，如果self没有routes，添加不了
            # 所以外面再包两层，等self里面有路由了再挂载到app
            def decorator(*args, **kwargs):
                def wrapper(endpoint):
                    symbol = Symbol.from_obj(endpoint)
                    if k.upper() == RequestMethodEnum.WEBSOCKET:
                        self.add_api_websocket_route(*args, **kwargs, endpoint=endpoint)
                    else:
                        self.add_api_route(*args, **kwargs, methods=[k], endpoint=endpoint)

                    # 挂载
                    mount_controller_to_app(symbol, self)
                    return endpoint

                return wrapper

            return decorator
        return attr
