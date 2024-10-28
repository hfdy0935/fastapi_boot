from typing import Any, List, Type

from fastapi_boot.core.mapping.match_route import match_route
from fastapi_boot.model.route_model import RouteRecordItem, Symbol
from fastapi_boot.utils.transformer import trans_path
from fastapi_boot.utils.validator import validate_prefix


def Prefix(prefix: str = "",tags:List[str]=[]):
    def wrapper(obj: Type[Any]):
        validate_prefix(obj)
        match_route(
            1,
            RouteRecordItem(
                symbol=Symbol.from_obj(obj),
                path=trans_path(prefix),
                methods=[],
                endpoint_name=obj.__name__,
            ),
        )
        return obj

    return wrapper
