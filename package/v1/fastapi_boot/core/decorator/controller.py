from inspect import isclass
from typing import Any, Callable, Union, TypeVar, Type, no_type_check

from fastapi_boot.core.helper.wired_bean import wired_bean
from fastapi_boot.core.mapping.func.base import RequestMapping
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.enums.bean import BeanType
from fastapi_boot.model.routes.route_record import RouteRecordItem
from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.utils.generator import get_stack_path
from fastapi_boot.utils.validator import validate_controller
from fastapi_boot.core.mapping.match_route import match_route


T = TypeVar("T")


@no_type_check
def Controller(name: Union[str, Callable[[Type[T]], Callable]]) -> T | Callable[[Any], T]:
    """Service
    ## Example
    ```python
    # 1. default, autowired by type
    @Controller
    class UserController:
        ...

    # 2. named, autowired by name
    @Controller('user_controller2')
    class UserController2:
        ...
    ```
    """
    path = get_stack_path(1)
    if callable(name):
        # @Controller without @RequestMapping
        obj = getattr(name, CommonVar.ORI_OBJ) if (
            has_mapping := hasattr(name, CommonVar.ORI_OBJ)) else name
        return handle_collect_controller(obj, has_mapping, path)
    assert isinstance(name, str), 'Type of name must be str'

    def wrapper(obj: Callable[[Type[T]], Callable]):
        cls = getattr(obj, CommonVar.ORI_OBJ) if (
            has_mapping := hasattr(obj, CommonVar.ORI_OBJ)) else obj
        return handle_collect_controller(cls, has_mapping, path)
    return wrapper


def handle_collect_controller(obj: Callable, has_mapping: bool, path: str):
    validate_controller(obj)
    if not has_mapping:
        RequestMapping(path='', methods=[] if isclass(obj) else ['GET'])(obj)

    def task():
        wired_bean(cls=obj, name=obj.__name__, tp=BeanType.CONTROLLER, annotations={},
                   add_bean_method=CommonVar.get_application(path).get_sv().add_controller)
    if CommonVar.get_application(path):
        task()
    else:
        CommonVar.add_todo_list_by_task_pos(path, task)
    return obj
