from inspect import isclass
from typing import TypeVar, no_type_check, overload

from fastapi_boot.store import NameDepRecord, TypeDepRecord, app_store, dep_store
from fastapi_boot.util import get_call_filename
from fastapi_boot.model import AppRecord

from .util import inject_init_deps_and_get_instance

T = TypeVar('T')


def collect_dep(app_record: AppRecord, cls: type, name: str | None = None):
    """init class decorated by Inject decorator and collect it's instance as dependency"""
    if hasattr(cls.__init__, '__globals__'):
        cls.__init__.__globals__[cls.__name__] = cls  # avoid error when getting cls in __init__ method
    instance = inject_init_deps_and_get_instance(app_record, cls)
    if name is None:
        dep_store.add_dep_by_type(TypeDepRecord(cls, instance))
    else:
        dep_store.add_dep_by_name(NameDepRecord(cls, instance, name))


@overload
def Injectable(value: str): ...
@overload
def Injectable(value: type[T]): ...


@no_type_check
def Injectable(value: str | type[T]) -> type[T]:
    """decorate a class and collect it's instance as a dependency
    # Example
    ```python
    @Injectable
    class Foo:...

    @Injectable('bar1')
    class Bar:...
    ```

    """
    app_record = app_store.get((get_call_filename()))
    if isclass(value):
        collect_dep(app_record, value)
        return value
    else:

        def wrapper(cls: type[T]):
            collect_dep(app_record, cls, value)
            return cls

        return wrapper
