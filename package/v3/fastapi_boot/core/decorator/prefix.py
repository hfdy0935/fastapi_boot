from inspect import isclass
from typing import TypeVar, no_type_check

from fastapi_boot.constants import CONTROLLER_ROUTE_RECORD
from fastapi_boot.model.route import EndpointRouteRecord, PrefixRouteRecord
from fastapi_boot.utils.pure import trans_path

T = TypeVar('T')


def update_endpoint_prefix(prefix: str, record: EndpointRouteRecord):
    """更新endpoint路由记录的前缀"""
    record.api_route.path = prefix + record.api_route.path


def update_prefix_prefix(prefix: str, record: PrefixRouteRecord):
    """更新prefix路由记录的前缀"""
    new_prefix = record.prefix + prefix
    for r in record.api_routes:
        if isinstance(r, EndpointRouteRecord):
            update_endpoint_prefix(new_prefix, r)
        elif isinstance(r, PrefixRouteRecord):
            update_prefix_prefix(new_prefix, r)


def get_wrapper(prefix: str = ""):
    prefix = trans_path(prefix)

    def wrapper(cls: type):
        # 本层prefix的路由记录
        prefix_route_record = PrefixRouteRecord(api_routes=[], cls=cls, prefix=prefix)
        for v in cls.__dict__.values():
            if (
                hasattr(v, CONTROLLER_ROUTE_RECORD)
                and (attr := getattr(v, CONTROLLER_ROUTE_RECORD))
                and (isinstance(attr, (EndpointRouteRecord, PrefixRouteRecord)))
            ):
                # 更新路径
                if isinstance(attr, EndpointRouteRecord):
                    update_endpoint_prefix(prefix, attr)
                elif isinstance(attr, PrefixRouteRecord):
                    update_prefix_prefix(prefix, attr)
                prefix_route_record.api_routes.append(attr)
        # 把本层的方法或子类的路由记录添加到本层的记录上
        setattr(cls, CONTROLLER_ROUTE_RECORD, prefix_route_record)
        return cls

    return wrapper


@no_type_check
def Prefix(prefix: type[T] | str = "") -> T:
    """控制器中的前缀，装饰类
    - 同一个控制器中前缀相同或请求依赖相同的的可以写在一个Prefix装饰的类中；

    Args:
        prefix (type[T] | str, optional): 字符串或类，字符串默认空. Defaults to "".

    Returns:
        T: 被装饰类的实例
    """
    if isclass(prefix):
        return get_wrapper()
    # 把前缀加到Prefix的路由记录前面
    return get_wrapper(trans_path(prefix))
