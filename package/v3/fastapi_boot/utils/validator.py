from collections.abc import Callable
import inspect
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.exception.bean import (
    BeanTypeException,
    BeanUsePositionException,
    DependencyPositionException,
    DependencyTypeException,
)
from fastapi_boot.exception.route import (
    RequestMethodException,
    MappingUseTypeException,
)
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.utils.judger import is_top_level


def must_decorate_function(
    Exp: type[Exception] = DependencyTypeException,
    msg: str = DependencyTypeException.msg,
    show_pos: bool = True,
):
    """只能装饰函数"""

    def validator(validator_):
        def wrapper(obj: Callable, *args):
            if not inspect.isfunction(obj):
                symbol = Symbol.from_obj(obj)
                message = msg + f"，位置：{symbol.pos}" if show_pos else ""
                raise Exp(message)
            return validator_(obj, *args)

        return wrapper

    return validator


def must_decorate_class(
    Exp: type[Exception] = DependencyTypeException,
    msg: str = DependencyTypeException.msg,
    show_pos: bool = True,
):
    """只能装饰类"""

    def validator(validator_):
        def wrapper(obj: Callable, *args):
            if not inspect.isclass(obj):
                symbol = Symbol.from_obj(obj)
                message = msg + f"，位置：{symbol.pos}" if show_pos else ""
                raise Exp(message)
            return validator_(obj, *args)

        return wrapper

    return validator


@must_decorate_class(msg="Prefix只能装饰类")
def validate_prefix(obj: Callable): ...


@must_decorate_function(BeanUsePositionException, "Bean装饰器只能写在模块顶层函数上")
def validate_bean(obj: Callable):
    """校验Bean"""
    annotations = obj.__annotations__
    if not inspect.isclass(annotations.get("return").__class__):
        raise BeanTypeException(BeanTypeException.msg + f"，位置：{Symbol.from_obj(obj).pos}")


@must_decorate_class(msg="Inject只能装饰类")
def validate_inject(obj: Callable):
    if not is_top_level(obj):
        symbol = Symbol.from_obj(obj)
        message = "Inject只能写在模块顶层" + f"，位置：{symbol.pos}"
        raise DependencyPositionException(message)


@must_decorate_class(msg="Controller只能装饰类")
def validate_controller(obj: Callable):
    if not is_top_level(obj):
        symbol = Symbol.from_obj(obj)
        message = "Controller只能写在模块顶层" + f"，位置：{symbol.pos}"
        raise DependencyPositionException(message)


# -------------------------------------------------- 路由映射装饰器 -------------------------------------------------- #


@must_decorate_function(MappingUseTypeException, msg="具体的路由映射装饰器只能装饰函数")
def validate_specific_mapping(obj: Callable): ...


@must_decorate_function(MappingUseTypeException, msg="Req装饰只能装饰函数")
def validate_request_mapping(obj: Callable, methods: list[str], symbol: Symbol):
    """校验@Req装饰器"""
    if RequestMethodEnum.WEBSOCKET.value in methods:
        raise RequestMethodException(
            RequestMethodException.msg + f"Websocket应该用@Socket而不是@Req，位置：{symbol.pos}"
        )
    ms = RequestMethodEnum.get_strs()
    for m in methods:
        if m not in ms:
            raise RequestMethodException(
                RequestMethodException.msg + f"方法{m}不是合法的http请求方法，位置：{symbol.pos}"
            )
