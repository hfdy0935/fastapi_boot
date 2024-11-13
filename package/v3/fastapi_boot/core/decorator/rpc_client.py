import inspect
from collections.abc import Callable
from inspect import Parameter, signature
from typing import Any, TypeVar

from fastapi_boot.constants import Undefined  # type: ignore
from fastapi_boot.constants import CBV_ENDPOINT, CONTROLLER_ROUTE_RECORD, RPC_REPLACE_DEFAULT_TYPE
from fastapi_boot.enums import RequestMethodEnum
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.model.route import (
    BaseHttpRouteItem,
    ControllerRecord,
    EndpointRouteRecord,
    PrefixRouteRecord,
    WebSocketRouteItem,
)
from fastapi_boot.model.scan import DepRecord, Symbol
from fastapi_boot.utils.pure import get_stack_path, trans_path

T = TypeVar('T')

# ------------------------------------------------------- utils ------------------------------------------------------ #

EMPTY = inspect._empty


def is_empty(p: Parameter):
    """参数是否没有默认值"""
    return p.default == EMPTY


def is_cbv(endpoint):
    """该函数是否是Controller装饰的类中的请求方法"""
    return hasattr(endpoint, CBV_ENDPOINT)


def get_route_record(item):
    """判断item是否有路由记录，用于遍历RpcClient装饰的类时筛选出请求方法，有就返回"""
    return getattr(item, CONTROLLER_ROUTE_RECORD) if hasattr(item, CONTROLLER_ROUTE_RECORD) else None


# ----------------------------------------------------- 处理调用方法的参数，转换和默认值 ---------------------------------------------------- #
def trans_param_default_value(p: Parameter) -> Parameter:
    """转换参数
    - if没默认值，返回None
    - elif 有非RPC_REPLACE_DEFAULT_TYPE的默认值，直接返回
    - elif 有RPC_REPLACE_DEFAULT_TYPE默认值，if 设置了默认值或默认工厂，提取返回，else 返回None
    - else 返回 None

    Args:
        p (Parameter): 要转换的Parameter

    Returns:
        Parameter: 转换后的Parameter
    """
    default = p.default
    if is_empty(p):
        return p
    elif isinstance(default, RPC_REPLACE_DEFAULT_TYPE):
        if default.default != Undefined:
            return p.replace(default=default.default)
        elif default.default_factory and default.default_factory != Undefined:
            return p.replace(default=default.default_factory())
        else:
            return p.replace(default=EMPTY)
    else:
        return p


def call_endpoint(endpoint: Callable[..., T], v: Callable, *args, **kwds) -> T:
    """替换Query、Body等默认值，调用函数；
    如果没传值的，说明有默认值，需要把默认值取出来传值，比如Query(10)，需要把10取出来传给endpoint，避免接收到Query()无法pydantic序列化而报错

    Args:
        endpoint (Callable): endpoint
        v (Callable): RpcClient装饰的类中的方法
        args和kwds是调用时传的参数，含self
    """
    # 1. 转换v的参数
    v_params: list[Parameter] = [trans_param_default_value(p) for p in signature(v).parameters.values()]
    v_params_names = [p.name for p in v_params]

    # 2. 根据调用时传的参数整理
    ## 2.1 都改成关键字参数
    for idx, a in enumerate(args):
        kwds.update({v_params_names[idx]: a})
    ## 2.2 添加v_params中有默认值但调用时没传的参数
    for p in v_params:
        if not is_empty(p) and p.name not in kwds:
            kwds.update({p.name: p.default})

    # 3. 转换endpoint的参数
    e_params = [trans_param_default_value(p) for p in signature(endpoint).parameters.values()]
    ## 3.1 添加e_params中有默认值但rpc时没传的参数，rpc参数优先级高于endpoint
    for p in e_params:
        if not is_empty(p) and p.name not in kwds:
            kwds.update({p.name: p.default})

    # 4. 如果不是CBV，需要删除kwds的self
    if not is_cbv(endpoint):
        kwds.pop('self')

    # 5.调用endpoint
    return endpoint(**kwds)


