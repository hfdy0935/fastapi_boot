from enum import Enum
from typing import Literal, TypeAlias


class RequestMethodEnum(Enum):
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
    'get',
    'GET',
    'post',
    'POST',
    'put',
    'PUT',
    'delete',
    'DELETE',
    'connect',
    'CONNECT',
    'head',
    'HEAD',
    'options',
    'OPTIONS',
    'trace',
    'TRACE',
    'patch',
    'PATCH',
    'websocket',
    'WEBSOCKET',
]
