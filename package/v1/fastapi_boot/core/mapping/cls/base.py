from enum import Enum
from functools import wraps
import inspect
from typing import Any, Callable, Dict, Final, List, Optional, Sequence, Type, Union
from fastapi import Response, routing
from fastapi.params import Depends
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.responses import JSONResponse
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from fastapi_boot.core.var.common import CommonVar

from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.enums.route import RouteStatus, RouteType
from fastapi_boot.model.routes.route_record import RouteRecordItem
from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.routes.route_record import RouteRecordItem, RouteRecordItemParams
from fastapi_boot.utils.judger import is_top_level
from fastapi_boot.utils.transformer import trans_cls_deps, trans_endpoint, trans_methods, trans_path
from fastapi_boot.utils.validator import validate_request_mapping
from ..match_route import match_route


class RequestMapping:
    """
        - 装饰类时除了path、tags、description、summary的其它参数会被忽略
        - 装饰函数时等同于fastapi.APIRouter().route()的参数

        ## Example
        ```python
        from typing import Annotated
        from pydantic import BaseModel, Field
        from pyspring import Controller,RequestMapping,GetMapping

        # 当然，User最好定义在另一个模块中，这里再导入
        class User(BaseModel):
            id: Annotated[str, Field(description='用户id')]
            username: Annotated[str, Field(max_length=30, description='用户名')]
            password: Annotated[str, Field(
                regex='^[a-zA-Z_@#$][a-zA-Z0-9@#$]{7,17}$', description='用户密码')]
            age: Annotated[int, Field(ge=0, le=200, description='用户年龄')]

        @Controller
        @RequestMapping(path = '/', tags = ['用户相关控制器'])
        class UserController:
            @GetMapping(path = '/{id}', description = '获取用户id', status_code = 200, response_model = User)
            def get_user_by_id(self, id: Path(...,description='用户id')):
                ...
        ```
    """

    _type: Final[str] = 'RequestMapping'

    def __init__(
        self,
        path: str = '',
        response_model: Any = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: List[RequestMethodEnum | str] = [
            RequestMethodEnum.GET],
        operation_id: Optional[str] = None,
        response_model_include: Optional[IncEx] = None,
        response_model_exclude: Optional[IncEx] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(
            JSONResponse
        ),
        name: Optional[str] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(
            generate_unique_id
        )
    ):
        self.path= trans_path(path)
        self.response_model= response_model
        self.status_code = status_code
        self.tags = tags
        self.dependencies = dependencies
        self.summary = summary
        self.description = description
        self.response_description = response_description
        self.deprecated = deprecated
        self.methods = methods
        self.responses = responses
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

    def __call__(self, obj: Callable):
        symbol = Symbol.from_obj(obj)
        __methods = trans_methods(self.methods)
        validate_request_mapping(__methods, symbol)

        # 声明式，没有手动调用过程
        # wraps包起来，不影响原函数名
        @wraps(obj)
        def effect(*args, **kwargs): ...
        # 设置original_obj为被装饰的类/函数
        setattr(effect, CommonVar.ORI_OBJ, obj)
        setattr(obj, CommonVar.DEC_OBJ, effect)
        # 如果是类
        if inspect.isclass(obj):
            # 判断是否是模块顶级
            setattr(obj, CommonVar.ROUTE_TYPE, RouteType.CBV if is_top_level(
                obj) else RouteType.INNER_CBV)
            # 处理depends
            trans_cls_deps(obj)
            for v in obj.__dict__.values():
                # v是被装饰的方法，o是原来的方法
                if hasattr(v, CommonVar.ORI_OBJ) and (o := getattr(v, CommonVar.ORI_OBJ)) and getattr(o, CommonVar.ROUTE_TYPE, None) == RouteType.ENDPOINT:
                    trans_endpoint(o, obj)  # 修改原方法的self
            # 匹配路由
            match_route(2,RouteRecordItem(
                    symbol=symbol, path=self.path, methods=[], endpoint_name=obj.__name__))
        # 如果是函数，说明这条路径到终点了
        elif inspect.isfunction(obj):
            setattr(obj, CommonVar.ROUTE_TYPE, RouteType.FBV if is_top_level(
                obj) else RouteType.ENDPOINT)
            # 插入最终路由，扫描时不激活，启动时才激活
            item = RouteRecordItem(
                symbol=symbol,
                path=self.path,
                methods=__methods,
                endpoint_name=obj.__name__,
                endpoint=obj,
                route_status=RouteStatus.UN_CONTROLLED,
                params=RouteRecordItemParams(
                    response_model=self.response_model,
                    status_code=self.status_code,
                    tags=self.tags,
                    dependencies=self.dependencies,
                    summary=self.summary,
                    description=self.description,
                    response_description=self.response_description,
                    deprecated=self.deprecated,
                    responses=self.responses,
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
                    generate_unique_id_function=self.generate_unique_id_function
                )
            )
            match_route(2,item)
        return effect
