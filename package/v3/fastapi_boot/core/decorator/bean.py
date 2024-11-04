from collections.abc import Callable
import inspect
from typing import (
    TypeVar,
    no_type_check,
    overload,
)
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.enums import DepPos
from fastapi_boot.model.scan import DepRecord, MountedTask, Symbol
from fastapi_boot.utils.deps import get_dep_pos, try_resolve_other_init_params

T = TypeVar("T")


# ------------------------------------------------------- Bean ------------------------------------------------------- #
def resolve_bean_task(func: Callable, name: str | None = None):
    """执行Bean装饰的函数，收集依赖

    Args:
        func (Callable): Bean装饰的函数
        name (str | None, optional): 依赖名，如果有就加上. Defaults to None.
    """
    symbol = Symbol.from_obj(func)
    return_annotations = inspect.signature(func).return_annotation
    dep_pos = get_dep_pos(symbol.stack_path)
    params_dict = {k: v for k, v in inspect.signature(func).parameters.items()}

    def task():
        func_params_res = try_resolve_other_init_params(func, params_dict, symbol.stack_path)
        if func_params_res.ok:
            # 可以调用
            instance = func(**func_params_res.params)
            # 有结果，添加到依赖列表
            item = DepRecord(
                symbol=symbol,
                name=name,
                # 如果没类型注解，直接用type判断返回值类型作为类型
                constructor=(return_annotations if return_annotations != inspect._empty else type(instance)),
                value=instance,
            )
            if dep_pos == DepPos.NO_APP:
                GlobalVar.add_dep(item.to_no_app_dep_record())
            else:
                GlobalVar.get_app(symbol.stack_path).sa.add_dep(item)
        return func_params_res.ok

    if not task():
        task_ = MountedTask(symbol=symbol, task=task)
        if dep_pos == DepPos.NO_APP:
            GlobalVar.add_no_app_task(task_)
        else:
            GlobalVar.get_app(symbol.stack_path).add_task(task_)


@overload
def Bean(value: str): ...
@overload
def Bean(value: Callable[..., T]): ...
@no_type_check
def Bean(value: str | Callable[..., T]) -> Callable[..., T]:
    """装饰一个函数，将其返回值作为依赖进行收集"""

    if callable(value):
        resolve_bean_task(func=value)
        return value
    else:

        def wrapper(func: Callable[..., T]) -> Callable[..., T]:
            resolve_bean_task(func=func, name=value)
            return func

        return wrapper
