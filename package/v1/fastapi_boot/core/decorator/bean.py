from typing import Any, Callable, TypeVar, Union
from inspect import isfunction

from fastapi_boot.core.helper.wired_bean import wired_bean
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.bean import BeanType
from fastapi_boot.utils.generator import get_stack_path
from fastapi_boot.utils.validator import validate_bean

T = TypeVar('T')


def Bean(name: Union[str, Callable[..., T]]) -> Union[Callable[..., T], Callable[..., Callable[..., T]]]:
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
    if isfunction(name):
        validate_bean(name)
        def task():  
            wired_bean(cls=name, name=name.__name__, tp=BeanType.BEAN, annotations=name.__annotations__,
                                add_bean_method=CommonVar.get_application(path).get_sv().add_bean)
        if CommonVar.get_application(path):
            task()
        else:
            CommonVar.add_todo_list_by_task_pos(path, task)
        return name

    assert isinstance(name, str)

    def wrapper(obj: Callable[..., T]):
        validate_bean(obj)

        def task(): 
            wired_bean(cls=obj, name=name, tp=BeanType.BEAN, annotations=obj.__annotations__,
                               add_bean_method=CommonVar.get_application(path).get_sv().add_bean)
        if CommonVar.get_application(path):
            task()
        else:
            CommonVar.add_todo_list_by_task_pos(path, task)
        return obj
    return wrapper
