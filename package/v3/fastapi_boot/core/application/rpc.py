from fastapi_boot.core.decorator.controller.controller import Controller
from fastapi_boot.enums import RequestMethodEnum, RequestMethodStrEnum
from fastapi_boot.model.route import BaseHttpRouteItem, ControllerRecord
from fastapi_boot.model.scan import DepRecord


class RpcApplication:
    """远程调用相关的"""

    def __init__(self):
        # 控制器记录字典
        self.__controller_route_records_dict: dict[str, ControllerRecord] = {}
        # RpcClient的依赖
        self.__dep_list: list[DepRecord] = []

    # ------------------------------------------------------- 添加和获取路由 ------------------------------------------------------- #
    def add_controller_route_records(self, ctrl: Controller):
        """添加路由记录"""
        for route_record in ctrl.total_route_record_list:
            if isinstance(route_record, BaseHttpRouteItem):
                for method in route_record.methods:
                    key = (
                        route_record.path
                        + ":"
                        + (method.value if isinstance(method, RequestMethodEnum) else method.upper())
                    )
                    self.__controller_route_records_dict.update(
                        {key: ControllerRecord(ctrl.decorated_instance, route_record)}
                    )
            else:
                key = route_record.path + ':' + RequestMethodEnum.WEBSOCKET.value
                self.__controller_route_records_dict.update(
                    {key: ControllerRecord(ctrl.decorated_instance, route_record)}
                )

    def get_controller_route_records_by_path_and_method(
        self, path: str, method: RequestMethodEnum | RequestMethodStrEnum
    ) -> ControllerRecord | None:
        """获取路由记录

        Args:
            path (str): 请求路径

        Returns:
            ControllerRecord | None: 结果，可能是None
        """
        key = path + ':' + (method.value if isinstance(method, RequestMethodEnum) else method.upper())
        return self.__controller_route_records_dict.get(key)

    # ------------------------------------------------------- 依赖注入 ------------------------------------------------------- #
    def add_dep(self, dep: DepRecord):
        self.__dep_list.append(dep)

    def get_dep_list(self):
        return self.__dep_list
