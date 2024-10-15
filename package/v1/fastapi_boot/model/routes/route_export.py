from typing import Annotated, List, Literal, TypeAlias
from pydantic import BaseModel, Field

from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.routes.route_record import RouteRecordItem

RouteTypeLiteral: TypeAlias = Literal['CBV', 'FBV', 'ENDPOINT', 'INNER_CBV']


class RouteLayerItem(BaseModel):
    full_path: Annotated[str, Field(description='累计到这的全路径')]
    path: Annotated[str, Field(description='路径')] = ''
    symbol: Annotated[Symbol, Field(
        description='路由唯一标识')]
    type: Annotated[RouteTypeLiteral,
                    Field(description='类型')]
    name: Annotated[str, Field(description='名')]
    methods: Annotated[List[str], Field(description='请求方法')]
    children: Annotated[List['RouteLayerItem'],
                        Field(description='子路由')] = []

    @staticmethod
    def partial_from_record(item: RouteRecordItem, full_path: str, type_: RouteTypeLiteral, children: List['RouteLayerItem']) -> 'RouteLayerItem':
        """
        - 从RouteRecordItem获取RouteLayerItem，还需要传额外字段
        """
        return RouteLayerItem(
            full_path=full_path,
            path=item.path,
            symbol=item.symbol,
            type=type_,
            name=item.endpoint_name,
            methods=item.methods,
            children=children
        )


class Route(RouteLayerItem, BaseModel):
    """路由信息
    """
