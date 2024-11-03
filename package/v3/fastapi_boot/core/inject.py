import time
from typing import TypeVar

from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.enums import DepPos, InjectType
from fastapi_boot.exception import AppNotFoundException, InjectFailException
from fastapi_boot.utils import get_stack_path

T = TypeVar("T")


def get_dep_pos(stack_path: str):
    """在无app模块还是子应用中"""
    try:
        GlobalVar.get_app(stack_path)
        return DepPos.APP
    except AppNotFoundException:
        return DepPos.NO_APP


def find_dependency_once(
    inject_type: InjectType, stack_path: str, DepType: type[T], name: str = "", dep_type_name: str = ""
):
    """寻找 一次 依赖，找不到返回None；此时已挂载

    Args:
        inject_type (InjectType): 依赖注入方式
        stack_path (str): 调用栈路径
        DepType (type[T]): 类型
        name (str, optional): 依赖名. Defaults to "".
        dep_type_name (str, optional): 类型名. Defaults to "".

    Returns:
        _type_: 找到了就返回结果，找不到返回None
    """
    dep_pos = get_dep_pos(stack_path)
    if dep_pos == DepPos.APP:
        application = GlobalVar.get_app(stack_path)
        if inject_type == InjectType.NAME:
            res = application.sa.inject_by_name(name, DepType)
        elif inject_type == InjectType.TYPE:
            res = application.sa.inject_by_type(DepType)
        elif inject_type == InjectType.NAME_OF_TYPE:
            res = application.sa.inject_by_type_name(dep_type_name)
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
    """寻找依赖"""
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


T = TypeVar("T")
MatMulProps = type["Inject"] | type[T]


def resolve_at(self: type["Inject"], other: type[T], stack_path: str):
    """处理左@和右@，@时不考虑ForwardRef"""
    if self.INJECT_TYPE == InjectType.TYPE:
        return find_dependency(InjectType.TYPE, stack_path, DepType=other)
    else:
        return find_dependency(InjectType.NAME, stack_path, DepType=other, name=self.INJECT_NAME)


class AtUsable(type):
    """@运算支持元类"""

    def __new__(cls, name, bases, dct):
        return super().__new__(cls, name, bases, dct)

    def __matmul__(self: type["Inject"], other: type[T]) -> T:
        return resolve_at(self, other, get_stack_path(1))

    def __rmatmul__(self: type["Inject"], other: type[T]) -> T:
        return resolve_at(self, other, get_stack_path(1))


class Inject(metaclass=AtUsable):
    """注入依赖"""

    INJECT_TYPE = InjectType.TYPE
    INJECT_NAME = ""

    def __new__(cls, DepType: type[T], name: str | None = None) -> T:
        """直接调用，判断有没有name"""
        stack_path = get_stack_path(1)
        if name:
            return find_dependency(InjectType.NAME, stack_path, DepType=DepType, name=name)
        else:
            return find_dependency(InjectType.TYPE, stack_path, DepType=DepType)

    @classmethod
    def Qualifier(cls, name: str) -> type["Inject"]:
        """按依赖名注入"""

        # 不修改原类
        class Cls(cls):
            INJECT_TYPE = InjectType.NAME
            INJECT_NAME = name

        return Cls
