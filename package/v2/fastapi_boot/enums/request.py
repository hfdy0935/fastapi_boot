from enum import Enum
from typing import Optional


class RequestMethodEnum(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    HEAD = 'HEAD'
    PATCH = 'PATCH'
    TRACE = 'TRACE'
    WEBSOCKET = 'WEBSOCKET'

    @staticmethod
    def get_enum_by_str(method: str) -> Optional['RequestMethodEnum']:
        return RequestMethodEnum.__dict__.get('_member_map_', {}).get(method.upper())

    @staticmethod
    def get_str_by_enum(method: 'RequestMethodEnum') -> Optional[str]:
        return method.value
    
    @staticmethod
    def get_strs():
        return list(RequestMethodEnum.__dict__.get('_member_map_', {}).keys())

    @staticmethod
    def get_enums():
        return list(RequestMethodEnum.__dict__.get('_member_map_', {}).values())

