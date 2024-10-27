from collections import OrderedDict
from collections.abc import Callable
import inspect
from typing import (
    Any,
    TypeVar,
    no_type_check,
    overload,
)
from inspect import Parameter, isclass, isfunction
import typing

from fastapi_boot.core.helper.inject import find_dependency
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.exception.bean import InjectFailException
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.model.scan_model import InjectItem
from fastapi_boot.utils.get import get_stack_path
from fastapi_boot.utils.validator import (
    validate_bean,
    validate_inject,
)
from fastapi_boot.utils.add_task import handle_task

T = TypeVar("T")


# -------------------------------------------------------- 初始化 ------------------------------------------------------- #
# 处理有类型注解的情况
def handle_has_annotations_condition(k: str, v: Parameter, params: OrderedDict, stack_path: str):
    # 如果是Annotated且第二个参数是name，则按依赖名注入
    if typing.get_origin(anno := v.annotation) == typing.Annotated:
        args = typing.get_args(anno)
        DepType, name, *_ = args
        # 第二个参数是字符串，默认作为依赖名
        if isinstance(name, str):
            instance = find_dependency(DepType, stack_path, name)
        else:
            # 其他类型，按第一个类型注入依赖
            instance = find_dependency(DepType, stack_path)
    else:
        instance = find_dependency(v.annotation, stack_path)
    params.update({k: instance})


def do_bean_init(func: Callable[..., T]) -> T:
    """执行Bean装饰的函数"""
    params = OrderedDict()
    for k, v in inspect.signature(func).parameters.items():
        # 如果有默认值
        if (default_value := v.default) != inspect._empty:
            params.update({k: default_value})
        elif (Type := v.annotation) == inspect._empty:
            # 如果没类型，直接报错
            raise Exception(f"找不到参数类型也没有默认值，{k}")
        # 有类型，尝试注入
        else:
            handle_has_annotations_condition(k, v, params, get_stack_path(2))
    return func(*params.values())


def do_injectable_init(cls: type[T]) -> T:
    """初始化Injectable装饰的类"""
    # 如果没定义__init__，直接实例化返回
    if not cls.__dict__.get("__init__"):
        return cls()
    params = OrderedDict()
    for k, v in inspect.signature(cls.__init__).parameters.items():
        # 排除self
        if k == "self":
            continue
        # 如果有默认值
        if (default_value := v.default) != inspect._empty:
            params.update({k: default_value})
        elif (Type := v.annotation) == inspect._empty:
            # 如果没类型，直接报错
            raise InjectFailException(
                f"{InjectFailException.msg}，参数 {k} 没有写类型也没有默认值，位置：{Symbol.from_obj(cls).pos}"
            )
        # 有类型，尝试注入
        else:
            handle_has_annotations_condition(k, v, params, get_stack_path(4))
    return cls(*params.values())


# ------------------------------------------------------- Bean ------------------------------------------------------- #


@overload
def Bean(value: str) -> Callable[..., Any]: ...
@overload
def Bean(value: Callable[..., T]) -> T: ...
def Bean(value: str | Callable[..., T]) -> T | Callable[..., T]:
    """用于注入函数返回类的实例"""
    path = get_stack_path(1)
    if isfunction(value):
        validate_bean(value)
        # 执行@Bean装饰的函数得到的实例
        instance = do_bean_init(func=value)

        def task():
            # 之前已经判断了，这里肯定有
            if app := CommonVar.get_app(path):
                method = app.sv.add_inject
                item = InjectItem(
                    symbol=Symbol.from_obj(value),
                    name=None,
                    constructor=type(instance),
                    value=instance,
                )
                method(item)

        handle_task(path, task)
        return instance

    assert isinstance(value, str)

    def wrapper(obj: Callable[..., T]):
        validate_bean(obj)
        instance = do_bean_init(obj)

        def task():
            if app := CommonVar.get_app(path):
                method: Callable = app.sv.add_inject
                item = InjectItem(
                    symbol=Symbol.from_obj(obj),
                    name=value,
                    constructor=type(instance),
                    value=instance,
                )
                method(item)

        handle_task(path, task)
        return instance

    return wrapper


# ---------------------------------------------------- Injectable ---------------------------------------------------- #


@overload
def Injectable(value: str): ...
@overload
def Injectable(value: type): ...
@no_type_check
def Injectable(value) -> type[T]:
    """可注入的装饰器"""
    path = get_stack_path(1)
    # 如果直接装饰类
    if isclass(value):
        validate_inject(value)

        def task():
            if app := CommonVar.get_app(path):
                method = app.sv.add_inject
                item = InjectItem(
                    symbol=Symbol.from_obj(value),
                    name=None,
                    constructor=value,
                    value=do_injectable_init(value),
                )
                method(item)

        handle_task(path, task)
        return value
    else:
        # 如果传了name
        def wrapper(cls: type):
            validate_inject(cls)

            def task():
                if app := CommonVar.get_app(path):
                    method = app.sv.add_inject
                    item = InjectItem(
                        symbol=Symbol.from_obj(cls),
                        name=value,
                        constructor=cls,
                        value=do_injectable_init(cls),
                    )
                    method(item)

            handle_task(path, task)
            return cls

    return wrapper
