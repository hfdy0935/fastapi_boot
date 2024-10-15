from fastapi import FastAPI

from fastapi_boot.core.var.routes import RoutesVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.model.route_model import RouteRecordItem
from fastapi_boot.model.scan_model import ControllerItem


class RoutesApplication:
    """Route application, manage route initialization, control, activation"""

    def __init__(self, app: FastAPI, routes_var: RoutesVar, scanner_var: ScannerVar):
        self.app = app
        self.rv = routes_var
        self.sv = scanner_var

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

    def _filter_apis(self):
        for _ in range(4):
            self.app.routes.pop(0)

    def _mount_routes(self, c: ControllerItem):
        router = c.router
        for r in self.rv.get_route_record_list():
            if not r.symbol.contains(c.symbol):
                continue
            assert r.endpoint
            if r.methods == [RequestMethodEnum.WEBSOCKET.value]:
                assert r.params
                router.add_api_websocket_route(
                    path=r.path,
                    endpoint=r.endpoint,
                    name=r.params.name,
                    dependencies=r.params.dependencies,
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
                params_dict = r.params.model_dump() if r.params else {}
                for method in r.methods:
                    # 每次只注册一个方法
                    params_dict.update(dict(methods=[method]))
                    router.add_api_route(
                        path=r.path, endpoint=r.endpoint, **params_dict
                    )

    def register(self):
        if self.rv.get_need_pure_api():
            self._filter_apis()
        for c in self.sv.get_controller_list():
            self._mount_routes(c)
            self.app.include_router(c.router)
        self.sv.handle_routes()
