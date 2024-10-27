from typing import Annotated, Any, Callable, Dict, List, Optional, Union
from fastapi import APIRouter
from pydantic import BaseModel, Field
from fastapi_boot.enums.bean import BeanType
from fastapi_boot.model.route_model import Symbol


class ModulePathItem(BaseModel):
    """项目中每个模块的路径类，包括：
    1. `mod_sys_abs_ln_path`：模块在系统中的绝对路径，以斜杠反斜杠分隔
    2. `mod_pro_abs_dot_path`：模块在项目中的绝对路径，以.分隔
    3. `mod_pro_abs_ln_path`：模块在项目中的绝对路径，以斜杠反斜杠分隔
    """

    mod_sys_abs_ln_path: Annotated[
        str, Field(description="模块在系统中的绝对路径，以斜杠反斜杠分隔")
    ]
    mod_pro_abs_dot_path: Annotated[
        str, Field(description="模块在项目中的绝对路径，以斜杠反斜杠分隔")
    ]
    mod_pro_abs_ln_path: Annotated[
        str,
        Field(
            pattern=r"^(([^\.]*)*\.)*([^\.]*)$",
            description="模块在项目中的绝对路径，以.分隔",
        ),
    ]


class Config(BaseModel):
    need_pure_api: Annotated[bool, Field(description="是否删除自带的api")] = False
    scan_timeout_second: Annotated[
        Union[int, float], Field(gt=0, description="扫描超时时间，超时未找到报错")
    ] = 10
    exclude_scan_path:Annotated[List[str],Field(description='忽略扫描的模块或包在项目中的点路径')]=[]
    include_scan_path:Annotated[List[str],Field(description='额外扫描的模块或包在项目中的点路径')]=[]


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

    type: Annotated[BeanType, Field(description="Component")]
    symbol: Annotated[Symbol, Field(description="bean的唯一标识")]
    name: Annotated[str, Field(description="名")]
    constructor: Annotated[Any, Field(description="构造器")]
    annotations: Annotated[Dict[str, Any], Field(description="构造器参数")]
    value: Annotated[Optional[Any], Field(description="bean的值")] = None


class ControllerItem:
    def __init__(self, symbol: Symbol, router: APIRouter) -> None:
        self.symbol = symbol
        self.router = router

    @property
    def dict(self) -> Dict:
        return dict(symbol=self.symbol, router=self.router)
