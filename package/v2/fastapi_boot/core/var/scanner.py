from inspect import isclass
from typing import Any, Final, Generic, List, Type, TypeVar, Union

from fastapi.routing import APIRoute, APIWebSocketRoute
from starlette.routing import BaseRoute

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.model.scan_model import BeanItem, ControllerItem, ModulePathItem


T = TypeVar("T")


class ScannerVar(Generic[T]):
    """存储应用创建过程中扫描相关的变量"""

    def __init__(
        self, scan_timeout_second: Union[int, float], exclude_path_list: List[str],include_path_list:List[str]
    ):
        self._scan_timeout_second = scan_timeout_second
        # 需要排除的包/模块在项目中的点路径
        self._exclude_path_list: Final[List[str]] = exclude_path_list
        # 需要额外扫描的包/模块在项目中的点路径
        self._include_path_list:Final[List[str]]=include_path_list

        # 项目下所有模块的路径类列表
        self._mod_path_list: Final[List[ModulePathItem]] = []
        self._bean_list: Final[List[BeanItem]] = []
        self._component_list: Final[List[BeanItem]] = []
        self._controller_list: Final[List[ControllerItem]] = []
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

    # -------------------------------------------------------------------------------------------------------------------- #

    def get_exclude_path_list(self) -> List[str]:
        """获取需要排除的包/模块在项目中的绝对路径，以.分隔

        Returns:
            List[str]: 字符串列表
        """
        return self._exclude_path_list

    def add_exclude_path(self, path: str):
        """添加需要排除扫描的包/模块

        Args:
            path (str): 包/模块在项目的绝对路径，以.分隔
        """
        if not path in self._exclude_path_list:
            self._exclude_path_list.append(path)
    
    def get_include_path_list(self)->List[str]:
        return self._include_path_list

    # -------------------------------------------------- bean list ------------------------------------------------- #

    def get_bean_list(self) -> List[BeanItem]:
        return self._bean_list

    def add_bean(self, item: BeanItem):
        self.get_bean_list().append(item)

    def get_component_list(self) -> List[BeanItem]:
        return self._component_list

    def add_component(self, item: BeanItem):
        self.get_component_list().append(item)

    def get_controller_list(self) -> List[ControllerItem]:
        return self._controller_list

    def is_controller(self, symbol: Symbol) -> bool:
        """判断该symbol是否是属于控制器"""
        for i in self.get_controller_list():
            if i.symbol.equals(symbol):
                return True
        return False

    def add_controller(self, item: ControllerItem):
        self.get_controller_list().append(item)

    def get_service_list(self) -> List[BeanItem]:
        return self._service_list

    def add_service(self, item: BeanItem):
        self.get_service_list().append(item)

    def get_repository_list(self) -> List[BeanItem]:
        return self._repository_list

    def add_repository(self, item: BeanItem):
        self.get_repository_list().append(item)

    # ----------------------------------------------------- other -----------------------------------------------------

    def get_scan_timeout_second(self) -> Union[int, float]:
        return self._scan_timeout_second

    def set_scan_timeout_second(self, timeout_second: Union[int, float]):
        self._scan_timeout_second = timeout_second

    # ---------------------------------------- add routes to CBV and prefix_class ---------------------------------------- #

    def _get_routes_of_prefix_class(
        self, cls: Type[T], routes: List[BaseRoute]
    ) -> List[APIRoute]:
        res: List[Any] = []
        for r in routes:
            assert isinstance(r, APIRoute) or isinstance(r, APIWebSocketRoute)
            endpoint_symbol = Symbol.from_obj(r.endpoint)
            if endpoint_symbol.contains(Symbol.from_obj(cls)):
                res.append(r)
        return res

    def _handle_routes(self, cls: Type[Any], ctrl: ControllerItem):
        """
        - only handle routes
        """
        for k, v in cls.__dict__.items():
            if v == CommonVar.ROUTES_PLACEHOLDER:
                setattr(
                    cls, k, self._get_routes_of_prefix_class(cls, ctrl.router.routes)
                )
            if isclass(v):
                self._handle_routes(v, ctrl)

    def handle_routes(self):
        """
        - do this after router being mounted
        """
        for ctrl in self.get_controller_list():
            if isclass((obj := getattr(ctrl, CommonVar.ORI_OBJ))):
                self._handle_routes(obj, ctrl)
