from typing import Type, TypeVar, Union, no_type_check
from inspect import isclass

from fastapi_boot.core.helper.wired_bean import wired_bean
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.bean import BeanType
from fastapi_boot.utils.generator import get_stack_path
from fastapi_boot.utils.validator import validate_component

T = TypeVar('T')


@no_type_check
def Component(name: Union[str, Type[T]]) -> T:
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
    if isclass(name):
        validate_component(name)

        def task():
            wired_bean(cls=name, name=name.__name__, tp=BeanType.COMPONENT, annotations={},
                       add_bean_method=CommonVar.get_application(path).get_sv().add_component)
        if CommonVar.get_application(path):
            task()
        else:
            CommonVar.add_todo_list_by_task_pos(path, task)

        return name
    assert isinstance(name, str), 'Type of name must be str'

    def wrapper(obj: Type[T]):
        validate_component(obj)

        def task():
            wired_bean(cls=obj, name=name, tp=BeanType.COMPONENT, annotations={},
                       add_bean_method=CommonVar.get_application(path).get_sv().add_component)
        if CommonVar.get_application(path):
            task()
        else:
            CommonVar.add_todo_list_by_task_pos(path, task)

        return obj
    return wrapper
