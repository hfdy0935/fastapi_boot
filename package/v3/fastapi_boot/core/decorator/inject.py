from typing import TypeVar
from fastapi_boot.enums import InjectType
from fastapi_boot.utils.deps import find_dependency, get_real_type
from fastapi_boot.utils.pure import get_stack_path

T = TypeVar("T")


def resolve_at(self: type["Inject"], DepType: type[T], stack_path: str):
    """处理左@和右@，注入依赖，@时不考虑ForwardRef

    Args:
        self (type[&quot;Inject&quot;]): Inject类
        DepType (type[T]): 依赖类型
        stack_path (str): 调用栈文件系统路径

    Returns:
        _type_: 结果
    """
    if self.INJECT_TYPE == InjectType.TYPE:
        return find_dependency(InjectType.TYPE, stack_path, DepType=DepType)
    else:
        return find_dependency(InjectType.NAME, stack_path, DepType=DepType, name=self.INJECT_NAME)


class AtUsable(type):
    """@运算支持元类"""

    def __new__(cls, name, bases, dct):
        return super().__new__(cls, name, bases, dct)

    def __matmul__(self: type["Inject"], other: type[T]) -> T:
        # 获取真正要注入的依赖类型
        RealType = get_real_type(other)
        return resolve_at(self, RealType, get_stack_path(1))

    def __rmatmul__(self: type["Inject"], other: type[T]) -> T:
        RealType = get_real_type(other)
        ss = get_stack_path(1)
        return resolve_at(self, RealType, get_stack_path(1))


class Inject(metaclass=AtUsable):
    """注入依赖"""

    INJECT_TYPE = InjectType.TYPE
    INJECT_NAME = ""

    def __new__(cls, DepType: type[T], name: str | None = None) -> T:
        """直接调用，判断有没有name"""
        stack_path = get_stack_path(1)
        # 真实类型，考虑到非Bean依赖返回的是个函数，真正的类型在函数的DECORATED_FUNCTION_WRAPS_CLS属性上
        RealType = get_real_type(DepType)
        if name:
            return find_dependency(InjectType.NAME, stack_path, DepType=RealType, name=name)
        else:
            return find_dependency(InjectType.TYPE, stack_path, DepType=RealType)

    @classmethod
    def Qualifier(cls, name: str) -> type["Inject"]:
        """按依赖名注入"""

        # 不修改原类，避免后面的受前面的影响
        class Cls(cls):
            INJECT_TYPE = InjectType.NAME
            INJECT_NAME = name

        return Cls
