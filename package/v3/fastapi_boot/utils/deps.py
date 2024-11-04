import time
from typing import Any, TypeVar
from collections.abc import Callable
import inspect
from inspect import Parameter
from typing import (
    TypeVar,
    Annotated,
)
import typing

from fastapi_boot.constants import DECORATED_FUNCTION_WRAPS_CLS
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.enums import DepInjectPos, DepPos, InjectType
from fastapi_boot.exception import AppNotFoundException, InjectFailException
from fastapi_boot.model.scan import InjectParamsResult, Symbol

T = TypeVar("T")


def get_dep_pos(stack_path: str) -> DepPos:
    """在无app模块还是子应用中

    Args:
        stack_path (str): 调用栈文件系统路径

    Returns:
        DepPos: 依赖在应用中还是无应用
    """
    try:
        GlobalVar.get_app(stack_path)
        return DepPos.APP
    except AppNotFoundException:
        return DepPos.NO_APP


# ------------------------------------------------------- 查找依赖 ------------------------------------------------------- #
def get_real_type(DepType: type[T]) -> type[T]:
    """获取真实类型
    - 原来是Bean装饰的，直接返回
    - 原来是其他装饰的，返回DECORATED_FUNCTION_WRAPS_CLS属性

    Args:
        DepType (type[T]): 可能是类型或函数

    Returns:
        type[T]: 真实类型
    """
    return getattr(DepType, DECORATED_FUNCTION_WRAPS_CLS) if hasattr(DepType, DECORATED_FUNCTION_WRAPS_CLS) else DepType


def find_dependency_once(
    inject_type: InjectType, stack_path: str, DepType: type[T], name: str = "", dep_type_name: str = ""
) -> T | None:
    """寻找 一次 依赖，找不到返回None；此时已挂载

    Args:
        inject_type (InjectType): 依赖注入方式
        stack_path (str): 调用栈路径
        DepType (type[T]): 类型
        name (str, optional): 依赖名. Defaults to "".
        dep_type_name (str, optional): 类型名. Defaults to "".

    Returns:
        T | None: 找到了就返回结果，找不到返回None
    """
    dep_pos = get_dep_pos(stack_path)
    if dep_pos == DepPos.APP:
        app = GlobalVar.get_app(stack_path)
        if inject_type == InjectType.NAME:
            res = app.sa.inject_by_name(name, DepType)
        elif inject_type == InjectType.TYPE:
            res = app.sa.inject_by_type(DepType)
        elif inject_type == InjectType.NAME_OF_TYPE:
            res = app.sa.inject_by_type_name(dep_type_name)
        if res:
            return res
        else:
            # 没找到，执行所有任务，更新依赖列表
            GlobalVar.get_app(stack_path).run_tasks()
            return None
    else:
        # 无app模块只能注入无app模块的依赖，不能注入app中的依赖，防止循环引用
        if inject_type == InjectType.NAME:
            res = GlobalVar.inject_by_name(name, DepType)
        elif inject_type == InjectType.TYPE:
            assert DepType
            res = GlobalVar.inject_by_type(DepType)
        elif inject_type == InjectType.NAME_OF_TYPE:
            res = GlobalVar.inject_by_type_name(dep_type_name)
        if res:
            return res
        else:
            GlobalVar.run_no_app_tasks()
            return None


def find_dependency(
    inject_type: InjectType, stack_path: str, DepType: type[T], name: str = "", dep_type_name: str = ""
) -> T:
    """查找依赖

    Args:
        inject_type (InjectType): 注入类型，依赖类型/依赖名/依赖类型名
        stack_path (str): 调用栈文件系统路径
        DepType (type[T]): 依赖类型
        name (str, optional): 依赖名. Defaults to "".
        dep_type_name (str, optional): 依赖类型名. Defaults to "".

    Raises:
        InjectFailException: 注入失败

    Returns:
        T:查找结果
    """
    res: T | None = None
    dep_pos = get_dep_pos(stack_path)
    timeout_second = (
        GlobalVar.get_app(stack_path).sa.scan_timeout_second
        if dep_pos == DepPos.APP
        else GlobalVar.no_app_scan_timeout_second
    )
    # 报错信息
    if inject_type == InjectType.NAME:
        msg = f"名为 {name} "
    elif inject_type == InjectType.TYPE:
        msg = f"类型为 {DepType.__name__ if DepType else ...}"
    elif inject_type == InjectType.NAME_OF_TYPE:
        msg = f"类型为 {dep_type_name}"
    # 开始寻找依赖
    start = time.time()
    while True:
        print("\r", end="")
        res = find_dependency_once(inject_type, stack_path, DepType, name, dep_type_name)
        if res:
            return res
        time.sleep(0.1)
        if timeout_second > 0 and time.time() - start > timeout_second:
            raise InjectFailException(f"扫描超时，{msg} 的依赖未找到，位置： {stack_path}")


