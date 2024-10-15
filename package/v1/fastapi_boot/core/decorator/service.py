from inspect import isclass
from typing import Type, TypeVar, Union, no_type_check

from fastapi_boot.core.helper.wired_bean import wired_bean
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.bean import BeanType
from fastapi_boot.utils.generator import get_stack_path
from fastapi_boot.utils.validator import validate_service


T = TypeVar('T')


@no_type_check
def Service(name: Union[str, Type[T]]) -> T:
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
    if isclass(name):
        validate_service(name)

        def task():
            wired_bean(cls=name, name=name.__name__, tp=BeanType.SERVICE, annotations={},
                       add_bean_method=CommonVar.get_application(path).get_sv().add_service)
        if CommonVar.get_application(path):
            task()
        else:
            CommonVar.add_todo_list_by_task_pos(path, task)
        return name
    assert isinstance(name, str), 'Type of name must be str'

    def wrapper(obj: Type[T]):
        validate_service(obj)

        def task():
            wired_bean(cls=obj, name=name, tp=BeanType.SERVICE, annotations={},
                       add_bean_method=CommonVar.get_application(path).get_sv().add_service)
        if CommonVar.get_application(path):
            task()
        else:
            CommonVar.add_todo_list_by_task_pos(path, task)
        return obj
    return wrapper
