from enum import Enum
from typing import Literal


class AutoWiredType(Enum):
    TYPE = 'type'
    NAME = 'name'

    def to_enum(self, name: Literal['type', 'name']) -> 'AutoWiredType':
        return AutoWiredType.TYPE if name == 'type' else AutoWiredType.NAME


class BeanType(Enum):
    BEAN = 'Bean'
    COMPONENT = 'Component'
    CONTROLLER = 'Controller'
    SERVICE = 'Service'
    REPOSITORY = 'Repository'
