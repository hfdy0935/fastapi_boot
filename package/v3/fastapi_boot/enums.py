from enum import Enum
from typing import Literal, TypeAlias


class InjectType(Enum):
    """依赖注入方式"""

    TYPE = "type"  # 按类型
    NAME = "name"  # 按依赖名
    NAME_OF_TYPE = "name of type"  # 按类型名


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
        return k.upper() in list(RequestMethodEnum.__dict__.get("_member_map_", {}).keys())


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
