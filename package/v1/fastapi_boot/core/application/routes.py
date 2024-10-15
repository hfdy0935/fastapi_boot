import copy
from typing import List, Optional

from fastapi import FastAPI

from fastapi_boot.core.var.routes import RoutesVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.enums.route import RouteStatus
from fastapi_boot.model.routes.route_export import RouteLayerItem
from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.routes.route_record import RouteRecordItem


class RoutesApplication:
    """Route application, manage route initialization, control, activation"""

    def __init__(self, app: FastAPI, routes_var: RoutesVar, scanner_var: ScannerVar):
        self.app = app
        self.rv = routes_var
        self.sv = scanner_var

    # ------------------------------------------------------ 路由受控、激活 ----------------------------------------------------- #

    def control(self) -> int:
        """
        controll routes
        """
        return self._control_route_record_list(
            [i.symbol for i in self.sv.get_controller_list()]
        )

    def activate_and_register(self) -> int:
        """
        activate and register routes
        """
        # 是否只保留手动配置的api
        if self.rv.get_need_pure_api():
            self._filter_pure_api_routes()
        return self.activate_register_all_deactivated_route_record()

    # ------------------------------------------------------ 修改路由记录 ------------------------------------------------------ #

    def match_route_record_list(self, route: RouteRecordItem) -> int:
        """匹配单个路由，并修改路径

        - path修改举例：
            - 类：
                - 原来的`path`是`///c`，类的`path`是`//b`，则修改为`//b/c`
            - 函数：
                - 原来没有，直接加入（函数path的值一定在最后）

        Args:
            route (RouteRecordItem): 路由记录类

        Returns:
            int: 修改的路由数
        """
        # 深拷贝，不然会跟着变
        self.rv.get_all_route_record_list().append(copy.deepcopy(route))
        count = 0
        is_matched = False
        # 匹配路由记录
        for i in self.rv.get_route_record_list():
            if i.symbol.contains(route.symbol):
                # 第一次加函数，之后倒序向上遍历，每次在前面加一个/xxx，最终拼成完整路径
                # 得益于多个装饰器的调用顺序，每次不用不计算完整的路径
                path_list = i.path.split("/")
                path_list[len(route.symbol.context_path.split("/")) - 1] = route.path
                i.path = "/".join(path_list)
                count += 1
                # 添加的是类
                is_matched = True
        if not is_matched:
            self.rv.add_route_record(route)
            count += 1
        return count

    def _control_route_record_list(self, symbol_list: List[Symbol]) -> int:
        """使路由列表受控

        Args:
            symbol_list ( List[Symbol]): 所有要受控的路由所在类的Symbol实例的列表

        Returns:
            int: 修改的路由数
        """
        count = 0
        for i in self.rv.get_route_record_list():
            for s in symbol_list:
                if i.symbol.contains(s) and i.route_status == RouteStatus.UN_CONTROLLED:
                    # 先判断一下路由列表的路径，看是否有只有一个函数的情况（path = ''），需要改成 '/'
                    i.path = i.path if i.path else "/"
                    i.route_status = RouteStatus.DEACTIVATE
                    count += 1
        return count

    def _register_activate_route_record(self, route: RouteRecordItem):
        """注册传来已激活的路由

        Args:
            route (RouteRecordItem): 路由类实例

        Returns:
            int: 修改的路由数
        """
        assert (
            route.route_status == RouteStatus.ACTIVATE
            and route.endpoint
            and route.methods
        )
        params = route.params
        # websocket，请求参数和其他的不同
        if route.methods == [RequestMethodEnum.WEBSOCKET.value]:
            assert params
            self.app.add_api_websocket_route(
                path=route.path,
                endpoint=route.endpoint,
                name=params.name,
                dependencies=params.dependencies,
            )
        else:
            # 其他请求方法
            # 1. 如果有多个，一起加的话FastAPI生成路由唯一id会重复
            # self.app.add_api_route(path=r.path,
            #                     endpoint=r.endpoint, **ps.dict())
            # 源码：
            # def generate_unique_id(route: "APIRoute") -> str:
            #   operation_id = f"{route.name}{route.path_format}"
            #   operation_id = re.sub(r"\W", "_", operation_id)
            #   assert route.methods
            #   一个处理函数对应多个请求方法时，得到的id中的请求方法总是第一个请求方法
            #   operation_id = f"{operation_id}_{list(route.methods)[0].lower()}"
            #   return operation_id

            # 2. 试试分开加
            params_dict = params.dict() if params else {}
            for method in route.methods:
                # 每次只注册一个方法
                params_dict.update(dict(methods=[method]))
                self.app.add_api_route(
                    path=route.path, endpoint=route.endpoint, **params_dict
                )

    def activate_register_all_deactivated_route_record(self) -> int:
        """激活并注册所有于未激活状态的路由

        Returns:
            int: 修改的路由数
        """
        count = 0
        for i in self.rv.get_route_record_list():
            if i.route_status == RouteStatus.DEACTIVATE:
                i.route_status = RouteStatus.ACTIVATE
                self._register_activate_route_record(i)
                count += 1
        return count

    def _filter_pure_api_routes(self):
        """过滤除手动写的纯净api路由，删除自带的文档等路由"""
        for _ in range(4):
            self.app.routes.pop(0)

    # ------------------------------------------------------ 路由层级记录 ------------------------------------------------------ #

    def get_route_layer_list(self) -> List[RouteLayerItem]:
        """
        - 获取路由层级列表
        """
        return self.rv.get_route_layer_list()

    def get_route_layer_by_symbol(self, symbol: Symbol) -> Optional[RouteLayerItem]:
        """
        - 根据symbol获取路由层级信息
        """
        return self.rv.get_route_layer_by_symbol(symbol)
