import time
from typing import TypeVar

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.exception.bean import InjectFailException
from fastapi_boot.utils.get import get_stack_path
from typing import TypeVar

T = TypeVar("T")


def find_dependency(DepType: type[T], stack_path: str, name: str | None = None) -> T:
    res: T | None = None
    while True:
        # 先等获取到application
        application = CommonVar.get_app(stack_path)
        if application:
            break

    sa = application.sa
    sv: ScannerVar = application.sv
    # 开始计时，装配
    start = time.time()
    while True:
        timeout_second = sv.get_scan_timeout_second()
        print("\r", end="")
        if name != None:
            param = name
            if res := sa.inject_by_name(name):
                break
        else:
            param = DepType
            if res := sa.inject_by_type(DepType):
                break
        time.sleep(0.1)
        if time.time() - start > timeout_second:
            msg = f"名为 {param} " if isinstance(param, str) else f"类型为 {param.__name__} "
            raise InjectFailException(f"扫描超时，{msg} 的依赖未找到")
    return res


T = TypeVar("T")
MatMulProps = type["Inject"] | type[T]


class AtUsable(type):
    def __new__(cls, name, bases, dct):
        return super().__new__(cls, name, bases, dct)

    def __matmul__(self: type["Inject"], other: type[T]) -> T:
        return find_dependency(other, get_stack_path(1), self.INJECT_NAME)

    def __rmatmul__(self: type["Inject"], other: type[T]) -> T:
        return find_dependency(other, get_stack_path(1), self.INJECT_NAME)


class Inject(metaclass=AtUsable):
    """注入依赖"""

    INJECT_NAME = None

    def __new__(cls, DepType: type[T], name: str | None = None) -> T:
        stack_path = get_stack_path(1)
        return find_dependency(DepType, stack_path, name)

    @classmethod
    def Qualifier(cls, name: str) -> type["Inject"]:
        class Temp(cls):
            INJECT_NAME = name

            def __new__(cls, DepType: type[T]):
                stack_path = get_stack_path(1)
                return find_dependency(DepType, stack_path, name)

        return Temp
