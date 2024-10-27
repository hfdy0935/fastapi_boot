from collections.abc import Callable, Sequence
from dataclasses import dataclass
import inspect
from enum import Enum
from typing import (
    Annotated,
    Any,
    Literal,
    TypeAlias,
    TypeVar,
)
from fastapi import Response
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id


@dataclass
class Symbol:
    """
    - 路由的唯一标识
    """

    file_path: Annotated[str, "文件在系统的的绝对路径"]
    context_path: Annotated[str, "该对象的上下文路径"]

    def equals(self, other: "Symbol") -> bool:
        """
        - 判断两个Symbol实例是否相等，即对应的两个路由是否路径是否相同
        """
        return self.file_path == other.file_path and self.context_path == other.context_path

    def contains(self, other: "Symbol") -> bool:
        """
        - 判断是否是other的后代路由
        - 不能直接用in，example: a.b1  a.b
        """
        contain = [1 for i, j in zip(self.context_path.split("."), other.context_path.split(".")) if i == j]
        return self.file_path == other.file_path and len(contain) == len(other.context_path.split("."))

    def is_child(self, other: "Symbol") -> bool:
        """
        - 判断是否是other的子路由
        """
        return (
            self.contains(other)
            and not self.equals(other)
            and len(self.context_path.split(".")) - 1 == len(other.context_path.split("."))
        )

    @staticmethod
    def from_obj(obj: type | Callable) -> "Symbol":
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


class RouteRecordItemParams:
    """
    - 装饰器参数，除methods外等同于fastapi.APIRouter().router()的参数
    """

    def __init__(
        self,
        response_model: Annotated[Any, "响应类型"] = None,
        status_code: Annotated[int | None, "响应状态码"] = None,
        tags: Annotated[list[str | Enum] | None, "路由标签，自定义"] = None,
        # pydantic没有Depends的验证器，需要自定义验证器
        dependencies: Annotated[Sequence[Any] | None, "依赖"] = None,
        summary: Annotated[str | None, "路由概要，自定义"] = None,
        description: Annotated[str | None, "路由描述，自定义"] = None,
        response_description: Annotated[str, "响应结果描述"] = "Successful Response",
        responses: Annotated[dict[int | str, dict[str, Any]] | None, "响应"] = None,
        deprecated: Annotated[bool | None, "是否已弃用"] = None,
        operation_id: Annotated[str | None, "处理id"] = None,
        response_model_include: Annotated[IncEx | None, "包括的响应类型"] = None,
        response_model_exclude: Annotated[IncEx | None, "排除的响应类型"] = None,
        response_model_by_alias: Annotated[bool, "别名响应类型"] = True,
        response_model_exclude_unset: Annotated[bool, "是否排除非默认响应类型"] = False,
        response_model_exclude_defaults: Annotated[bool, "是否排除默认响应类型"] = False,
        response_model_exclude_none: Annotated[bool, "是否排除空的响应类型"] = False,
        include_in_schema: Annotated[bool, ""] = True,
        response_class: Annotated[type[Response] | Any, "返回响应的类型"] = Default(JSONResponse),
        name: Annotated[str | None, "名"] = None,
        openapi_extra: Annotated[dict[str, Any] | None, ""] = None,
        generate_unique_id_function: Annotated[Any, "路由处理函数唯一id的生成函数"] = Default(generate_unique_id),
    ):
        self.response_model = response_model
        self.status_code = status_code
        self.tags = tags
        self.dependencies = dependencies
        self.summary = summary
        self.description = description
        self.response_description = response_description
        self.responses = responses
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.response_model_include = response_model_include
        self.response_model_exclude = response_model_exclude
        self.response_model_by_alias = response_model_by_alias
        self.response_model_exclude_unset = response_model_exclude_unset
        self.response_model_exclude_defaults = response_model_exclude_defaults
        self.response_model_exclude_none = response_model_exclude_none
        self.include_in_schema = include_in_schema
        self.response_class = response_class
        self.name = name
        self.openapi_extra = openapi_extra
        self.generate_unique_id_function = generate_unique_id_function

    @property
    def dict(self):
        return dict(
            response_model=self.response_model,
            status_code=self.status_code,
            tags=self.tags,
            dependencies=self.dependencies,
            summary=self.summary,
            description=self.description,
            response_description=self.response_description,
            responses=self.responses,
            deprecated=self.deprecated,
            operation_id=self.operation_id,
            response_model_include=self.response_model_include,
            response_model_exclude=self.response_model_exclude,
            response_model_by_alias=self.response_model_by_alias,
            response_model_exclude_unset=self.response_model_exclude_unset,
            response_model_exclude_defaults=self.response_model_exclude_defaults,
            response_model_exclude_none=self.response_model_exclude_none,
            include_in_schema=self.include_in_schema,
            response_class=self.response_class,
            name=self.name,
            openapi_extra=self.openapi_extra,
            generate_unique_id_function=self.generate_unique_id_function,
        )


@dataclass
class RouteRecordItem:
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

    symbol: Annotated[Symbol, "该路径的唯一标识"]
    methods: Annotated[list[str], "请求方法"]
    path: Annotated[str, "路径，随着匹配逐渐增长"] = ""
    endpoint_name: Annotated[str, "路由处理函数名"] = ""
    endpoint: Annotated[Callable | None, "路由处理函数"] = None
    params: Annotated[RouteRecordItemParams | None, "装饰器中的路由参数"] = None


# endregion


RouteTypeLiteral: TypeAlias = Literal["CBV", "FBV", "ENDPOINT", "INNER_CBV"]
