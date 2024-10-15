from typing import Final, List

from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.model.route_model import RouteRecordItem


class RoutesVar:
    """存储应用创建过程中路由相关的变量即获取方法"""

    def __init__(self, scanner_var: ScannerVar, need_pure_api: bool):
        # 是否使用纯api，即删除自带的路由文档路由. Defaults to False.
        self._need_pure_api: bool = need_pure_api
        self.sv = scanner_var
        # 每个路由的记录，会随着匹配叠加
        self._route_record_list: Final[List[RouteRecordItem]] = []

    # ----------------------------------------------------- 是否使用纯api ----------------------------------------------------- #

    def get_need_pure_api(self) -> bool:
        return self._need_pure_api

    def set_need_pure_api(self, v: bool):
        self._need_pure_api = v

    # ------------------------------------------------------ 路由记录 ------------------------------------------------------ #

    def get_route_record_list(self) -> List[RouteRecordItem]:
        """获取所有路由记录列表

        Returns:
            List[RouteRecordItem]: 结果
        """
        return self._route_record_list

    def add_route_record(self, item: RouteRecordItem):
        self.get_route_record_list().append(item)
