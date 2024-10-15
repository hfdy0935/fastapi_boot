from typing import Any, Final, Generic, List, TypeVar, Union

from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.scan.bean import BeanItem
from fastapi_boot.model.scan.module_path_item import ModulePathItem


T = TypeVar('T')


class ScannerVar(Generic[T]):
    """存储应用创建过程中扫描相关的变量
    """

    def __init__(self, scan_timeout_second: Union[int, float], exclude_path_lis: List[str] = []):
        # 自动装配超时时间
        self._scan_timeout_second = scan_timeout_second
        # 需要排除的包/模块在系统中的绝对路径，以斜杠、反斜杠分隔，//
        self._exclude_path_list: Final[List[str]] = exclude_path_lis

        # 项目下所有模块的路径类列表
        self._mod_path_list: Final[List[ModulePathItem]] = []
        # bean列表
        self._bean_list: Final[List[BeanItem]] = []
        self._component_list: Final[List[BeanItem]] = []
        self._controller_list: Final[List[BeanItem]] = []
        self._service_list: Final[List[BeanItem]] = []
        self._repository_list: Final[List[BeanItem]] = []

    # ------------------------------------------------ 项目下所有模块的路径类列表 ------------------------------------------------ #

    def get_mod_path_list(self) -> List[ModulePathItem]:
        """获取项目下所有模块的路径类列表

        Returns:
            List[ModulePathItem]: 项目下所有模块的路径类列表
        """
        return self._mod_path_list

    def add_mod_path_list(self, item: ModulePathItem):
        """向目下所有模块的路径类列表中添加一项

        Args:
            item (ModulePathItem): 要添加的模块路径类
        """
        self.get_mod_path_list().append(item)

    # ------------------------------------------------ 需要排除扫描的包/模块路径 ------------------------------------------------ #

    def get_exclude_path_list(self) -> List[str]:
        """获取需要排除的包/模块在系统中的绝对路径，以斜杠、反斜杠分隔

        Returns:
            List[str]: 字符串列表
        """
        return self._exclude_path_list

    def add_exclude_path(self, path: str):
        """添加需要排除扫描的包/模块

        Args:
            path (str): 包/模块在系统的绝对路径，以斜杠、反斜杠分隔
        """
        if not path in self._exclude_path_list:
            self._exclude_path_list.append(path)

    # -------------------------------------------------- 获取修改bean列表 ------------------------------------------------- #

    def get_bean_list(self) -> List[BeanItem]:
        return self._bean_list

    def add_bean(self, item: BeanItem):
        self.get_bean_list().append(item)

    def get_component_list(self) -> List[BeanItem]:
        return self._component_list

    def add_component(self, item: BeanItem):
        self.get_component_list().append(item)

    def get_controller_list(self) -> List[BeanItem]:
        return self._controller_list

    def is_controller(self, symbol: Symbol) -> bool:
        """判断该symbol是否是属于控制器
        """
        for i in self.get_controller_list():
            if i.symbol.equals(symbol):
                return True
        return False

    def add_controller(self, item: BeanItem):
        self.get_controller_list().append(item)

    def get_service_list(self) -> List[BeanItem]:
        return self._service_list

    def add_service(self, item: BeanItem):
        self.get_service_list().append(item)

    def get_repository_list(self) -> List[BeanItem]:
        return self._repository_list

    def add_repository(self, item: BeanItem):
        self.get_repository_list().append(item)

    # ----------------------------------------------------- 自动装配超时时间 -----------------------------------------------------
    def get_scan_timeout_second(self) -> Union[int, float]:
        return self._scan_timeout_second

    def set_scan_timeout_second(self, timeout_second: Union[int, float]):
        self._scan_timeout_second = timeout_second
