from enum import Enum
from typing import Literal, TypeAlias


class InjectType(Enum):
    """依赖注入方式"""

    TYPE = "type"  # 按类型
    NAME = "name"  # 按依赖名
    NAME_OF_TYPE = "name of type"  # 按类型名


class DepPos(Enum):
    """依赖所在位置"""

    NO_APP = "no_app"  # 无app模块的依赖，没找到的都分为NO_APP，后续找到可能会改
    APP = "app"  # 某个app的依赖


class DepInjectPos(Enum):
    """依赖要注入的位置
    - 控制器需要一直阻塞，等待注入
    - 其他位置的如果没找到依赖，会添加到应用或全局任务，之后再找
    """

    CONTROLLER = "controller"  # 控制器
    OTHER = "other"  # 其他


class RequestMethodEnum(Enum):
    """请求方法"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    PATCH = "PATCH"
    TRACE = "TRACE"
    WEBSOCKET = "WEBSOCKET"

    @staticmethod
    def contains(k: str):
        return k.upper() in RequestMethodEnum.__members__


RequestMethodStrEnum: TypeAlias = Literal[
    "get",
    "GET",
    "post",
    "POST",
    "put",
    "PUT",
    "delete",
    "DELETE",
    "connect",
    "CONNECT",
    "head",
    "HEAD",
    "options",
    "OPTIONS",
    "trace",
    "TRACE",
    "patch",
    "PATCH",
    "websocket",
    "WEBSOCKET",
]
