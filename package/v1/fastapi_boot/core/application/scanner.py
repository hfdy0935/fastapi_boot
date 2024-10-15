import inspect
import os
from pathlib import Path
from typing import Any, Generic, List, Optional, Type, TypeVar

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.routes import RoutesVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.enums.route import RouteType
from fastapi_boot.exception.bean import AutoWiredFailException
from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.scan.bean import BeanItem
from fastapi_boot.model.scan.module_path_item import ModulePathItem
from fastapi_boot.utils.generator import get_stack_path

T = TypeVar('T')


class ScannerApplication(Generic[T]):
    """扫描应用，负责扫描项目中的模块，并交给RoutesApplication受控
    """

    def __init__(self, routes_var: RoutesVar, scanner_var: ScannerVar):
        self.rv = routes_var
        self.sv = scanner_var
        # 排除项目启动文件，不扫描
        self.sv.add_exclude_path(get_stack_path(3))

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
            pkg_pro_abs_ln_path = dirpath.replace(
                scan_path, '')[1:]  # 如果开头有斜杠就去掉
            if (l := dot_prefix.split('.')):
                pkg_pro_abs_ln_path = os.path.join(*l, pkg_pro_abs_ln_path)
            # 包中的所有模块
            for filename in filenames:
                if not filename.endswith('.py'):
                    continue
                # 模块在系统中的绝对路径，以/分隔
                mod_sys_abs_ln_path = os.path.join(dirpath, filename)
                # 如果在需要排除扫描列表中，跳过
                need_exit_this_module = False
                for i in self.sv.get_exclude_path_list():
                    if i in mod_sys_abs_ln_path:
                        need_exit_this_module = True
                if need_exit_this_module:
                    continue
                # 模块在项目中的绝对路径，以/分隔
                mod_pro_abs_ln_path = os.path.join(
                    pkg_pro_abs_ln_path, filename)
                # 模块在项目中的绝对路径，以.分隔
                mod_pro_abs_dot_path = '.'.join(
                    Path(mod_pro_abs_ln_path[:-3]).parts)
                self.sv.add_mod_path_list(
                    ModulePathItem(mod_sys_abs_ln_path=mod_sys_abs_ln_path, mod_pro_abs_dot_path=mod_pro_abs_dot_path, mod_pro_abs_ln_path=mod_pro_abs_ln_path))

    # -------------------------------------------------- 导包，让装饰器静态阶段生效 ------------------------------------------------- #

    def _init_bean_list(self):
        """初始化项目中所有bean
        """
        num = 0
        for idx, mod in enumerate((l := self.sv.get_mod_path_list())):
            # 排除扫描包/模块
            if mod.mod_pro_abs_dot_path in self.sv.get_exclude_path_list():
                continue
            #  导入模块，这里就把该模块内的所有的装饰器执行完了
            __import__(mod.mod_pro_abs_dot_path)
            print(
                f'\r正在扫描：{(idx+1)*100/len(l):.2f}% {mod.mod_pro_abs_dot_path}', end='')
        print(f'\n> > 项目 {mod.mod_pro_abs_dot_path.split(".")[0]} 扫描完成')

    # ----------------------------------------------------- 自动装配 ---------------------------------------------------- #

    def get_bean_by_type(self, BeanType_: Type[T]) -> Optional[T]:
        """根据bean类型找到对应的已装配好的bean实例

        Args:
            BeanType_ (Type[T]): 需要自动装配的bean类型

        Returns:
            Optional[T]: bean实例，没找到返回None
        """
        res: List[BeanItem] = []
        # Bean
        for i in self.sv.get_bean_list():
            if i.annotations.get('return') == BeanType_ and i.value:
                res.append(i)
        # 其他组件
        for i in [*self.sv.get_controller_list(), *self.sv.get_service_list(), *self.sv.get_repository_list(), *self.sv.get_component_list()]:
            if i.constructor == BeanType_:
                res.append(i)
        if res == []:
            return None
        # 只要是一个组件一个类，貌似不可能重复...
        if (c := len(res)) > 1:
            raise_pos = '\n'.join([
                f'\t{idx}. {i.symbol.pos}' for idx, i in enumerate(res, start=1)])
            raise AutoWiredFailException(
                f'找到{c}个Bean，自动装配失败，确保类型{BeanType_.__name__}只对应一个Bean，错误位置：\n{raise_pos}')
        return res[0].value

    def get_bean_by_name(self, name: str) -> Optional[Any]:
        """根据bean名找到对应的已装配好的bean实例

        Args:
            name (str): 名

        Returns:
            Optional[Optional[T]: 装配结果
        """
        res: List[BeanItem] = []
        for i in [*self.sv.get_bean_list(), *self.sv.get_controller_list(), *self.sv.get_service_list(), *self.sv.get_repository_list(), *self.sv.get_component_list()]:
            if i.name == name:
                res.append(i)
        if res == []:
            return None
        if (c := len(res)) > 1:
            raise_pos = '\n'.join([
                f'\t{idx}. {i.symbol.pos}' for idx, i in enumerate(res, start=1)])
            raise AutoWiredFailException(
                f'找到{c}个Bean，自动装配失败，确保名{name}只对应一个Bean，错误位置：\n{raise_pos}')
        return res[0].value

    # ------------------------------------------------- 处理控制器的route_info ------------------------------------------------ #

    def _handle_class_route_info(self, _cls: Type[Any]):
        """
        - 处理内部控制类的route_info，_cls是未装饰的类
        """
        self_route_info = self.rv.get_route_layer_by_symbol(
            Symbol.from_obj(_cls))
        # setattr(_cls, CommonVar.ROUTE_INFO, self_route_info)

        for k, v in _cls.__dict__.items():
            # 替换useRoute()的值
            if v == CommonVar.ROUTE_PLACEHOLDER:
                setattr(_cls, k, self_route_info)
            # 排除未装饰的和在原类上设置的装饰类
            elif (not hasattr(v, CommonVar.ORI_OBJ)) or k == CommonVar.DEC_OBJ:
                continue
            elif (o := getattr(v, CommonVar.ORI_OBJ)) and getattr(o, CommonVar.ROUTE_TYPE) == RouteType.INNER_CBV:
                self._handle_class_route_info(o)

    def _handle_route_info(self):
        """
        - 处理控制器的route_info
        """
        for ctrl in self.sv.get_controller_list():
            cons = ctrl.constructor
            if inspect.isclass(cons):
                self._handle_class_route_info(cons)
            elif inspect.isfunction(cons):
                # 给加了装饰器的函数加属性
                obj=getattr(cons, CommonVar.DEC_OBJ) if hasattr(cons, CommonVar.DEC_OBJ) else cons
                setattr(obj, CommonVar.ROUTE_INFO, self.rv.get_route_layer_by_symbol(
                    Symbol.from_obj(cons)))

    # ------------------------------------------------------ 扫描 ------------------------------------------------------ #

    def scan(self, scan_path: str, dot_prefix: str):
        """扫描项目

        Args:
            scan_path (str): 扫描路径
        """
        # 1. 遍历获取模块类列表
        self._walk_module_path_list(scan_path, dot_prefix)
        # 2. 扫描，导包，让装饰器静态阶段生效
        self._init_bean_list()
        # 3. 计算出所有Controller及内部控制类的route_info
        self._handle_route_info()
