import inspect
from collections.abc import Callable, Sequence
from enum import Enum
from functools import wraps
from inspect import Parameter, signature
from typing import Any, Generic, TypeVar, get_type_hints, no_type_check

from fastapi import APIRouter, Depends, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from fastapi_boot.constants import CONTROLLER_ROUTE_RECORD, REQ_DEP_PLACEHOLDER, ControllerRoutePlaceholderContainer
from fastapi_boot.enums import RequestMethodEnum, RequestMethodStrEnum
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.model.route import BaseHttpRouteItem, EndpointRouteRecord, PrefixRouteRecord, WebSocketRouteItem
from fastapi_boot.model.scan import MountedTask, Symbol
from fastapi_boot.utils.deps import try_resolve_controller_init_params
from fastapi_boot.utils.pure import trans_path

T = TypeVar('T')


# -------------------------------------------------------- 依赖 -------------------------------------------------------- #
def update_proj_deps_params_to_depends(params: list[Parameter], proj_deps_dict: dict[str, Any]):
    """
    1. 把参数params中项目依赖参数proj_deps_dict的默认值改为Depends()，避免被识别成查询参数；
    2. 把上面找到的参数类型改为关键字参数，避免顺序出现错误；

    Args:
        params (list[Parameter]): Controller或Prefix装饰类的__init__的参数
        proj_deps_dict (dict[str, Any]): 找到的项目依赖，key => 依赖名，value => 注入的依赖值
    """
    for idx, param in enumerate(params):
        if param.name in proj_deps_dict and (default := proj_deps_dict.get(param.name)):
            params[idx] = param.replace(kind=Parameter.KEYWORD_ONLY, default=Depends(lambda: default))


def resolve_req_dependencies(cls: type, proj_deps_dict: dict[str, Any]):
    """处理请求方法的依赖，即使用了usedep的静态变量

    Args:
        cls (type): Controller或Prefix装饰的类
        proj_deps_dict (dict[str, Any]): 已经注入的__init__方法中的项目依赖
    """
    # 1. 获得新的init方法签名
    old_init = cls.__init__
    old_sign = inspect.signature(cls)
    old_params = list(old_sign.parameters.values())[1:]
    new_params = [i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)]
    dep_names: list[str] = []
    for name, value in cls.__dict__.items():
        hint = get_type_hints(cls).get(name)
        if hasattr(value, REQ_DEP_PLACEHOLDER):
            dep_names.append(name)
            new_params.append(Parameter(name, Parameter.KEYWORD_ONLY, annotation=hint, default=value))
    # 替换已注入参数的kind和default
    update_proj_deps_params_to_depends(new_params, proj_deps_dict)
    # 新方法的签名
    new_sign = old_sign.replace(parameters=new_params)

    # 3。 得到新的init
    def new_init(self, *args, **kwds):
        # 删除usedep变量名，并设置到self上
        for name in dep_names:
            value = kwds.pop(name)
            setattr(self, name, value)
        # 旧的init只需要项目依赖
        old_init(self, **proj_deps_dict)

    setattr(cls, '__signature__', new_sign)
    setattr(cls, '__init__', new_init)


def inject_proj_deps(cls: type, symbol: Symbol):
    """注入项目中的依赖

    Args:
        cls (type): 所在的类
        symbol (Symbol): 调用栈文件系统路径

    Returns:
        tuple[InjectParamsResult, Callable]: tuple(注入的结果，该类被wraps装饰后的函数)
    """

    @wraps(cls)
    def decorator(*args, **kwds):
        return cls(*args, **kwds)

    init_params = inspect.signature(cls.__init__).parameters
    init_params_dict = {k: v for k, v in init_params.items() if k != 'self'}
    res = try_resolve_controller_init_params(decorator, init_params_dict, symbol)
    return res, decorator


# -------------------------------------------------------- 路由 -------------------------------------------------------- #
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
            dic.update({'methods': [method]})
            anchor.add_api_route(**dic)