# ----------------------------------------------- 替换endpoint、递归替换prefix ---------------------------------------------- #
def replace_endpoint(attr: EndpointRouteRecord, target_app: Any, cls: type, k: str, v: Any, prefix: str, instance: Any):
    """替换endpoint为找到的路由记录的endpoint；
    调用时如果找到一个则返回结果，如果多个返回结果列表

    Args:
        attr (EndpointRouteRecord): endpoint记录
        target_app (Any): 要在哪个应用上找endpoint
        cls (type): 找到后要替换哪个类的方法
        k (str): 要替换这个类的哪个key
        v (Any): 这个key对应的v
        prefix (str): RpcClient的请求前缀
        instance (Any): 被RpcClient装饰的类的实例
    """
    path = prefix + attr.api_route.path
    methods = []
    if isinstance(attr.api_route, WebSocketRouteItem):
        methods = [RequestMethodEnum.WEBSOCKET]
    elif isinstance(attr.api_route, BaseHttpRouteItem):
        methods = attr.api_route.methods
    controller_list: list[ControllerRecord] = []
    for method in methods:
        ctrl = target_app.ra.get_controller_route_records_by_path_and_method(path, method)
        if not ctrl:
            raise Exception(f'远程调用的请求未找到，位置：{Symbol.from_obj(cls).pos}, 请求方法：{method}')
        controller_list.append(ctrl)

    def new_endoint(self, *args, **kwds):
        # 如果原来是FBV，不加实例，否则加上原来的实例
        res_list = []
        for c in controller_list:
            endpoint = c.route_record.endpoint
            # 如果是类的方法，用c.instance替代self
            if is_cbv(endpoint):
                res_list.append(call_endpoint(endpoint, v, c.instance, *args, **kwds))
            else:
                # 否则用instance替代self，不过self也似乎用不上
                res_list.append(call_endpoint(endpoint, v, instance, *args, **kwds))
        return res_list[0] if len(res_list) == 1 else res_list

    setattr(cls, k, new_endoint)


def replace_prefix(attr: PrefixRouteRecord, target_app: Any, prefix: str, instance: Any):
    """替换prefix下的所有endpoint，递归查找

    Args:
        attr (PrefixRouteRecord): prefix的路由记录
        target_app (Any): 要在哪个应用上找endpoint
        prefix (str): 前缀
        instance (Any): 被RpcClient装饰的类的实例
    """
    for k, v in attr.cls.__dict__.items():
        if subattr := get_route_record(v):
            if isinstance(subattr, EndpointRouteRecord):
                replace_endpoint(subattr, target_app, attr.cls, k, v, prefix, instance)
            elif isinstance(subattr, PrefixRouteRecord):
                replace_prefix(subattr, target_app, prefix, instance)


# ----------------------------------------------------- RpcClient ---------------------------------------------------- #
class NewCls: ...


def RpcClient(server_name: str, prefix: str = ""):
    prefix = trans_path(prefix)
    stack_path = get_stack_path(1)

    def decorator(cls: type[T]) -> type[T]:
        # 空实例
        instance = NewCls()
        instance_num = 0

        # 遍历__dict__，根据mapping方法修饰的属性找到需要注入的方法
        def task():
            target_app = GlobalVar.get_app_by_server_name(server_name)
            # 把实例添加到rpc依赖中，直接添加依赖，不管依赖是否准备好，后面target_app创建后会运行任务修改实例的方法
            # 只添加一次
            nonlocal instance_num
            if instance_num == 0:
                GlobalVar.get_app(stack_path).ra.add_dep(
                    DepRecord(symbol=Symbol.from_obj(cls), name=None, constructor=cls, value=instance)
                )
            instance_num += 1
            if target_app:
                for k, v in cls.__dict__.items():
                    if attr := get_route_record(v):
                        if isinstance(attr, EndpointRouteRecord):
                            replace_endpoint(attr, target_app, NewCls, k, v, prefix, instance)
                        elif isinstance(attr, PrefixRouteRecord):
                            replace_prefix(attr, target_app, prefix, instance)

        # 如果没找到target_app，就把任务添加到全局子应用任务列表，等该子应用创建后执行
        if not task():
            GlobalVar.add_app_server_name_task(server_name, task)
        return cls

    return decorator
