from enum import Enum
from functools import wraps
import inspect
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union
from fastapi import Response, routing
from fastapi.params import Depends
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.responses import JSONResponse
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from fastapi_boot.core.var.common import CommonVar

from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.enums.route import RouteStatus, RouteType
from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.routes.route_record import RouteRecordItem, RouteRecordItemParams
from fastapi_boot.utils.judger import is_top_level
from fastapi_boot.utils.transformer import trans_cls_deps, trans_endpoint, trans_methods, trans_path
from fastapi_boot.utils.validator import validate_request_mapping
from ..match_route import match_route


def RequestMapping(
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
    """
        - 装饰类时除了path的其它参数会被忽略
        - 装饰函数时等同于fastapi.APIRouter().route()的参数

        ## Example
        ```python
        from typing import Annotated
        from pydantic import BaseModel, Field
        from fastapi_boot import Controller,RequestMapping,GetMapping

        # User better in another module, this module can import it to use
        class User(BaseModel):
            id: Annotated[str, Field(description='id')]
            username: Annotated[str, Field(max_length=30, description='username')]
            password: Annotated[str, Field(
                regex='^[a-zA-Z_@#$][a-zA-Z0-9@#$]{7,17}$', description='password')]
            age: Annotated[int, Field(ge=0, le=200, description='age')]

        @Controller
        @RequestMapping(path = '/', tags = ['userController'])
        class UserController:
            @GetMapping(path = '/{id}', description = 'get user's id', status_code = 200, response_model = User)
            def get_user_by_id(self, id: Path(...,description='id')):
                ...
        ```
    """
    _path: str = trans_path(path)

    def decorator(obj: Callable):
        symbol = Symbol.from_obj(obj)
        _methods = trans_methods(methods)
        validate_request_mapping(_methods, symbol)

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
            match_route(2,RouteRecordItem(
                    symbol=symbol, path=_path, methods=[], endpoint_name=obj.__name__))
        # 如果是函数，说明这条路径到终点了
        elif inspect.isfunction(obj):
            setattr(obj, CommonVar.ROUTE_TYPE, RouteType.FBV if is_top_level(
                obj) else RouteType.ENDPOINT)
            # 插入最终路由，扫描时不激活，启动时才激活
            item = RouteRecordItem(
                symbol=symbol,
                path=_path,
                methods=_methods,
                endpoint_name=obj.__name__,
                endpoint=obj,
                route_status=RouteStatus.UN_CONTROLLED,
                params=RouteRecordItemParams(
                    response_model=response_model,
                    status_code=status_code,
                    tags=tags,
                    dependencies=dependencies,
                    summary=summary,
                    description=description,
                    response_description=response_description,
                    deprecated=deprecated,
                    responses=responses,
                    operation_id=operation_id,
                    response_model_include=response_model_include,
                    response_model_exclude=response_model_exclude,
                    response_model_by_alias=response_model_by_alias,
                    response_model_exclude_unset=response_model_exclude_unset,
                    response_model_exclude_defaults=response_model_exclude_defaults,
                    response_model_exclude_none=response_model_exclude_none,
                    include_in_schema=include_in_schema,
                    response_class=response_class,
                    name=name,
                    openapi_extra=openapi_extra,
                    generate_unique_id_function=generate_unique_id_function
                )
            )
            match_route(2,item)
        return effect
    return decorator
