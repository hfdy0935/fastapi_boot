from collections.abc import Callable
from dataclasses import dataclass, field
import inspect
import os
from pathlib import Path
from typing import (
    Annotated,
    Generic,
    TypeVar,
)
from fastapi_boot.constants import PROJ_SYS_PATH


# ------------------------------------------------------- 模块/包 ------------------------------------------------------- #


class ModPkgItem:

    def __init__(self, file_sys_path: str):
        """file_sys_path: 文件所在系统路径"""
        self.__file_sys_path = file_sys_path

    # ------------------------------------------------------- file ------------------------------------------------------ #
    @property
    def file_sys_path(self):
        """文件在系统的绝对路径"""
        return self.__file_sys_path

    @property
    def file_dot_parts(self):
        """文件在项目中的点路径parts"""
        # 去掉前面的项目路径和后面的.py
        return list(Path(self.file_sys_path[:-3]).parts[len(Path(PROJ_SYS_PATH).parts) :])

    @property
    def file_dot_path(self):
        """文件在项目中的点路径"""
        return ".".join(self.file_dot_parts)

    # -------------------------------------------------------- dir ------------------------------------------------------- #
    @property
    def dir_sys_path(self):
        """文件所在目录在系统的路径"""
        return os.path.dirname(self.__file_sys_path)

    @property
    def dir_dot_parts(self) -> list[str]:
        """文件所在路径在项目中的点路径parts"""
        return self.file_dot_parts[:-1]

    @property
    def dir_dot_path(self):
        """文件所在目录在项目中的点路径"""
        return ".".join(self.dir_dot_parts)

    # ------------------------------------------------------ methods ----------------------------------------------------- #

    def is_child_of_dot_path(self, dot_path: str):
        """本模块是否在点路径dot_path之下，用于排除和额外扫描路径"""
        sys_parts1 = Path(os.path.join(PROJ_SYS_PATH, *dot_path.split("."))).parts
        sys_parts2 = Path(self.file_sys_path[:-3]).parts  # 删除.py
        same_head = [1 for i, j in zip(sys_parts1, sys_parts2) if i == j]
        return len(same_head) == len(sys_parts1)

    def is_super_of_stack_path(self, stack_path: str):
        """本模块所在文件夹是否包含系统绝对路径stack_path，用于查找application"""
        sys_parts1 = Path(stack_path[:-3]).parts
        sys_parts2 = Path(self.dir_sys_path).parts

        same_head = [1 for i, j in zip(sys_parts1, sys_parts2) if i == j]
        return len(same_head) == len(sys_parts2)


# --------------------------------------------------- 所在模块和上下文路径的标识 -------------------------------------------------- #


@dataclass
class Symbol:
    """
    - 路由的唯一标识
    """

    mod_pkg_item: Annotated[ModPkgItem, "ModPkgItem实例"]
    context_path: Annotated[str, "该对象的上下文路径"]

    @staticmethod
    def from_obj(obj: type | Callable) -> "Symbol":
        """根据类/类的方法获取唯一symbol

        Args:
            obj (Callable): 要获取路径信息的对象（这里是类或函数）

        Returns:
            Symbol: symbol类实例，{文件绝对路径, 该对象在文件的引用路径}
        """
        stack_path = inspect.getfile(obj)
        stack_path = stack_path[0].upper() + stack_path[1:]
        context_path = obj.__qualname__
        return Symbol(ModPkgItem(stack_path), context_path=context_path)

    @classmethod
    def fake(cls, stack_path):
        return cls(ModPkgItem(stack_path), "")

    @property
    def stack_path(self) -> str:
        return self.mod_pkg_item.file_sys_path

    @property
    def pos(self) -> str:
        return f"{self.stack_path}  {self.context_path}"


# ------------------------------------------------------- 依赖注入 ------------------------------------------------------- #

T = TypeVar("T")


@dataclass
class InjectItem(Generic[T]):
    """依赖注入的模型"""

    symbol: Symbol
    name: str | None
    constructor: Callable | type[T]
    value: T | None = None


# -------------------------------------------------------- 项目配置 -------------------------------------------------------- #
@dataclass
class Config:
    need_pure_api: Annotated[bool, "是否删除自带的api"] = False
    scan_timeout_second: Annotated[int, "扫描超时时间，超时未找到报错"] = 10
    exclude_scan_paths: Annotated[list[str], "忽略扫描的模块或包在项目中的点路径"] = field(default_factory=list)
    include_scan_paths: Annotated[list[str], "额外扫描的模块或包在项目中的点路径"] = field(default_factory=list)
    max_scan_workers: Annotated[int, "扫描最大线程数，按照ThreadPoolExecutor的约定"] = field(
        default=min(32, (os.cpu_count() or 1) + 4)
    )


# ---------------------------------------------------- 主应用中要执行的任务，当前依赖没找到时添加 --------------------------------------------------- #
T = TypeVar("T")


class MountedTask(Generic[T]):
    def __init__(self, symbol: Symbol, task: Callable[..., T], args: list = [], done: bool = False):
        self.__symbol = symbol
        self.__task = task
        self.__args = args
        self.__done: bool = done

    def run(self) -> T:
        """执行"""
        self.__done = True
        return self.__task(*self.__args)

    @property
    def symbol(self):
        return self.__symbol

    @property
    def task(self):
        return self.__task

    @property
    def done(self):
        return self.__done

    def undo(self):
        """修改任务状态为未运行"""
        self.__done = False
