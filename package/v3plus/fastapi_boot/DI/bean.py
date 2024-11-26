import inspect
from collections.abc import Callable
from typing import TypeVar, no_type_check, overload

from fastapi_boot.store import NamedDepRecord, TypeDepRecord, app_store, dep_store
from fastapi_boot.util import get_call_filename

from .util import inject_params_deps

T = TypeVar('T')


def collect_bean(inject_timeout: float, func: Callable, name: str | None = None):
    """
    1. run function decorated by Bean decorator
    2. add the result to deps_store

    Args:
        inject_timeout (float)
        func (Callable): func
        name (str | None, optional): name of dep
    """
    params: list[inspect.Parameter] = list(inspect.signature(func).parameters.values())
    return_annotations = inspect.signature(func).return_annotation

    inject_params_res = inject_params_deps(inject_timeout, params)
    instance = func(**inject_params_res)
    tp = return_annotations if return_annotations != inspect._empty else type(instance)
    if name is None:
        dep_store.add_dep_by_type(TypeDepRecord(tp, instance))
    else:
        dep_store.add_dep_by_name(NamedDepRecord(tp, instance, name))


@overload
def Bean(value: str): ...
@overload
def Bean(value: Callable[..., T]): ...


@no_type_check
def Bean(value: str | Callable[..., T]) -> Callable[..., T]:
    """A decorator, will collect the return value of the func decorated by Bean
    # Example
    1. collect by `type`
    ```python
    @dataclass
    class Foo:
        bar: str

    @Bean
    def _():
        return Foo('baz')
    ```

    2. collect by `name`
    ```python
    class User(BaseModel):
        name: str = Field(max_length=20)
        age: int = Field(gt=0)

    @Bean('user1')
    def _():
        return User(name='zs', age=20)

    @Bean('user2)
    def _():
        return User(name='zs', age=21)
    ```
    """
    inject_timeout = app_store.get(get_call_filename()).inject_timeout

    if callable(value):
        collect_bean(inject_timeout, value)
        return value
    else:

        def wrapper(func: Callable[..., T]) -> Callable[..., T]:
            collect_bean(inject_timeout, func, value)
            return func

        return wrapper
