from collections.abc import Callable

from fastapi_boot.constants import ROUTE_RECORD
from fastapi_boot.model.route import EndpointRouteRecord, PrefixReoutRecord
from fastapi_boot.utils import trans_path


def get_wrapper(prefix: str = ""):
    def wrapper(cls: type):
        # 本层prefix的路由记录
        prefix_route_record = PrefixReoutRecord(api_routes=[], cls=cls, prefix=prefix)
        for v in cls.__dict__.values():
            if (
                hasattr(v, ROUTE_RECORD)
                and (attr := getattr(v, ROUTE_RECORD))
                and (isinstance(attr, (EndpointRouteRecord, PrefixReoutRecord)))
            ):
                prefix_route_record.api_routes.append(attr)
        # 把本层的方法或子类的路由记录添加到本层的记录上
        setattr(cls, ROUTE_RECORD, prefix_route_record)
        return cls

    return wrapper


def Prefix(prefix: Callable | str = ""):
    if isinstance(prefix, Callable):
        return get_wrapper()
    # 需要把前缀加到prefix内的所有路由前面
    return get_wrapper(trans_path(prefix))
