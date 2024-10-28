from enum import Enum
from typing import Literal, TypeAlias


ControllerType: TypeAlias = Literal["CBV", "FBV"]


class RouteType(Enum):
    """路由类型"""

    CBV = "CBV"
    FBV = "FBV"
    ENDPOINT = "ENDPOINT"


class InjectType(Enum):
    """注入方式"""

    TYPE = "type"  # 按类型
    NAME = "name"  # 按依赖名
    NAME_OF_TYPE = "name of type"  # 按类型名
