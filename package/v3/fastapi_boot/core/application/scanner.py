from inspect import isclass
import os
from threading import Thread
from typing import Any, Generic, Literal, TypeVar

from fastapi_boot.core.var.constants import ORI_OBJ, ROUTE_TYPE
from fastapi_boot.core.var.routes import RoutesVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.enums.scan_enum import RouteType
from fastapi_boot.exception.bean import InjectFailException
from fastapi_boot.model.scan_model import (
    ControllerItem,
    InjectItem,
    ModPkgItem,
)

from fastapi_boot.utils.transformer import trans_cls_deps, trans_endpoint

T = TypeVar("T")
# 注入方式，按类型或名称
InjectType = Literal["name", "type"]


def scan_task(idx: int, ls: list[str], path: str):
    """扫描"""
    print("\r" + " " * 120, end="")
    print(
        f"\r正在扫描：{(idx + 1) * 100 / len(ls):.2f}% {path}",
        end="",
    )
    __import__(path)


class ScannerApplication(Generic[T]):
    """扫描应用"""

    def __init__(self, routes_var: RoutesVar, scanner_var: ScannerVar, setup_stack_path: str):
        self.rv = routes_var
        self.sv = scanner_var
        # 启动类所在路径
        self.__setup_stack_path = setup_stack_path

    # ----------------------------------------------------- 遍历获取模块类列表 ---------------------------------------------------- #

    def _walk_module_path_list(self, scan_path: str, dot_prefix: str):
        """遍历扫描路径，获得项目下所有模块的路径类列表

        Args:
            scan_path (str): 扫描路径
        """
        for i in os.walk(scan_path):
            # dirpath: 包在系统的绝对路径
            dirpath, _, filenames = i
            # 包中的所有模块
            for filename in filenames:
                # 只扫描.py文件
                if not filename.endswith(".py"):
                    continue
                # 如果在需要排除扫描列表中，跳过
                need_ignore_this_module = False
                mod_item = ModPkgItem(os.path.join(dirpath, filename))
                for i in self.sv.get_exclude_path_list():
                    if mod_item.contains(i):
                        need_ignore_this_module = True
                        break
                if need_ignore_this_module:
                    continue
                self.sv.add_mod_item(mod_item)

    # -------------------------------------------------- 导包，让装饰器静态阶段生效 ------------------------------------------------- #

    def _init_bean_list(self):
        """初始化项目中所有bean"""
        tasks: list[Thread] = []

        for idx, mod in enumerate((ls := self.sv.get_mod_list())):
            #  导入模块，这里就把该模块内的所有的装饰器执行完了
            target = Thread(
                target=scan_task,
                args=(idx, ls, mod.dot_path),
            )
            tasks.append(target)
            target.start()

        for t in tasks:
            t.join()
        # 扫描额外扫描路径
        for p in self.sv.get_include_path_list():
            __import__(p)
        print(f"\n> > 扫描完成")

    # ----------------------------------------------------- 注入依赖 ---------------------------------------------------- #

    def _handle_inject_result(self, find_list: list[InjectItem[T]], raise_msg: str) -> T | None:
        """处理注入结果"""
        # 如果没找到
        l = len(find_list)
        if l == 0:
            return None
        # 如果找到多个
        if l > 1:
            raise_pos = "\n".join([f"\t{idx}. {i.symbol.pos}" for idx, i in enumerate(find_list, start=1)])
            raise InjectFailException(f"找到{l}个依赖，注入失败，{raise_msg}，依赖位置：\n{raise_pos}")
        # 只有一个
        return find_list[0].value

    def inject_by_type(self, DepType: type[T]) -> T | None:
        """根据类型注入依赖"""
        res: list[InjectItem[T]] = []
        for b in self.sv.get_inject_list():
            # 考虑到Bean返回字符串，类型后定义的情况
            if b.constructor == DepType or b.constructor == DepType.__name__:
                res.append(b)
        return self._handle_inject_result(res, f"确保类型{DepType.__name__}只对应一个依赖，或使用命名依赖")

    def inject_by_name(self, name: str) -> T | None:
        """根据名称注入依赖"""
        res: list[InjectItem[T]] = []
        for b in self.sv.get_inject_list():
            if b.name == name:
                res.append(b)
        return self._handle_inject_result(res, f"确保依赖名{name}唯一")

    def inject_by_type_name(self, type_name) -> T | None:
        """根据类型名注入，考虑到使用 '类型' 的方式写类型，得到的是个 typing.ForwardRef 实例，用 __forward_arg__ 取出字符串/类型名"""
        res: list[InjectItem[T]] = []
        for b in self.sv.get_inject_list():
            # ForwardRef的情况
            if isinstance(b.constructor, str):
                if b.constructor == type_name:
                    res.append(b)
            # 其他情况
            elif b.constructor.__name__ == type_name:

                res.append(b)
        return self._handle_inject_result(res, f"确保类型{type_name}只对应一个依赖，或使用命名依赖")

    # ----------------------------------------------------- 处理请求方法和请求的公共依赖 ---------------------------------------------------- #

    def _handle_endpoint_deps(self, cls: type[Any], ctrl: ControllerItem):
        """处理请求映射方法和类的公共依赖"""
        for k, v in cls.__dict__.items():
            if (
                hasattr(v, ORI_OBJ)
                and (o := getattr(v, ORI_OBJ))
                and getattr(o, ROUTE_TYPE, None) == RouteType.ENDPOINT
            ):
                # 1. endpoint
                trans_endpoint(o, cls)
            if isclass(v):
                self._handle_endpoint_deps(v, ctrl)
        # 2. deps
        trans_cls_deps(cls, self.__setup_stack_path)

    def scan(self, scan_path: str, dot_prefix: str):
        """
        Args:
            scan_path (str): 扫描路径
            dot_prefix (str): 启动文件在项目中的位置（不含启动文件），点前缀
        """
        self._walk_module_path_list(scan_path, dot_prefix)
        self._init_bean_list()

    def handle_controller_list(self):
        """
        - 处理控制器
        """
        for ctrl in self.sv.get_controller_list():
            # 只挂载CBV，FBV会自动挂载
            if isclass((obj := getattr(ctrl, ORI_OBJ))):
                self._handle_endpoint_deps(obj, ctrl)
