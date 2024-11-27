import inspect
import time
from inspect import Parameter, signature
from typing import Annotated, TypeVar, get_args, get_origin

from fastapi_boot.exception import DependencyNotFoundException, InjectFailException
from fastapi_boot.store import dep_store
from fastapi_boot.model import AppRecord

T = TypeVar('T')


def inject(app_record:AppRecord, tp: type[T], name: str | None = None) -> T:
    """inject dependency by type or name

    Args:
        app_record (AppRecord)
        tp (type[T])
        name (str | None)

    Returns:
        T: instance
    """
    start = time.time()
    while True:
        if res := dep_store.inject_by_type(tp) if name is None else dep_store.inject_by_name(name, tp):
            return res
        time.sleep(app_record.inject_retry_step)
        if time.time() - start > app_record.inject_timeout:
            raise DependencyNotFoundException(f'Dependency "{tp}" not found')


def inject_params_deps(app_record: AppRecord, params: list[Parameter]):
    """find dependencies of params
    Args:
        app_record (AppRecord)
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
                    f'The annotation of param {param.name} is missing, add an annotation or give it a default value'
                )
            # 2.2. with annotation
            if get_origin(param.annotation) == Annotated:
                # 2.2.1 Annotated
                tp, name, *_ = get_args(param.annotation)
                if not isinstance(name, str):
                    # 2.2.1.1 name is not str
                    params_dict.update({param.name: inject(app_record, tp)})
                else:
                    # 2.2.1.2 name is str, as dependency's name to inject
                    params_dict.update({param.name: inject(app_record, tp, name)})
            else:
                # 2.2.2 other
                params_dict.update({param.name: inject(app_record, param.annotation)})
    return params_dict


def inject_init_deps_and_get_instance(app_record: AppRecord, cls: type[T]) -> T:
    """inject cls's __init__ params and get params deps"""
    old_params = list(signature(cls.__init__).parameters.values())[1:]  # self
    new_params = [
        i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]  # *args、**kwargs
    return cls(**inject_params_deps(app_record, new_params))
