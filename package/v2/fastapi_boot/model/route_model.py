import inspect
from pydantic import BaseModel, Field
from enum import Enum
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    TypeAlias,
    TypeVar,
    Union,
)
from fastapi import Response
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from pydantic import BaseModel, Field, validator


class Symbol(BaseModel):
    """
    - 路由的唯一标识
    """

    file_path: Annotated[str, Field(description="文件在系统的的绝对路径")]
    context_path: Annotated[str, Field(description="该对象的上下文路径")]

    def equals(self, other: "Symbol") -> bool:
        """
        - 判断两个Symbol实例是否相等，即对应的两个路由是否路径是否相同
        """
        return (
            self.file_path == other.file_path
            and self.context_path == other.context_path
        )

    def contains(self, other: "Symbol") -> bool:
        """
        - 判断是否是other的后代路由
        - 不能直接用in，example: a.b1  a.b
        """
        contain=[1 for i,j in zip(self.context_path.split('.'), other.context_path.split('.')) if i==j]
        return (
            self.file_path == other.file_path
            and len(contain)==len(other.context_path.split('.'))
        )

    def is_child(self, other: "Symbol") -> bool:
        """
        - 判断是否是other的子路由
        """
        return (
            self.contains(other)
            and not self.equals(other)
            and len(self.context_path.split(".")) - 1
            == len(other.context_path.split("."))
        )

    @staticmethod
    def from_obj(obj: Union[Type, Callable]) -> "Symbol":
        """根据类/类的方法获取唯一symbol

        Args:
            obj (Callable): 要获取路径信息的对象（这里是类或函数）

        Returns:
            Symbol: symbol类实例，{文件绝对路径, 该对象在文件的引用路径}
        """
        file_path = inspect.getfile(obj)
        file_path = file_path[0].upper() + file_path[1:]
        context_path = obj.__qualname__
        return Symbol(file_path=file_path, context_path=context_path)

    @property
    def pos(self) -> str:
        return f"{self.file_path}  {self.context_path}"

    @staticmethod
    def fake_symbol():
        return Symbol(file_path="", context_path="")


# region rote_record
T = TypeVar("T")


class RouteRecordItemParams(BaseModel):
    """
    - 装饰器参数，除methods外等同于fastapi.APIRouter().router()的参数
    """

    response_model: Annotated[Optional[Any], Field(description="响应类型")] = None
    status_code: Annotated[Optional[int], Field(description="响应状态码")] = None
    tags: Annotated[
        Optional[List[Union[str, Enum]]], Field(description="路由标签，自定义")
    ] = None
    # pydantic没有Depends的验证器，需要自定义验证器
    dependencies: Annotated[Optional[Sequence[Any]], Field(description="依赖")] = None
    summary: Annotated[Optional[str], Field(description="路由概要，自定义")] = None
    description: Annotated[Optional[str], Field(description="路由描述，自定义")] = None
    response_description: Annotated[str, Field(description="响应结果描述")] = (
        "Successful Response"
    )
    responses: Annotated[
        Optional[Dict[Union[int, str], Dict[str, Any]]], Field(description="响应")
    ] = None
    deprecated: Annotated[Optional[bool], Field(description="是否已弃用")] = None
    operation_id: Annotated[Optional[str], Field(description="处理id")] = None
    response_model_include: Annotated[
        Optional[IncEx], Field(description="包括的响应类型")
    ] = None
    response_model_exclude: Annotated[
        Optional[IncEx], Field(description="排除的响应类型")
    ] = None
    response_model_by_alias: Annotated[bool, Field(description="别名响应类型")] = True
    response_model_exclude_unset: Annotated[
        bool, Field(description="是否排除非默认响应类型")
    ] = False
    response_model_exclude_defaults: Annotated[
        bool, Field(description="是否排除默认响应类型")
    ] = False
    response_model_exclude_none: Annotated[
        bool, Field(description="是否排除空的响应类型")
    ] = False
    include_in_schema: Annotated[bool, Field(description="")] = True
    response_class: Annotated[
        Union[Type[Response], Any], Field(description="返回响应的类型")
    ] = Default(JSONResponse)
    name: Annotated[Optional[str], Field(description="名")] = None
    openapi_extra: Annotated[Optional[Dict[str, Any]], Field(description="")] = None
    # Callable[[APIRoute], str]
    generate_unique_id_function: Annotated[
        Any, Field(description="路由处理函数唯一id的生成函数")
    ] = Default(generate_unique_id)

    @validator("dependencies")
    def dependencies_validator(cls, v):
        if v is None:
            return v
        if isinstance(v, Sequence) and isinstance(v[0], Depends):
            return v
        raise ValueError("依赖参数错误")

    @validator("response_class")
    def response_class_validator(cls, v):
        if v is None:
            return v
        if (v == Type[Response]) or isinstance(v, DefaultPlaceholder):
            return v
        raise ValueError("响应类型错误")


class RouteRecordItem(BaseModel):
    """单个路由记录的类型
    - 结构
        - symbol: Symbol 唯一标识
            - 所在模块在系统的绝对路径
            - 所在处理函数的上下文路径
        - path: str 路由路径
        - endpoint_name: str 处理函数名
        - route_params: RouteStatus 路由状态
        - endpoint: Optional[Callable] 路由处理函数名
        - params: optional[RouteRecordItemParams] 路由参数
    """

    symbol: Annotated[Symbol, Field(description="该路径的唯一标识")]
    path: Annotated[str, Field(description="路径，随着匹配逐渐增长")] = ""
    methods: Annotated[List[str], Field(description="请求方法")]
    endpoint_name: Annotated[str, Field(description="路由处理函数名")] = ""

    endpoint: Annotated[Optional[Callable], Field(description="路由处理函数")] = None
    params: Annotated[
        Optional[RouteRecordItemParams], Field(description="装饰器中的路由参数")
    ] = None


# endregion


RouteTypeLiteral: TypeAlias = Literal["CBV", "FBV", "ENDPOINT", "INNER_CBV"]
