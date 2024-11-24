from inspect import isclass
from typing import TypeVar, no_type_check, overload

from fastapi_boot.util import inject_dependency_init_deps
from fastapi_boot.vars import NamedDepRecord, TypeDepRecord, dep_store


T = TypeVar('T')


def collect_dep(cls: type, name: str | None = None):
    """init class decorated by Inject decorator and collect it's instance as dependency 
    """
    cls.__init__.__globals__[
        cls.__name__] = cls  # avoid error when getting cls in __init__ method
    instance = inject_dependency_init_deps(cls)
    if name is None:
        dep_store.add_dep_by_type(TypeDepRecord(cls, instance))
    else:
        dep_store.add_dep_by_name(
            NamedDepRecord(cls, instance, name))


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
    if isclass(value):
        collect_dep(value)
        return value
    else:
        def wrapper(cls: type[T]):
            collect_dep(cls=cls, name=value)
            return cls
        return wrapper
