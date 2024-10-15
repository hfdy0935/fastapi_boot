from inspect import isclass
import os
from pathlib import Path
from threading import Thread
from typing import Any, Generic, List, Optional, Type, TypeVar
from concurrent.futures import ThreadPoolExecutor

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.routes import RoutesVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.enums.scan_enum import RouteType
from fastapi_boot.exception.bean import AutoWiredFailException
from fastapi_boot.model.scan_model import BeanItem, ControllerItem, ModulePathItem
from fastapi_boot.utils.transformer import trans_cls_deps, trans_endpoint

T = TypeVar("T")


class ScannerApplication(Generic[T]):
    """扫描应用，负责扫描项目中的模块，并交给RoutesApplication受控"""

    def __init__(self, routes_var: RoutesVar, scanner_var: ScannerVar):
        self.rv = routes_var
        self.sv = scanner_var

    # ----------------------------------------------------- 遍历获取模块类列表 ---------------------------------------------------- #
    def _walk_module_path_list(self, scan_path: str, dot_prefix: str):
        """遍历扫描路径，获得项目下所有模块的路径类列表

        Args:
            scan_path (str): 扫描路径
        """
        for i in os.walk(scan_path):
            # dirpath: 包在系统的绝对路径
            dirpath, _, filenames = i
            # 包在项目的绝对路径，以/分隔，如果还有父项目还需要加上前缀
            pkg_pro_abs_ln_path = dirpath.replace(scan_path, "")[
                                  1:
                                  ]  # 如果开头有斜杠就去掉
            if l := dot_prefix.split("."):
                pkg_pro_abs_ln_path = os.path.join(*l, pkg_pro_abs_ln_path)
            # 包中的所有模块
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                # 模块在系统中的绝对路径，以/分隔
                mod_sys_abs_ln_path = os.path.join(dirpath, filename)
                # 模块在项目中的绝对路径，以/分隔
                mod_pro_abs_ln_path = os.path.join(pkg_pro_abs_ln_path, filename)
                # 模块在项目中的绝对路径，以.分隔
                mod_pro_abs_dot_path = ".".join(Path(mod_pro_abs_ln_path[:-3]).parts)
                # 如果在需要排除扫描列表中，跳过
                need_ignore_this_module = False
                for i in self.sv.get_exclude_path_list():
                    if i == mod_sys_abs_ln_path:
                        need_ignore_this_module = True
                    else:
                        exclude_dot_path = i.split('.')
                        judge_dot_path = mod_pro_abs_dot_path.split('.')
                        contain = [1 for t1, t2 in zip(exclude_dot_path, judge_dot_path) if t1 == t2]
                        if len(contain) == len(exclude_dot_path):
                            need_ignore_this_module = True
                if need_ignore_this_module:
                    continue
                self.sv.add_mod_path_list(
                    ModulePathItem(
                        mod_sys_abs_ln_path=mod_sys_abs_ln_path,
                        mod_pro_abs_dot_path=mod_pro_abs_dot_path,
                        mod_pro_abs_ln_path=mod_pro_abs_ln_path,
                    )
                )

    # -------------------------------------------------- 导包，让装饰器静态阶段生效 ------------------------------------------------- #

    def _init_bean_list(self):
        """初始化项目中所有bean"""
        tasks:List[Thread]=[]
        def task(ls:List[str],path:str):
                print(
                    f"\r正在扫描：{(idx + 1) * 100 / len(ls):.2f}% {path}",
                    end="",
                )
                __import__(path)
        for idx, mod in enumerate((ls := self.sv.get_mod_path_list())):
            #  导入模块，这里就把该模块内的所有的装饰器执行完了
            target=Thread(target=task,args=(ls,mod.mod_pro_abs_dot_path,))
            tasks.append(target)
            target.start()
        for t in tasks:
            t.join()
        # 扫描额外扫描路径
        for p in self.sv.get_include_path_list():
            __import__(p)
        print(f'\n> > 项目 {mod.mod_pro_abs_dot_path.split(".")[0]} 扫描完成')

    # ----------------------------------------------------- 自动装配 ---------------------------------------------------- #

    def get_bean_by_type(self, bean_type_: Type[T]) -> Optional[T]:
        """根据bean类型找到对应的已装配好的bean实例

        Args:
            bean_type_ (Type[T]): 需要自动装配的bean类型

        Returns:
            Optional[T]: bean实例，没找到返回None
        """
        res: List[BeanItem] = []
        # Bean
        # for i in self.sv.get_bean_list():
        #     if i.annotations.get("return") == bean_type_ and i.value:
        #         res.append(i)
        # 其他组件
        for i in [
            *self.sv.get_bean_list(),
            *self.sv.get_service_list(),
            *self.sv.get_repository_list(),
            *self.sv.get_component_list(),
        ]:
            if i.constructor == bean_type_:
                res.append(i)
        if not res:
            return None
        # 只要是一个组件一个类，貌似不可能重复...
        if (c := len(res)) > 1:
            raise_pos = "\n".join(
                [f"\t{idx}. {i.symbol.pos}" for idx, i in enumerate(res, start=1)]
            )
            raise AutoWiredFailException(
                f"找到{c}个Bean，自动装配失败，确保类型{bean_type_.__name__}只对应一个Bean，错误位置：\n{raise_pos}"
            )
        return res[0].value

    def get_bean_by_name(self, name: str) -> Optional[Any]:
        """根据bean名找到对应的已装配好的bean实例

        Args:
            name (str): 名

        Returns:
            Optional[Optional[T]: 装配结果
        """
        res: List[BeanItem] = []
        for i in [
            *self.sv.get_bean_list(),
            *self.sv.get_service_list(),
            *self.sv.get_repository_list(),
            *self.sv.get_component_list(),
        ]:
            if i.name == name:
                res.append(i)
        if not res:
            return None
        if (c := len(res)) > 1:
            raise_pos = "\n".join(
                [f"\t{idx}. {i.symbol.pos}" for idx, i in enumerate(res, start=1)]
            )
            raise AutoWiredFailException(
                f"找到{c}个Bean，自动装配失败，确保名{name}只对应一个Bean，错误位置：\n{raise_pos}"
            )
        return res[0].value

    def _handle_endpoint_router_deps(self, cls: Type[Any], ctrl: ControllerItem):
        """
        - handle endpoint, router, deps
        - now routes is None, so we can add them after the router being mounted.
        """
        for k, v in cls.__dict__.items():
            if (
                    hasattr(v, CommonVar.ORI_OBJ)
                    and (o := getattr(v, CommonVar.ORI_OBJ))
                    and getattr(o, CommonVar.ROUTE_TYPE, None) == RouteType.ENDPOINT
            ):
                # 1. endpoint
                trans_endpoint(o, cls)
            # 2. router
            if v == CommonVar.ROUTER_PLACEHOLDER:
                setattr(cls, k, ctrl.router)
            if isclass(v):
                self._handle_endpoint_router_deps(v, ctrl)
        # 3. deps
        trans_cls_deps(cls)

    def scan(self, scan_path: str, dot_prefix: str):
        """
        Args:
            scan_path (str): scan path
            dot_prefix (str): dot prefix
        """
        self._walk_module_path_list(scan_path, dot_prefix)
        self._init_bean_list()

    def handle_controller_list(self):
        """
        - do this after the application loaded
        """
        for ctrl in self.sv.get_controller_list():
            if isclass((obj := getattr(ctrl, CommonVar.ORI_OBJ))):
                self._handle_endpoint_router_deps(obj, ctrl)
