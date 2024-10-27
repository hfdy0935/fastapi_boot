from collections.abc import Callable
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import (
    Annotated,
    Generic,
    TypeVar,
    Union,
)
from fastapi import APIRouter
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.utils.get import get_dot_path


# ------------------------------------------------------- 模块/包 ------------------------------------------------------- #


class ModPkgItem:
    def __init__(self, path: str):
        # 模块所在系统路径
        self.mod_sys_path = path

    @property
    def is_mod(self):
        return not os.path.isdir(self.mod_sys_path)

    @property
    def dot_path(self):
        """模块所在项目路径"""
        return get_dot_path(self.mod_sys_path)

    @property
    def dir_sys_path(self):
        """模块所在目录路径"""
        return os.path.dirname(self.mod_sys_path)

    @property
    def parts(self) -> list[str]:
        return self.dot_path.split(".")

    def contains(self, path: str) -> bool:
        """是否包含某个路径（包/模块在项目中的路径），用于排除扫描路径"""
        parts = Path(path).parts
        # 从头开始比较，相同部分
        same_head = [1 for i, j in zip(parts, self.parts) if i == j]
        # 相同部分 = app所在目录系统路径
        return len(same_head) == len(parts)

    def isin(self, path: str) -> bool:
        """检测path是不是FastApiBoot的启动类所在的目录内的文件"""
        return not self.contains(path)


# -------------------------------------------------------- 配置 -------------------------------------------------------- #
@dataclass
class Config:
    need_pure_api: Annotated[bool, "是否删除自带的api"] = False
    scan_timeout_second: Annotated[int, "扫描超时时间，超时未找到报错"] = 10
    exclude_scan_path: Annotated[list[str], "忽略扫描的模块或包在项目中的点路径"] = field(default_factory=list)
    include_scan_path: Annotated[list[str], "额外扫描的模块或包在项目中的点路径"] = field(default_factory=list)


# -------------------------------------------------------- 控制器 ------------------------------------------------------- #
class ControllerItem:
    """控制器"""

    def __init__(self, symbol: Symbol, router: APIRouter) -> None:
        self.symbol = symbol
        self.router = router

    @property
    def dict(self) -> dict:
        return dict(symbol=self.symbol, router=self.router)


# ------------------------------------------------------- 依赖注入 ------------------------------------------------------- #

T = TypeVar("T")


@dataclass
class InjectItem(Generic[T]):
    """依赖注入的模型"""

    symbol: Symbol
    name: str | None
    constructor: Union[Callable, type[T]]
    value: T | None = None
