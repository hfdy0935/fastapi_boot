from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
import inspect
from typing import (
    Generic,
    TypeVar,
    Annotated,
    no_type_check,
    overload,
)
from inspect import Parameter, isclass
import typing
from fastapi_boot.core.inject import find_dependency_once
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.enums import DepPos, InjectType
from fastapi_boot.exception import AppNotFoundException, InjectFailException
from fastapi_boot.model.scan import DepRecord, MountedTask, Symbol

T = TypeVar("T")


def get_dep_pos(stack_path: str):
    """在无app模块还是app中"""
    try:
        GlobalVar.get_app(stack_path)
        return DepPos.APP
    except AppNotFoundException:
        return DepPos.NO_APP


# ---------------------------------------------------- 处理Annotated中的Forward字符串表示的类型 ---------------------------------------------------- #


def handle_has_annotations_condition_once(k: str, v: Parameter, params: OrderedDict, stack_path: str) -> bool:
    """处理没默认值有类型注解的参数

    Args:
        k (str): 参数名
        v (Parameter): Parameter
        params (OrderedDict): 函数的参数，逐个积累
        stack_path (str): 调用者在项目中的标识

    Returns:
        bool:是否找到该类型的依赖，True找到了且修改了params，False没找到
    """
    # 如果是Annotated且第二个参数是name，则按依赖名注入，只判断一次
    instance = None
    if typing.get_origin(anno := v.annotation) == Annotated:
        args = typing.get_args(anno)
        DepType, name, *_ = args
        # 先判断按依赖名注入，第二个参数是字符串，空字符串的情况按照类型注入
        if isinstance(name, str) and name:
            instance = find_dependency_once(InjectType.NAME, stack_path, DepType, name=name)
        else:
            # 如果是ForWardRef类型
            if isinstance(DepType, typing.ForwardRef):
                dep_type_name = DepType.__forward_arg__  # 类型名
                instance = find_dependency_once(
                    InjectType.NAME_OF_TYPE, stack_path, DepType=object, dep_type_name=dep_type_name
                )
            else:
                # 按第一个类型注入依赖
                instance = find_dependency_once(InjectType.TYPE, stack_path, DepType=DepType)
    else:
        # 如果是字符串，默认为ForwardRef类型
        if isinstance(v.annotation, str):
            instance = find_dependency_once(
                InjectType.NAME_OF_TYPE, stack_path, DepType=object, dep_type_name=v.annotation
            )
        else:
            # 普通类型
            instance = find_dependency_once(InjectType.TYPE, stack_path, v.annotation)
    if instance:
        params.update({k: instance})
        return True
    return False


# ---------------------------------------------------- 尝试运行或初始化依赖 ---------------------------------------------------- #
@dataclass
class RunResult(Generic[T]):
    ok: bool
    result: T | None


InitResult = RunResult


def try_run_bean(func: Callable[..., T], stack_path: str) -> RunResult[T]:
    """尝试执行Bean装饰的方法"""
    params = OrderedDict()
    ok = True
    for k, v in inspect.signature(func).parameters.items():
        # 如果有默认值
        if (default_value := v.default) != inspect._empty:
            params.update({k: default_value})
        elif v.annotation == inspect._empty:
            # 如果没类型，直接报错
            raise Exception(f"找不到参数类型也没有默认值，{k}，位置：{Symbol.from_obj(func).pos}")
        # 有类型，尝试注入
        else:
            ok = handle_has_annotations_condition_once(k, v, params, stack_path)
            if not ok:
                break
    return RunResult(ok=ok, result=func(*params.values()) if ok else None)


