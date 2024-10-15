from typing import Final, List, Optional, Tuple

from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.model.routes.route_export import RouteLayerItem
from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.routes.route_record import RouteRecordItem
from fastapi_boot.model.routes.route_record import SimpleRouteRecordItem
from fastapi_boot.utils.transformer import trans_route_record_item


class RoutesVar:
    """存储应用创建过程中路由相关的变量即获取方法
    """
    _id=0

    def __init__(self, scanner_var: ScannerVar, need_pure_api: bool):
        self.id=RoutesVar._id
        RoutesVar._id+=1
        # 是否使用纯api，即删除自带的路由文档路由. Defaults to False.
        self._need_pure_api: bool = need_pure_api
        self.sv = scanner_var
        # 每个路由的记录，会随着匹配叠加
        self._route_record_list: Final[List[RouteRecordItem]] = []
        # 所有路由记录，不叠加
        self._all_route_record_list: Final[List[RouteRecordItem]] = []

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

    def get_simple_route_record_list(self) -> List[SimpleRouteRecordItem]:
        """获取所有路由简单记录列表

        Returns:
            List[SimpleRouteRecordItem]: 结果
        """
        return [trans_route_record_item(i) for i in self.get_route_record_list()]

    def get_simple_route_record_list_by_symbol(self, symbol: Symbol) -> Optional[SimpleRouteRecordItem]:
        """根据symbol实例获取对应的路由简单记录列表

        Args:
            symbol (Symbol): 查询参数

        Returns:
            Optional[SimpleRouteRecordItem]: 查询结果 | None
        """
        return [trans_route_record_item(i) for i in self.get_route_record_list()][0]

    # ------------------------------------------------------ 所有路由记录 ------------------------------------------------------ #

    def get_all_route_record_list(self) -> List[RouteRecordItem]:
        return self._all_route_record_list

    def add_all_route_record_list(self, v: RouteRecordItem):
        self.get_all_route_record_list().append(v)

    # ------------------------------------------------------- 路由层级 ------------------------------------------------------- #
    def _traverse_route(self, i: RouteRecordItem, l: RouteLayerItem, prefix: str) -> Tuple[Optional[RouteLayerItem], Optional[str]]:
        """从l和l的children中遍历找到i的父级，用于生成路由层级
        """
        if i.symbol.is_child(l.symbol):
            return l, prefix+l.path+i.path
        if l.children:
            for j in l.children:
                f, fp = self._traverse_route(i, j, prefix+l.path)
                if f and fp:
                    return f, fp
        return None, None

    def get_route_layer_list(self) -> List[RouteLayerItem]:
        """获取路由层级列表

        Returns:
            List[RouteLayerItem]
        """
        res: List[RouteLayerItem] = []
        # 按照qualname从顶级向下排序，先遍历控制器
        self.get_all_route_record_list().sort(
            key=lambda i: len(i.symbol.context_path.split('.')))
        for i in self.get_all_route_record_list():
            # 有控制器
            if self.sv.is_controller(i.symbol):
                res.append(RouteLayerItem.partial_from_record(
                    item=i,
                    full_path=i.path,
                    type_='FBV' if i.methods else 'CBV',
                    children=[]
                ))
            # 没控制器
            else:
                # 只遍历控制器类和内部控制类的列表，找到i的父级路由
                temp = [j for j in res if len(j.methods) == 0]
                for t in temp:
                    k, fp = self._traverse_route(i, t, '')
                    if k and fp:
                        item = RouteLayerItem.partial_from_record(
                            item=i,
                            full_path=fp,
                            type_='ENDPOINT' if i.methods else 'INNER_CBV',
                            children=[]
                        )
                        k.children.append(item)
        return res

    def _traverse_children_route_layer(self, symbol: Symbol, l: RouteLayerItem) -> Optional[RouteLayerItem]:
        """
        - 递归找到symbol对应的路由层级
        """
        if symbol.equals(l.symbol):
            return l
        elif l.children:
            for c in l.children:
                if (r := self._traverse_children_route_layer(symbol, c)):
                    return r
        return None

    def get_route_layer_by_symbol(self, symbol: Symbol) -> Optional[RouteLayerItem]:
        """
        - 根据symbol获取路由层级信息
        """
        for i in self.get_route_layer_list():
            if (r := self._traverse_children_route_layer(symbol, i)):
                return r
        return None
