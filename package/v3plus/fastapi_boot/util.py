import inspect
import inspect
from inspect import Parameter, signature
from typing import Annotated, TypeVar, get_args, get_origin
from fastapi_boot.exception import InjectFailException
from fastapi_boot.vars import dep_store

T = TypeVar('T')


def trans_path(path: str) -> str:
    """
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res = '/' + path.lstrip('/')
    res = res.rstrip('/')
    return '' if res == '/' else res


def inject_func_params(params: list[Parameter]):
    """find dependencies of params
    Args:
        params (list[Parameter]): param list without self
    """
    params_dict = {}
    for param in params:
        # 1. with default
        if param.default != inspect._empty:
            params_dict.update({param.name: param.default})
        else:
            # 2. no default
            if param.annotation == inspect._empty:
                # 2.1 not annotation
                raise InjectFailException(
                    f'The annotation of param {param.name} is missing, add an annotation or give it a default value')
            # 2.2. with annotation
            if get_origin(param.annotation) == Annotated:
                # 2.2.1 Annotated
                tp, name, *_ = get_args(param.annotation)
                if not isinstance(name, str):
                    # 2.2.1.1 name is not str
                    params_dict.update(
                        {param.name: dep_store.inject_by_type(tp)})
                else:
                    # 2.2.1.2 name is str, as dependency's name to inject
                    params_dict.update(
                        {param.name: dep_store.inject_by_name(name, tp)})
            else:
                # 2.2.2 other
                params_dict.update(
                    {param.name: dep_store.inject_by_type(param.annotation)})
    return params_dict


def inject_dependency_init_deps(cls: type[T]):
    """inject cls's __init__ params and get instance"""
    old_params = list(signature(cls.__init__).parameters.values())[
        1:]  # self
    new_params = [i for i in old_params if i.kind not in (
        Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)]  # *args、**kwargs
    return cls(**inject_func_params(new_params))