def try_init_dependency(cls: type[T], stack_path: str = "") -> InitResult[T]:
    """尝试实例化"""
    ok = True
    # 如果没定义__init__，直接实例化返回
    if not cls.__dict__.get("__init__"):
        return InitResult(ok=True, result=cls())
    params = OrderedDict()
    for k, v in inspect.signature(cls.__init__).parameters.items():
        # 排除self
        if k == "self":
            continue
        # 如果有默认值
        elif (default_value := v.default) != inspect._empty:
            params.update({k: default_value})
        elif v.annotation == inspect._empty:
            # 如果没类型，直接报错
            raise InjectFailException(
                f"{InjectFailException.msg}，参数 {k} 没有写类型也没有默认值，位置：{Symbol.from_obj(cls).pos}"
            )
        # 有类型，尝试注入
        else:
            ok = handle_has_annotations_condition_once(k, v, params, stack_path)
            # 只要有一个是False就证明依赖还没准备好
            if not ok:
                break
    return InitResult(ok=ok, result=cls(*params.values()) if ok else None)


# ----------------------------------------------------- 处理注入依赖的任务 ---------------------------------------------------- #
def resolve_bean_task(func: Callable, name: str | None = None):
    """执行Bean装饰的函数"""
    symbol = Symbol.from_obj(func)
    return_annotations = inspect.signature(func).return_annotation
    dep_pos = get_dep_pos(symbol.stack_path)

    def task():
        run_result = try_run_bean(func, symbol.stack_path)
        if run_result.ok:
            # 有结果，添加到依赖列表a
            item = DepRecord(
                symbol=symbol,
                name=name,
                # 如果没类型注解，直接用type判断返回值类型作为类型
                constructor=(return_annotations if return_annotations != inspect._empty else type(run_result.result)),
                value=run_result.result,
            )
            if dep_pos == DepPos.NO_APP:
                GlobalVar.add_dep(item.to_no_app_dep_record())
            else:
                GlobalVar.get_app(symbol.stack_path).add_dep(item)
        return run_result.ok

    if not task():
        task_ = MountedTask(symbol=symbol, task=task)
        if dep_pos == DepPos.NO_APP:
            GlobalVar.add_no_app_task(task_)
        else:
            GlobalVar.get_app(symbol.stack_path).add_task(task_)


def resolve_inject_task(cls: type, name: str | None = None):
    """初始化依赖"""
    symbol = Symbol.from_obj(cls)
    dep_pos = get_dep_pos(symbol.stack_path)

    def task():
        run_result = try_init_dependency(cls, symbol.stack_path)
        if run_result.ok:
            item = DepRecord(
                symbol=Symbol.from_obj(cls),
                name=name,
                constructor=cls,
                value=run_result.result,
            )
            if dep_pos == DepPos.NO_APP:
                GlobalVar.add_dep(item.to_no_app_dep_record())
            else:
                GlobalVar.get_app(symbol.stack_path).add_dep(item)
        return run_result.ok

    if not task():
        task_ = MountedTask(symbol=symbol, task=task)
        if dep_pos == DepPos.NO_APP:
            GlobalVar.add_no_app_task(task_)
        else:
            GlobalVar.get_app(symbol.stack_path).add_task(task_)


# ------------------------------------------------------- Bean ------------------------------------------------------- #


@overload
def Bean(value: str): ...
@overload
def Bean(value: Callable[..., T]): ...
def Bean(value: str | Callable[..., T]):
    """用于注入函数返回类的实例"""

    if callable(value):
        resolve_bean_task(func=value)
    else:

        def wrapper(func: Callable[..., T]):
            resolve_bean_task(func=func, name=value)
            return func

        return wrapper


# ---------------------------------------------------- Injectable ---------------------------------------------------- #


@overload
def Injectable(value: str): ...
@overload
def Injectable(value: type[T]): ...
@no_type_check
def Injectable(value: str | type[T]) -> type[T]:
    """可注入的装饰器"""
    if isclass(value):
        resolve_inject_task(cls=value)
        return value
    else:

        def wrapper(cls: type[T]):
            resolve_inject_task(cls=cls, name=value)
            return cls

        return wrapper
