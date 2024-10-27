from typing import Final
from fastapi_boot.model.scan_model import (
    ControllerItem,
    InjectItem,
    ModPkgItem,
)


class ScannerVar:
    """扫描相关的变量"""

    def __init__(
        self,
        scan_timeout_second: int | float,
        exclude_path_list: list[str],
        include_path_list: list[str],
        setup_stack_path: str,
    ):
        # 扫描超时时间
        self.__scan_timeout_second = scan_timeout_second
        # 需要排除的包/模块在项目中的路径
        self.__exclude_path_list = exclude_path_list
        # 需要额外扫描的包/模块在项目中的路径
        self.__include_path_list = include_path_list

        # 项目下所有模块列表
        self.__mod_list: Final[list[ModPkgItem]] = []
        # 可注入的组件列表
        self.__inject_bean_list: Final[list[InjectItem]] = []
        self.__controller_list: Final[list[ControllerItem]] = []
        # 启动类所在路径
        self.__setup_stack_path = setup_stack_path

    # ------------------------------------------------ 所有模块 ------------------------------------------------ #

    def get_mod_list(self) -> list[ModPkgItem]:
        return self.__mod_list

    def add_mod_item(self, item: ModPkgItem):
        self.get_mod_list().append(item)

    # -------------------------------------------------------- 扫描 -------------------------------------------------------- #

    def get_exclude_path_list(self) -> list[str]:
        """获取需要排除的包/模块在项目中的绝对路径，以.分隔"""
        return self.__exclude_path_list

    def add_exclude_path(self, path: str):
        """添加需要排除扫描的包/模块"""
        if not path in self.__exclude_path_list:
            self.__exclude_path_list.append(path)

    def get_include_path_list(self) -> list[str]:
        """获取需要额外扫描的包/模块列表"""
        return self.__include_path_list

    # -------------------------------------------------------- 组件 -------------------------------------------------------- #

    def get_inject_list(self):
        return self.__inject_bean_list

    def add_inject(self, inject: InjectItem):
        self.get_inject_list().append(inject)

    def get_controller_list(self) -> list[ControllerItem]:
        return self.__controller_list

    def add_controller(self, item: ControllerItem):
        """考虑到uvicorn会扫描一次，启动时会扫描一次，写在启动文件中的组件会扫描两次的问题"""
        exists = len([c for c in self.get_controller_list() if c.symbol.equals(item.symbol)]) > 0
        if not exists:
            self.get_controller_list().append(item)

    # ----------------------------------------------------- 扫描时间 -----------------------------------------------------

    def get_scan_timeout_second(self) -> int | float:
        return self.__scan_timeout_second

    def set_scan_timeout_second(self, timeout_second: int | float):
        self.__scan_timeout_second = timeout_second
