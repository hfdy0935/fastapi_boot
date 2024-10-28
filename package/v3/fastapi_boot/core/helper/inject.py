import time
from typing import  TypeVar

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.enums.scan_enum import InjectType
from fastapi_boot.exception.bean import InjectFailException
from fastapi_boot.utils.get import get_stack_path
from typing import TypeVar

T = TypeVar("T")


def find_dependency_once(
    inject_type: InjectType, stack_path: str, DepType: type[T] | None = None, name: str = "", dep_type_name: str = ""
):
    """寻找 一次 依赖，找不到返回None；此时已挂载

    Args:
        inject_type (InjectType): 依赖注入方式
        stack_path (str): 调用栈路径
        DepType (type[T], optional): 类型
        name (str, optional): 依赖名. Defaults to "".
        dep_type_name (str, optional): 类型名. Defaults to "".

    Returns:
        _type_: 找到了就返回结果，找不到返回None
    """
    application = CommonVar.get_app(stack_path)
    assert application
    if inject_type == InjectType.NAME and (res := application.sa.inject_by_name(name)):
        return res
    elif inject_type == InjectType.TYPE and (res := application.sa.inject_by_type(DepType)):
        return res
    elif inject_type == InjectType.NAME_OF_TYPE and (res := application.sa.inject_by_type_name(dep_type_name)):
        return res
    # 如果扫描不到，就更新一次
    CommonVar.run_task(application.dir_sys_path)
    return None


def find_dependency(
    inject_type: InjectType, stack_path: str, DepType: type[T] | None = None, name: str = "", dep_type_name: str = ""
) -> T:
    """寻找依赖"""
    res: T | None = None
    while True:
        # 先等获取到application
        application = CommonVar.get_app(stack_path)
        if application:
            break
    sv: ScannerVar = application.sv
    # 开始计时，装配
    start = time.time()
    while True:
        timeout_second = sv.get_scan_timeout_second()
        print("\r", end="")
        if inject_type == InjectType.NAME:
            msg = f"名为 {name} "
            if res := find_dependency_once(InjectType.NAME, stack_path, name=name):
                break
        elif inject_type == InjectType.TYPE:
            msg = f"类型为 {DepType.__name__ if DepType else ...}"
            if res := find_dependency_once(InjectType.TYPE, stack_path, DepType=DepType):
                break
        elif inject_type == InjectType.NAME_OF_TYPE:
            msg = f"类型为 {dep_type_name}"
            if res := find_dependency_once(InjectType.NAME_OF_TYPE, stack_path, dep_type_name=dep_type_name):
                break
        time.sleep(0.1)
        if time.time() - start > timeout_second:
            raise InjectFailException(f"扫描超时，{msg} 的依赖未找到")
    return res


T = TypeVar("T")
MatMulProps = type["Inject"] | type[T]


class AtUsable(type):
    """@运算支持元类"""

    def __new__(cls, name, bases, dct):
        return super().__new__(cls, name, bases, dct)

    def __matmul__(self: type["Inject"], other: type[T]) -> T:
        # 使用@的情况不考虑ForwardRef，规定只能用类型，不能用字符串，不然类定义在后面，导入时阻塞扫描，也注入不了
        return find_dependency(InjectType.TYPE, get_stack_path(1), DepType=other)

    def __rmatmul__(self: type["Inject"], other: type[T]) -> T:
        return find_dependency(InjectType.TYPE, get_stack_path(1), DepType=other)


class Inject(metaclass=AtUsable):
    """注入依赖"""

    INJECT_NAME = None

    def __new__(cls, DepType: type[T], name: str | None = None) -> T:
        stack_path = get_stack_path(1)
        if name:
            return find_dependency(InjectType.NAME, stack_path, name=name)
        else:
            return find_dependency(InjectType.TYPE, stack_path, DepType=DepType)

    @classmethod
    def Qualifier(cls, name: str) -> type["Inject"]:
        class Temp(cls):
            INJECT_NAME = name

            def __new__(cls, DepType: type[T]):
                stack_path = get_stack_path(1)
                return find_dependency(InjectType.NAME, stack_path, name=name)

        return Temp
