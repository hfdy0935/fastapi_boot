import inspect
from inspect import Parameter
from typing import Any, Callable, Type, TypeVar, get_type_hints
from typing import List
from fastapi import Depends

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.request import RequestMethodEnum

T = TypeVar("T")


def trans_path(path: str) -> str:
    """- handle path
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res: str = path if path.startswith("/") else "/" + path
    res = res if not res.endswith("/") else res[:-1]
    return res


def trans_methods(methods: List[RequestMethodEnum | str]) -> List[str]:
    """- handle RequestMethod, to string whose characters are uppercase.
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


def trans_endpoint(fn: Callable[..., T], dep: Callable):
    """
    - trans endpoint

    Args:
        fn (Callable[..., T]): endpoint
        dep (Callable): Depends value which will be used to replace 'self' if exists.
    """
    old_params = list(inspect.signature(fn).parameters.values())
    # If the first param isn't 'self', return the original fn
    if (not (osn := [i.name for i in old_params])) or (osn and osn[0] != "self"):
        return fn
    old_sign = inspect.signature(fn)
    old_first_param = old_params[0]
    new_first_param = old_first_param.replace(default=Depends(dep))
    new_params = [new_first_param] + [
        p.replace(kind=inspect.Parameter.KEYWORD_ONLY) for p in old_params[1:]
    ]
    new_sign = old_sign.replace(parameters=new_params)
    setattr(fn, "__signature__", new_sign)


def trans_cls_deps(cls: Type[Any]):
    """trans signature and __init__ method of class, so that we can inject the depends."""
    # 1
    old_init = cls.__init__
    old_sign = inspect.signature(cls)
    old_params = list(old_sign.parameters.values())[1:]
    new_params = [
        i
        for i in old_params
        if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]

    dep_names = []
    for name, value in cls.__dict__.items():
        hint = get_type_hints(cls).get(name)
        if getattr(value, CommonVar.DEP_PLACEHOLDER, None) == CommonVar.DepsPlaceholder:
            dep_names.append(name)
            new_params.append(
                Parameter(name, Parameter.KEYWORD_ONLY, annotation=hint, default=value)
            )
    new_sign = old_sign.replace(parameters=new_params)

    # 2
    def new_init(self, *args, **kwargs):
        for name in dep_names:
            value = kwargs.pop(name)
            setattr(self, name, value)
        old_init(*[self, *args], **kwargs)

    setattr(cls, "__signature__", new_sign)
    setattr(cls, "__init__", new_init)