def resolve_use_router_path(
    path_list: list[str],
    prefix: str,
    total_route_record_list: list[BaseHttpRouteItem | WebSocketRouteItem],
) -> APIRouter:
    """use_router的路由提取

    Args:
        path_list (list[str]): 要提取的请求路径列表
        prefix (str): 前缀，一般使用Controller的前缀
        total_route_record_list (list[BaseHttpRouteItem  |  WebSocketRouteItem]): 总的路由记录列表，已记录完整

    Returns:
        APIRouter:
    """
    res = APIRouter()
    # 如果是空就全挂载
    if len(path_list) == 0:
        for record in total_route_record_list:
            record.path = prefix + record.path
            add_single_api_route(record, res)
    else:
        # 提取出use_router的path内的路由
        for path in path_list:
            for record in total_route_record_list:
                if trans_path(path) == record.path:
                    record.path = prefix + record.path
                    add_single_api_route(record, res)
    return res


def resolve_endpoint(
    ctrl: 'Controller',
    route_record: EndpointRouteRecord,
    cls: type[T],
    total_route_list: list[BaseHttpRouteItem | WebSocketRouteItem],
):
    """处理endpoint

    Args:
        ctrl (Controller): 控制器实例
        route_record (EndpointRouteRecord): 路由记录
        cls (type): 该endpoint所在的类，用于初始化它的self
        total_route_list (list[BaseHttpRouteItem | WebSocketRouteItem]): 控制器的所有请求记录
    """
    api_route = route_record.api_route
    old_sign = signature(api_route.endpoint)
    params = list(old_sign.parameters.values())
    if len(params) > 0 and params[0].name == 'self':
        params[0] = params[0].replace(kind=Parameter.KEYWORD_ONLY, default=Depends(cls))
    new_sign = old_sign.replace(parameters=params)
    setattr(api_route.endpoint, '__signature__', new_sign)

    total_route_list.append(api_route)
    # 挂载路由
    add_single_api_route(api_route, ctrl)


def resolve_prefix(
    ctrl: 'Controller',
    route_record: PrefixRouteRecord,
    symbol: Symbol,
    total_route_list: list[BaseHttpRouteItem | WebSocketRouteItem],
):
    """处理Prefix装饰的类

    Args:
        ctrl (Controller): Controlelr实例
        route_record (PrefixRouteRecord): 路由记录
        symbol (Symbol): 调用位置
        total_route_list (list[BaseHttpRouteItem | WebSocketRouteItem]): 控制器的所有请求路径，每添加一个endpoint就累积
    """
    cls = route_record.cls
    # 先注入项目的依赖
    res, _ = inject_proj_deps(cls, symbol)
    # 再修__init__中项目依赖的参数的kind和default，以及处理请求的依赖
    resolve_req_dependencies(cls, res.params)
    # 挂载路由
    for api_route in route_record.api_routes:
        if isinstance(api_route, EndpointRouteRecord):
            resolve_endpoint(ctrl, api_route, cls, total_route_list)
        elif isinstance(api_route, PrefixRouteRecord):
            # 把该prefix下的子endpoint路由的self挂载到它装饰的类的实例
            resolve_prefix(ctrl, api_route, symbol, total_route_list)


