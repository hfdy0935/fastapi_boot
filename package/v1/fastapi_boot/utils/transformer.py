import inspect
from inspect import Parameter
import os
from typing import Any, Callable, Type, TypeVar, get_type_hints
from typing import List
from fastapi import Depends


from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.model.routes.route_record import RouteRecordItem, SimpleRouteRecordItem


T = TypeVar('T')


def trans_sys_abs_path_upper_first(path: str) -> str:
    """Upper the first character of an absolute path.
    """
    assert os.path.isabs(path), 'The argument path must be absolute path.'
    return path[0].upper()+path[1:]


def trans_path(path: str) -> str:
    """- halde path
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res: str = path if path.startswith('/') else '/'+path
    res = res if not res.endswith('/') else res[:-1]
    return res


def trans_methods(methods: List[RequestMethodEnum | str]) -> List[str]:
    """ - hanlde RequestMethod, to string whose characters are uppercase.
    - Example：
    > [RequestMethodEnum.PUT, 'get'] => ['PUT', 'GET']

    Args:
        methods (List[RequestMethodEnum  |  str])

    Returns:
        List[str]
    """
    res: List[str] = []
    for method in methods:
        if type(method) == str:
            res.append(method.upper())
        elif isinstance(method, RequestMethodEnum):
            res.append(method.value)
    return res


def trans_route_record_item(item: RouteRecordItem) -> SimpleRouteRecordItem:
    """trans RouteRecordItem to SimpleRouteRecordItem.
    """
    return SimpleRouteRecordItem(symbol=item.symbol, methods=item.methods,
                                 path=item.path, endpoint_name=item.endpoint_name, route_status=item.route_status)


def trans_endpoint(fn: Callable[..., T], dep: Callable):
    """
    - trans endpoint

    Args:
        fn (Callable[..., T]): endpoint
        dep (Callable): Depends value which will be userd to replace 'self' if exists.
    """
    old_params = list(inspect.signature(fn).parameters.values())
    # If the first param isn't 'self', return the original fn
    if (not (osn := [i.name for i in old_params])) or (osn and osn[0] != 'self'):
        return fn
    print(old_params)
    old_sign = inspect.signature(fn)
    old_first_param = old_params[0]
    new_first_param = old_first_param.replace(
        default=Depends(dep))
    new_params = [new_first_param] + \
        [p.replace(kind=inspect.Parameter.KEYWORD_ONLY)
         for p in old_params[1:]]
    new_sign = old_sign.replace(parameters=new_params)
    setattr(fn, '__signature__', new_sign)


def trans_cls_deps(cls: Type[Any]):
    """trans signature and __init__ method of class, so that we can inject the depends.
    """
    # 1
    old_init = cls.__init__
    old_sign = inspect.signature(cls)
    old_params = list(old_sign.parameters.values())[1:]
    new_params = [i for i in old_params if i.kind not in (
        Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)]

    dep_names = []
    for name, value in cls.__dict__.items():
        hint = get_type_hints(cls).get(name)
        if getattr(value, CommonVar.DEP_PLACEHOLDER, None) == CommonVar.DepsPlaceholder:
            dep_names.append(name)
            new_params.append(
                Parameter(name, Parameter.KEYWORD_ONLY, annotation=hint, default=value))
    new_sign = old_sign.replace(parameters=new_params)

    # 2
    def new_init(self, *args, **kwargs):
        for name in dep_names:
            value = kwargs.pop(name)
            setattr(self, name, value)
        old_init(*[self, *args], **kwargs)

    setattr(cls, '__signature__', new_sign)
    setattr(cls, '__init__', new_init)
