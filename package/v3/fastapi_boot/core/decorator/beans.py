from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
import inspect
from typing import (
    Generic,
    TypeVar,
    ForwardRef,
    Annotated,
    no_type_check,
    overload,
)
from inspect import Parameter, isclass, isfunction
import typing

from fastapi_boot.core.helper.inject import find_dependency_once
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.scan_enum import InjectType
from fastapi_boot.exception.bean import InjectFailException
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.model.scan_model import InjectItem, MountedTask
from fastapi_boot.utils.get import get_forward_ref_args, get_stack_path
from fastapi_boot.utils.judger import is_forward_ref
from fastapi_boot.utils.validator import (
    validate_bean,
    validate_inject,
)
from fastapi_boot.utils.task import add_task

T = TypeVar("T")


# -------------------------------------------------------- 初始化 ------------------------------------------------------- #


# ---------------------------------------------------- 处理Bean执行时机 ---------------------------------------------------- #
def handle_forward_ref(DepType: ForwardRef, stack_path: str):
    """处理forward_ref类型的依赖

    Args:
        DepType (ForwardRef):类型
        stack_path (str): 调用栈位置

    Returns:
        _type_: 找到就返回，找不到没返回
    """
    dep_type_name = get_forward_ref_args(DepType)  # 类型名
    return find_dependency_once(InjectType.NAME_OF_TYPE, stack_path, dep_type_name=dep_type_name)


def handle_has_annotations_condition_once(k: str, v: Parameter, params: OrderedDict, stack_path: str) -> bool:
    """处理没默认值有类型注解的参数

    Args:
        k (str): 参数名
        v (Parameter): Parameter
        params (OrderedDict): 函数的参数，逐个积累
        stack_path (str): 用于找app的路径

    Returns:
        bool: 是否修改params，如果False表示没找到该依赖
    """
    # 如果是Annotated且第二个参数是name，则按依赖名注入，只判断一次
    if typing.get_origin(anno := v.annotation) == Annotated:
        args = typing.get_args(anno)
        DepType, name, *_ = args
        # 先判断按依赖名注入，第二个参数是字符串，空字符串的情况按照类型注入
        if isinstance(name, str) and name:
            instance = find_dependency_once(InjectType.NAME, stack_path, DepType, name=name)
        else:
            # 如果是ForWardRef类型
            if is_forward_ref(DepType):
                instance = handle_forward_ref(DepType, stack_path)
            else:
                # 按第一个类型注入依赖
                instance = find_dependency_once(InjectType.TYPE, stack_path, DepType=DepType)
    else:
        # 如果是字符串，默认为ForwardRef类型
        if isinstance(v.annotation, str):
            instance = find_dependency_once(InjectType.NAME_OF_TYPE, stack_path, dep_type_name=v.annotation)
        else:
            # 普通类型
            instance = find_dependency_once(InjectType.TYPE, stack_path, v.annotation)

    if instance:
        params.update({k: instance})
        return True
    return False


@dataclass
class RunResult(Generic[T]):
    ok: bool
    result: T | None


InitResult = RunResult


def try_run_bean(func: Callable[..., T], stack_path: str) -> RunResult[T]:
    """尝试执行"""
    params = OrderedDict()
    ok = True
    for k, v in inspect.signature(func).parameters.items():
        # 如果有默认值
        if (default_value := v.default) != inspect._empty:
            params.update({k: default_value})
        elif v.annotation == inspect._empty:
            # 如果没类型，直接报错
            raise Exception(f"找不到参数类型也没有默认值，{k}")
        # 有类型，尝试注入
        else:
            ok = handle_has_annotations_condition_once(k, v, params, stack_path)
            if not ok:
                break
    return RunResult(ok=ok, result=func(*params.values()) if ok else None)


def try_init_dependency(cls: type[T], stack_path: str) -> InitResult[T]:
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


# ------------------------------------------------------- Bean ------------------------------------------------------- #


@overload
def Bean(value: str): ...
@overload
def Bean(value: Callable[..., T]): ...
def Bean(value: str | Callable[..., T]):
    """用于注入函数返回类的实例"""
    stack_path = get_stack_path(1)
    if isfunction(value):
        validate_bean(value)
        # 如果写了返回值的类型，按照返回值类型添加适用于有泛型的情况；否则用type(instance)，没泛型
        return_annotations = inspect.signature(value).return_annotation

        def task():
            run_result = try_run_bean(value, stack_path)
            if not run_result.ok:
                # 如果没有执行，说明有依赖还没加载，把这个任务放到任务列表最后面
                CommonVar.add_task(MountedTask(path=stack_path, task=task))
            else:
                # 有结果，添加到依赖列表
                # 这时app肯定存在，因为task时在app挂载后才执行的，判断一下啊为了类型不报错
                if app := CommonVar.get_app(stack_path):
                    item = InjectItem(
                        symbol=Symbol.from_obj(value),
                        name=None,
                        constructor=(
                            return_annotations if return_annotations != inspect._empty else type(run_result.result)
                        ),
                        value=run_result.result,
                    )
                    app.sv.add_inject(item)

        add_task(stack_path, task)
        return

    assert isinstance(value, str), "依赖名必须是字符串"

    def wrapper(obj: Callable[..., T]):
        validate_bean(obj)
        return_annotations = inspect.signature(obj).return_annotation

        def task():
            run_result = try_run_bean(obj, stack_path)
            if not run_result.ok:
                # 如果没有执行，说明有依赖还没加载，把这个任务放到任务列表最后面
                CommonVar.add_task(MountedTask(path=stack_path, task=task))
                return
            else:
                # 有结果，添加到依赖列表
                # 这时app肯定存在，因为task时在app挂载后才执行的，判断一下啊为了类型不报错
                if app := CommonVar.get_app(stack_path):
                    item = InjectItem(
                        symbol=Symbol.from_obj(obj),
                        name=value,
                        constructor=(
                            return_annotations if return_annotations != inspect._empty else type(run_result.result)
                        ),
                        value=run_result.result,
                    )
                    app.sv.add_inject(item)

        add_task(stack_path, task)

    return wrapper


# ---------------------------------------------------- Injectable ---------------------------------------------------- #


@overload
def Injectable(value: str): ...
@overload
def Injectable(value: type): ...
@no_type_check
def Injectable(value) -> type[T]:
    """可注入的装饰器"""
    stack_path = get_stack_path(1)
    # 如果直接装饰类
    if isclass(value):
        validate_inject(value)

        def task():
            init_result = try_init_dependency(value, stack_path)
            if not init_result.ok:
                CommonVar.add_task(MountedTask(stack_path, task))
            elif app := CommonVar.get_app(stack_path):
                item = InjectItem(
                    symbol=Symbol.from_obj(value),
                    name=None,
                    constructor=value,
                    value=init_result.result,
                )
                app.sv.add_inject(item)

        add_task(stack_path, task)
        return value
    else:
        # 如果传了name
        def wrapper(cls: type):
            validate_inject(cls)

            def task():
                init_result = try_init_dependency(value, stack_path)
                if not init_result.ok:
                    CommonVar.add_task(MountedTask(stack_path, task))
                elif app := CommonVar.get_app(stack_path):
                    item = InjectItem(
                        symbol=Symbol.from_obj(cls),
                        name=value,
                        constructor=cls,
                        value=init_result.result,
                    )
                    app.sv.add_inject(item)

            add_task(stack_path, task)
            return cls

        return wrapper
