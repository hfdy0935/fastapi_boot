from typing import Annotated, Any, Dict, Optional, TypeVar
from pydantic import BaseModel, Field

from fastapi_boot.enums.bean import BeanType
from fastapi_boot.model.routes.route_props import Symbol


T = TypeVar('T')


class BeanItem(BaseModel):
    """项目中的bean实例
    - 字段：
        - type: BeanType 类型，BeanType
        - symbol: str bean的唯一标识
        - name: str 名
        - constructor: str 构造器
        - annotation: Dict[str, Any] 构造器参数
        - value: Any 值
    """
    type: Annotated[BeanType,
                    Field(description='Component')]
    symbol: Annotated[Symbol,
                      Field(description='bean的唯一标识')]
    name: Annotated[str, Field(description='名')]
    constructor: Annotated[Any, Field(description='构造器')]
    annotations: Annotated[Dict[str, Any], Field(description='构造器参数')]
    value: Annotated[Optional[Any], Field(description='bean的值')] = None