# ---------------------------------------------------- 处理Annotated中的Forward字符串表示的类型 ---------------------------------------------------- #


def handle_has_annotations_condition(
    k: str, v: Parameter, params: dict[str, Any], stack_path: str, dep_inject_pos: DepInjectPos
) -> bool:
    """处理没默认值有类型注解的参数

    Args:
        k (str): 参数名
        v (Parameter): Parameter
        params (dict): 函数的参数，逐个积累
        stack_path (str): 调用者栈文件系统路径
        dep_inject_pos (DepInjectPos): 该依赖所在位置，控制器或其他

    Returns:
        bool:是否找到该类型的依赖，True找到了且修改了params，False没找到
    """
    # 如果是Annotated且第二个参数是name，则按依赖名注入，只判断一次
    instance = None
    # 根据注入位置决定注入方法
    inject_method = find_dependency if dep_inject_pos == DepInjectPos.CONTROLLER else find_dependency_once
    if typing.get_origin(anno := v.annotation) == Annotated:
        args = typing.get_args(anno)
        DepType, name, *_ = args
        RealType = get_real_type(DepType)
        # 先判断按依赖名注入，第二个参数是字符串，空字符串的情况按照类型注入
        if isinstance(name, str) and name:
            instance = inject_method(InjectType.NAME, stack_path, RealType, name=name)
        else:
            # 如果是ForWardRef类型
            # name没变，非Bean的情况下也能继续用
            if isinstance(DepType, typing.ForwardRef):
                dep_type_name = DepType.__forward_arg__  # 类型名
                # 随便传个类型，用不到
                instance = inject_method(
                    InjectType.NAME_OF_TYPE, stack_path, DepType=object, dep_type_name=dep_type_name
                )
            else:
                # 按第一个类型注入依赖
                instance = inject_method(InjectType.TYPE, stack_path, DepType=RealType)
    else:
        # 如果是字符串，默认为ForwardRef类型
        if isinstance(v.annotation, str):
            instance = inject_method(InjectType.NAME_OF_TYPE, stack_path, DepType=object, dep_type_name=v.annotation)
        else:
            # 普通类型
            instance = inject_method(InjectType.TYPE, stack_path, get_real_type(v.annotation))
    if instance:
        params.update({k: instance})
        return True
    return False


# ---------------------------------------------------- 尝试运行或初始化依赖 ---------------------------------------------------- #


def try_resolve_init_params(
    func: Callable[..., T], parameters: dict[str, Parameter], stack_path: str, dep_inject_pos: DepInjectPos
) -> InjectParamsResult:
    """尝试注入Bean装饰的函数或Injectable等装饰的类 的 所有依赖

    Args:
        func (Callable[...,T]): （1）函数；（2）被包装的函数，返回类的实例
        parameters (dict[str,Parameter]): 第二种情况的func的参数是*args、**kwds，所以要把原来类的__init__方法的参数去掉self传进来
        stack_path (str): 调用栈所在文件系统路径
        dep_inject_pos (DepInjectPos): 依赖注入的位置，控制器还是其他位置

    Returns:
        InjectParamsResult: 是否成功及注入的参数字典
    """
    # 用于初始化的参数
    params = {}
    ok = True
    for k, v in parameters.items():
        # 如果有默认值
        if v.default != inspect._empty:
            parameters.update({k: v.default})
        elif v.kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]:
            # 如果时*args和**kwds之类的参数，跳过，因为IOC初始化不由用户控制，用户只能指定要注入的依赖，不额外传参
            pass
        elif v.annotation == inspect._empty:
            # 如果没类型，直接报错
            raise Exception(f"找不到参数类型也没有默认值，{k}，位置：{Symbol.from_obj(func).pos}")
        # 有类型，尝试注入
        else:
            ok = handle_has_annotations_condition(k, v, params, stack_path, dep_inject_pos)
            if not ok:
                break
    # 不成功就返回空有序字典
    return InjectParamsResult(ok=ok, params=params if ok else {})


def try_resolve_controller_init_params(func: Callable[..., T], parameters: dict[str, Parameter], stack_path: str):
    """注入控制器装饰的类的__init__的参数"""
    return try_resolve_init_params(func, parameters, stack_path, DepInjectPos.CONTROLLER)


def try_resolve_other_init_params(func: Callable[..., T], parameters: dict[str, Parameter], stack_path: str):
    """在除了控制器的其他位置注入依赖"""
    return try_resolve_init_params(func, parameters, stack_path, DepInjectPos.OTHER)
