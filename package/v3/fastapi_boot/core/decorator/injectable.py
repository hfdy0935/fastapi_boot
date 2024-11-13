import inspect
from functools import wraps
from inspect import isclass
from typing import TypeVar, no_type_check, overload

from fastapi_boot.constants import DECORATED_FUNCTION_WRAPS_CLS
from fastapi_boot.enums import DepPos
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.model.scan import DepRecord, MountedTask, Symbol
from fastapi_boot.utils.deps import get_dep_pos, try_resolve_other_init_params

T = TypeVar('T')


def resolve_inject_task(cls: type, name: str | None = None):
    """初始化Injectable等装饰的类，收集依赖

    Args:
        cls (type): 装饰的类
        name (str | None, optional): 依赖名，如果有就加上. Defaults to None.

    Returns:
        _type_: _description_
    """
    symbol = Symbol.from_obj(cls)
    # 依赖位置，在子应用中或者非子应用的其他地方
    dep_pos = get_dep_pos(symbol.stack_path)
    # 类的__init__的参数，这里去掉self
    init_params = inspect.signature(cls.__init__).parameters
    init_params_dict = {k: v for k, v in init_params.items() if k != 'self'}

    # 保持原类的属性等
    @wraps(cls)
    def decorator(*args, **kwds):
        # 把原类名属性设置为对应方法的全局变量，否则在方法中使用原类名变量会报错找不到
        for v in cls.__dict__.values():
            if hasattr(v, '__globals__'):
                v.__globals__[cls.__name__] = cls
        return cls(*args, **kwds)

    # 把真正的类型作为属性加到函数上，便于按类型注入，不然获取到的是个函数，没法注入
    setattr(decorator, DECORATED_FUNCTION_WRAPS_CLS, cls)

    def task():
        func_params_res = try_resolve_other_init_params(decorator, init_params_dict, symbol.stack_path)
        if func_params_res.ok:
            # 可以初始化
            instance = decorator(**func_params_res.params)
            item = DepRecord(
                symbol=Symbol.from_obj(cls),
                name=name,
                constructor=cls,
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
    return decorator


@overload
def Injectable(value: str): ...
@overload
def Injectable(value: type[T]): ...


@no_type_check
def Injectable(value: str | type[T]) -> type[T]:
    """装饰一个类，将其手机为依赖"""
    if isclass(value):
        decorator = resolve_inject_task(value)
        return decorator
    else:

        def wrapper(cls: type[T]):
            decorator = resolve_inject_task(cls=cls, name=value)
            return decorator

        return wrapper