# ----------------------------------------------------- 控制器挂载到应用 ---------------------------------------------------- #
def mount_router_and_add_controller(symbol: Symbol, ctrl: 'Controller'):
    """把Controller挂载到应用、把Controller记录添加到应用

    Args:
        symbol (Symbol): 调用栈文件系统路径
        ctrl (Controller): 控制器实例
    """

    def task():
        app = GlobalVar.get_app(symbol.stack_path)
        if not app:
            return False
        # 设置了扫描才添加路由
        if app.config.scan:
            app.app.include_router(ctrl)
        # 前面没收集前缀，这里需要加上Controller的prefix
        for r in ctrl.total_route_record_list:
            r.path = ctrl.prefix + r.path
        return True

    if not task():
        GlobalVar.add_app_stack_path_task(MountedTask(symbol, task))


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
        # 总的路由记录列表，挂载过程中不断累积，用于匹配use_router的路径、提取路由记录用于rpc
        self.total_route_record_list: list[BaseHttpRouteItem | WebSocketRouteItem] = []

    @no_type_check
    def __call__(self, cls: type[T]) -> T:
        symbol = Symbol.from_obj(cls)
        # 先注入项目的依赖
        res, decorator = inject_proj_deps(cls, symbol)
        # 再修改__init__中项目依赖的参数的kind和default，以及处理请求的依赖
        resolve_req_dependencies(cls, res.params)
        # 需要替换的use_router静态属性名
        use_router_dict: dict[str, list[str]] = {}
        # 遍历，挂载，处理self
        for k, v in cls.__dict__.items():
            if isinstance(v, ControllerRoutePlaceholderContainer):
                # 路由占位符，更新decorator的就行了，最终返回的是decorator
                use_router_dict.update({k: v.paths})
            elif hasattr(v, CONTROLLER_ROUTE_RECORD) and (attr := getattr(v, CONTROLLER_ROUTE_RECORD)):
                if isinstance(attr, EndpointRouteRecord):
                    resolve_endpoint(self, attr, cls, self.total_route_record_list)
                elif isinstance(attr, PrefixRouteRecord):
                    # prefix内的endpoint的self指向prefix装饰的类的实例
                    resolve_prefix(self, attr, symbol, self.total_route_record_list)
        # 替换use_router
        for k, v in use_router_dict.items():
            setattr(decorator, k, resolve_use_router_path(v, self.prefix, self.total_route_record_list))
        # 把控制器挂载到应用
        mount_router_and_add_controller(symbol, self)
        return decorator

    def __getattribute__(self, k: str):
        attr = super().__getattribute__(k)
        if k in RequestMethodStrEnum.__args__ or k == 'api_route':
            # include_router的时候，如果self没有routes，添加不了
            # 所以外面再包两层，等self里面有路由了再挂载到app
            def decorator(*args, **kwds):
                # 转换一下path
                if len(args) > 0 and isinstance((path := args[0]), str):
                    # 如果在args中
                    args = [trans_path(path), *args[1:]]
                else:
                    path = trans_path(kwds.get('path', ""))
                    kwds.update({'path': path})

                def wrapper(endpoint):
                    symbol = Symbol.from_obj(endpoint)
                    if k.upper() == RequestMethodEnum.WEBSOCKET:
                        self.total_route_record_list = [WebSocketRouteItem(endpoint, *args, **kwds)]
                        add_single_api_route(self.total_route_record_list[0], self)
                    elif k == 'api_route':
                        methods: list[RequestMethodStrEnum | RequestMethodEnum] = (
                            kwds.pop('methods') if 'methods' in kwds and len(kwds['methods']) > 0 else ['get']
                        )
                        method = methods[0]
                        case_enum = isinstance(method, RequestMethodEnum) and method == RequestMethodEnum.WEBSOCKET
                        case_str_enum = method == 'websocket' or method == 'WEBSOCKET'
                        if len(methods) == 1 and (case_enum or case_str_enum):
                            self.total_route_record_list = [WebSocketRouteItem(endpoint, *args, **kwds)]
                            add_single_api_route(self.total_route_record_list[0], self)
                        else:
                            # 默认传多个没有websocket
                            self.total_route_record_list = [
                                BaseHttpRouteItem(endpoint, methods=[method], *args, **kwds) for method in methods
                            ]
                            add_single_api_route(BaseHttpRouteItem(endpoint, methods=methods, *args, **kwds), self)
                    else:
                        # 单个方法
                        self.total_route_record_list = [BaseHttpRouteItem(endpoint, methods=[k], *args, **kwds)]
                        add_single_api_route(self.total_route_record_list[0], self)
                    # 这里用endpoint随便传了，FBV用不到self
                    mount_router_and_add_controller(symbol, self)
                    setattr(endpoint, 'router', self)
                    return endpoint

                return wrapper

            return decorator
        return attr
