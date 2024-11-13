from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any, Generic, TypeVar, no_type_check

from fastapi import APIRouter, Response, params
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from fastapi_boot.constants import CBV_ENDPOINT, CONTROLLER_ROUTE_RECORD, ControllerRoutePlaceholderContainer
from fastapi_boot.core.decorator.controller.endpoint_util import trans_cbv_endpoint, trans_fbv_endpoint
from fastapi_boot.core.decorator.controller.hook_util import (
    add_single_api_route,
    resolve_proj_deps,
    resolve_req_dependencies,
)
from fastapi_boot.enums import RequestMethodEnum, RequestMethodStrEnum
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.model.route import BaseHttpRouteItem, EndpointRouteRecord, PrefixRouteRecord, WebSocketRouteItem
from fastapi_boot.model.scan import MountedTask, Symbol
from fastapi_boot.utils.pure import trans_path

T = TypeVar('T')


def resolve_endpoint(
    ctrl: 'Controller',
    route_record: EndpointRouteRecord,
    instance: Any,
    total_route_list: list[BaseHttpRouteItem | WebSocketRouteItem],
):
    """把endpoint挂载到控制器上

    Args:
        ctrl (Controller): 控制器实例
        route_record (EndpointRouteRecord): 路由记录
        instance (Any): 该endpoint所在的类的实例，用于初始化它的self
        total_route_list (list[BaseHttpRouteItem | WebSocketRouteItem]): 控制器的所有请求记录
    """
    api_route = route_record.api_route
    # 处理参数
    api_route.endpoint = trans_cbv_endpoint(api_route.endpoint, instance)
    # 记录是类的请求方法
    setattr(api_route.endpoint, CBV_ENDPOINT, True)
    total_route_list.append(api_route)
    # 挂载路由
    add_single_api_route(api_route, ctrl)


# ---------------------------------------------------- 递归处理Prefix ---------------------------------------------------- #
def resolve_prefix(
    ctrl: 'Controller',
    route_record: PrefixRouteRecord,
    stack_path: str,
    total_route_list: list[BaseHttpRouteItem | WebSocketRouteItem],
):
    """处理Prefix装饰的类

    Args:
        ctrl (Controller): Controlelr实例
        route_record (PrefixRouteRecord): 路由记录
        stack_path (str): 调用栈文件系统路径
        total_route_list (list[BaseHttpRouteItem | WebSocketRouteItem]): 控制器的所有请求路径，每添加一个endpoint就累积
    """
    cls = route_record.cls
    # 先注入项目的依赖
    res, _ = resolve_proj_deps(cls, stack_path)
    # 再修__init__中项目依赖的参数的kind和default，以及处理请求的依赖
    resolve_req_dependencies(cls, res.params)
    # 挂载路由
    for api_route in route_record.api_routes:
        if isinstance(api_route, EndpointRouteRecord):
            resolve_endpoint(ctrl, api_route, cls, total_route_list)
        elif isinstance(api_route, PrefixRouteRecord):
            # 把该prefix下的子endpoint路由的self挂载到它装饰的类的实例
            resolve_prefix(ctrl, api_route, stack_path, total_route_list)


# ----------------------------------------------------- 控制器挂载到应用 ---------------------------------------------------- #
def mount_router_and_add_controller(symbol: Symbol, ctrl: 'Controller'):
    """把Controller挂载到应用、把Controller记录添加到应用

    Args:
        symbol (Symbol): 调用栈文件系统路径
        ctrl (Controller): 控制器实例
    """

    def task():
        app = GlobalVar.get_app(symbol.stack_path)
        # 设置了扫描才添加路由
        if app.config.scan:
            app.app.include_router(ctrl)
        # 前面没收集前缀，这里需要加上Controller的prefix
        for r in ctrl.total_route_record_list:
            r.path = ctrl.prefix + r.path
        app.ra.add_controller_route_records(ctrl)

    try:
        task()
    except:
        GlobalVar.add_app_stack_path_task(MountedTask(symbol, task))


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
        # 被装饰的实例/函数，用于rpc时获取
        self.decorated_instance = None
        # 总的路由记录列表，挂载过程中不断累积，用于匹配use_router的路径、提取路由记录用于rpc
        self.total_route_record_list: list[BaseHttpRouteItem | WebSocketRouteItem] = []

    @no_type_check
    def __call__(self, cls: type[T]) -> T:
        symbol = Symbol.from_obj(cls)
        # 先注入项目的依赖
        res, decorator = resolve_proj_deps(cls, symbol.stack_path)
        # 再修__init__中项目依赖的参数的kind和default，以及处理请求的依赖
        resolve_req_dependencies(cls, res.params)
        # 控制器装饰的类的实例
        self.decorated_instance = cls()
        # 需要替换的use_router静态属性名
        use_router_dict: dict[str, list[str]] = {}
        # 遍历，挂载，处理self
        for k, v in cls.__dict__.items():
            if isinstance(v, ControllerRoutePlaceholderContainer):
                # 路由占位符，更新decorator的就行了，最终返回的是decorator
                use_router_dict.update({k: v.paths})
            elif hasattr(v, CONTROLLER_ROUTE_RECORD) and (attr := getattr(v, CONTROLLER_ROUTE_RECORD)):
                if isinstance(attr, EndpointRouteRecord):
                    resolve_endpoint(self, attr, self.decorated_instance, self.total_route_record_list)
                elif isinstance(attr, PrefixRouteRecord):
                    # prefix内的endpoint的self指向prefix装饰的类的实例
                    resolve_prefix(self, attr, symbol.stack_path, self.total_route_record_list)
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
                    # -------------------------------------------------------------------------------------------------------------------- #
                    # 查询参数处理，可以用dataclass、pydantic model
                    new_endpoint = trans_fbv_endpoint(endpoint)
                    self.decorated_instance = new_endpoint
                    if k.upper() == RequestMethodEnum.WEBSOCKET:
                        self.total_route_record_list = [WebSocketRouteItem(new_endpoint, *args, **kwds)]
                        add_single_api_route(self.total_route_record_list[0], self)
                    elif k == 'api_route':
                        methods: list[RequestMethodStrEnum | RequestMethodEnum] = (
                            kwds.pop('methods') if 'methods' in kwds and len(kwds['methods']) > 0 else ['get']
                        )
                        method = methods[0]
                        case_enum = isinstance(method, RequestMethodEnum) and method == RequestMethodEnum.WEBSOCKET
                        case_str_enum = method == 'websocket' or method == 'WEBSOCKET'
                        if len(methods) == 1 and (case_enum or case_str_enum):
                            self.total_route_record_list = [WebSocketRouteItem(new_endpoint, *args, **kwds)]
                            add_single_api_route(self.total_route_record_list[0], self)
                        else:
                            # 默认传多个没有websocket
                            self.total_route_record_list = [
                                BaseHttpRouteItem(new_endpoint, methods=[method], *args, **kwds) for method in methods
                            ]
                            add_single_api_route(BaseHttpRouteItem(new_endpoint, methods=methods, *args, **kwds), self)
                    else:
                        # 单个方法
                        self.total_route_record_list = [BaseHttpRouteItem(new_endpoint, methods=[k], *args, **kwds)]
                        add_single_api_route(self.total_route_record_list[0], self)
                    # 这里用endpoint随便传了，FBV用不到self
                    mount_router_and_add_controller(symbol, self)
                    setattr(new_endpoint, 'router', self)
                    return new_endpoint

                return wrapper

            return decorator
        return attr
