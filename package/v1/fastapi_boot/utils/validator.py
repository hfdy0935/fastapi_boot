import inspect
from typing import Callable, List, Type

from fastapi_boot.enums.bean import BeanType
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.exception.bean import BeanDecoratedFunctionHasNoReturnAnnotationException, BeanUsePositionException, ComponentUsePositionException, NotSupportFunctionBeanException
from fastapi_boot.exception.route import ClassWithSpecificDecoratorException, RequestMethodNotFoundException, UnExpectedWebsocketInRequestMappingException
from fastapi_boot.model.routes.route_props import Symbol


def must_decorate_function(Raise: Type[Exception], msg: str = '', show_pos: bool = True):
    """base
    - must decorate function
    """
    def validator(validator_):
        def wrapper(obj: Callable):
            if not inspect.isfunction(obj):
                symbol = Symbol.from_obj(obj)
                raise Raise(
                    f'{msg if msg else "can only decorate funvtion"}{"，" if msg and show_pos else ...}{"position: "+symbol.pos if show_pos else ...}')
            return validator_(obj)
        return wrapper
    return validator


def must_decorate_class(msg: str = 'can only decorate class'):
    """
    - must decorate class
    """
    def validator(validator_):
        def wrapper(obj: Callable):
            if not inspect.isclass(obj):
                symbol = Symbol.from_obj(obj)
                raise NotSupportFunctionBeanException(
                    f'{msg}{"，" if msg else ...}{"position: "+symbol.pos}')
            return validator_(obj)
        return wrapper
    return validator


def must_be_top_level(obj: Callable, tp: BeanType):
    """must decorate top-level class or function
    """
    symbol = Symbol.from_obj(obj)
    if len(symbol.context_path.split('.')) != 1:
        raise ComponentUsePositionException(
            f'{tp.value}can only decorate top-level {"class or function" if tp==BeanType.CONTROLLER else "class"}, posiition: {symbol.pos}')


@must_decorate_function(ClassWithSpecificDecoratorException, 'specific mapping can only decorate function')
def validate_specific_mapping(obj: Callable):...


@must_decorate_function(BeanUsePositionException, 'Bean can only decorate function')
def validate_bean(obj: Callable):
    """vaidate obj decorated by Bean.
    - （1）must be function；
    - （2）must have return type hint；
    """
    symbol = Symbol.from_obj(obj)
    if not obj.__annotations__.get('return'):
        raise BeanDecoratedFunctionHasNoReturnAnnotationException(
            f'function decorated by Bean must have return type hint, position: "{symbol.pos}'
        )


@must_decorate_class('Component can only decorate class')
def validate_component(obj: Callable):
    """
    - must decorate top-level class of a module
    """
    must_be_top_level(obj, BeanType.COMPONENT)


def validate_controller(obj: Callable):
    """
    - must decorate top-level class of a module/function
    """
    must_be_top_level(obj, BeanType.CONTROLLER)


@must_decorate_class('Service can only decorate class')
def validate_service(obj: Callable):
    """
    - must decorate top-level class of a module
    """
    must_be_top_level(obj, BeanType.SERVICE)


@must_decorate_class('Repository can only decorate class')
def validate_repository(obj: Callable):
    """
    - must decorate top-level class of a module
    """
    must_be_top_level(obj, BeanType.REPOSITORY)

    # -------------------------------------------------- RequestMapping -------------------------------------------------- #


def validate_request_mapping(methods: List[str], symbol: Symbol):
    """validate Requestmapping
    - can't have 'websocket'

    Args:
        methods (List[str]): requestMethodList
        symbol (Symbol): id

    Raises:
        UnExpectedWebsocketInRequestMappingException: has 'websocket'
        RequestMethodNotFoundException: unknown request method
    """
    if (RequestMethodEnum.WEBSOCKET.value in methods):
        raise UnExpectedWebsocketInRequestMappingException(
            f'WebSockets cannot be written alongside other methods in the methods block, it is recommended to use the WebsocketMapping.，position: {symbol.pos}')
    ms=RequestMethodEnum.get_strs()
    for m in methods:
        if m not in ms:
            raise RequestMethodNotFoundException(
                f'unknown request method, position: {symbol.pos}')
