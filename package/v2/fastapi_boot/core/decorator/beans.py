from typing import Callable, Type, TypeVar, Union, no_type_check
from inspect import isclass, isfunction

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.enums.bean import BeanType
from fastapi_boot.model.scan_model import BeanItem
from fastapi_boot.utils.generator import get_stack_path
from fastapi_boot.utils.validator import (
    validate_bean,
    validate_component,
    validate_repository,
    validate_service,
)
from fastapi_boot.utils.add_task import handle_task

T = TypeVar("T")


def Bean(
    value: Union[str, Callable[..., T]]
) -> Union[Callable[..., T], Callable[..., Callable[..., T]]]:
    """Bean, they must have a return type.
    ## Example
    ```python
    # 1. default, autowired by type
    @Bean
    def get_user()->User:
        ...

    # 2. named, autowired by name
    @Bean('user2')
    def get_user2()->User:
        ...
    ```
    """
    path = get_stack_path(1)
    if isfunction(value):
        validate_bean(value)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_bean
            item=BeanItem(
                type=BeanType.BEAN,
                symbol=Symbol.from_obj(value),
                name=value.__name__,
                constructor=value,
                annotations=value.__annotations__,
                value=value()
            )
            method(item)
        handle_task(path,task)
        return value

    assert isinstance(value, str)

    def wrapper(obj: Callable[..., T]):
        validate_bean(obj)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_bean
            item=BeanItem(
                type=BeanType.BEAN,
                symbol=Symbol.from_obj(obj),
                name=value,
                constructor=obj,
                annotations=obj.__annotations__,
                value=obj()
            )
            method(item)
        handle_task(path,task)
        return obj
    return wrapper


@no_type_check
def Component(value: Union[str, Type[T]]) -> T:
    """Service
    ## Example
    ```python
    # 1. default, autowired by type
    @Component
    class UserComponent:
        ...

    # 2. named, autowired by name
    @Component('user_component2')
    class UserComponent2:
        ...
    ```
    """
    path = get_stack_path(1)
    if isclass(value):
        validate_component(value)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_component
            item=BeanItem(
                type=BeanType.COMPONENT,
                symbol=Symbol.from_obj(value),
                name=value.__name__,
                constructor=value,
                annotations={},
                value=value()
            )
            method(item)
        handle_task(path,task)

        return value
    assert isinstance(value, str), "value must be str"

    def wrapper(obj: Type[T]):
        validate_component(obj)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_component
            item=BeanItem(
                type=BeanType.COMPONENT,
                symbol=Symbol.from_obj(obj),
                name=value,
                constructor=obj,
                annotations={},
                value=obj()
            )
            method(item)
        handle_task(path,task)
        return obj
    return wrapper


@no_type_check
def Service(value: Union[str, Type[T]]) -> T:
    """Service
    ## Example
    ```python
    # 1. default, autowired by type
    @Service
    class UserService:
        ...

    # 2. named, autowired by name
    @Service('user_service2')
    class UserService2:
        ...
    ```
    """
    path = get_stack_path(1)
    if isclass(value):
        validate_service(value)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_service
            item=BeanItem(
                type=BeanType.SERVICE,
                symbol=Symbol.from_obj(value),
                name=value.__name__,
                constructor=value,
                annotations={},
                value=value()
            )
            method(item)
        handle_task(path,task)
        return value
    assert isinstance(value, str), "value must be str"

    def wrapper(obj: Type[T]):
        validate_service(obj)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_service
            item=BeanItem(
                type=BeanType.SERVICE,
                symbol=Symbol.from_obj(obj),
                name=value,
                constructor=obj,
                annotations={},
                value=obj()
            )
            method(item)
        handle_task(path,task)
        return obj

    return wrapper


@no_type_check
def Repository(value: Union[str, Type[T]]) -> T:
    """Service
    ## Example
    ```python
    # 1. default, autowired by type
    @Repository
    class UserRepository:
        ...

    # 2. named, autowired by name
    @Repository('user_repository2')
    class UserRepository2:
        ...
    ```
    """
    path = get_stack_path(1)
    if isclass(value):
        validate_repository(value)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_repository
            item=BeanItem(
                type=BeanType.REPOSITORY,
                symbol=Symbol.from_obj(value),
                name=value.__name__,
                constructor=value,
                annotations={},
                value=value()
            )
            method(item)
        handle_task(path,task)
        return value
    assert isinstance(value, str), "value must be str"

    def wrapper(obj: Type[T]) -> Type[T]:
        validate_repository(obj)
        def task():
            method:Callable=CommonVar.get_application(path).get_sv().add_repository
            item=BeanItem(
                type=BeanType.REPOSITORY,
                symbol=Symbol.from_obj(obj),
                name=value,
                constructor=obj,
                annotations={},
                value=obj()
            )
            method(item)
        handle_task(path,task)
        return obj

    return wrapper
