import inspect
from collections.abc import Callable
from functools import wraps
from inspect import Parameter
from typing import Any, get_type_hints

from fastapi import APIRouter, Depends

from fastapi_boot.constants import REQ_DEP_PLACEHOLDER
from fastapi_boot.model.route import BaseHttpRouteItem, WebSocketRouteItem
from fastapi_boot.model.scan import InjectParamsResult
from fastapi_boot.utils.deps import try_resolve_controller_init_params
from fastapi_boot.utils.pure import trans_path


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
    def new_init(self, *args, **kwds):
        # 删除usedep变量名，并设置到self上
        for name in dep_names:
            value = kwds.pop(name)
            setattr(self, name, value)
        # 旧的init只需要项目依赖
        old_init(self, **proj_deps_dict)

    setattr(cls, '__signature__', new_sign)
    setattr(cls, '__init__', new_init)


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
    init_params_dict = {k: v for k, v in init_params.items() if k != 'self'}
    res = try_resolve_controller_init_params(decorator, init_params_dict, stack_path)
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
