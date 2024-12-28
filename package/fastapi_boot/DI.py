import time
from collections.abc import Callable
from inspect import Parameter, _empty, signature,isclass
from typing import Annotated, Generic, TypeVar, get_args, get_origin, no_type_check, overload

from fastapi_boot.const import  app_store, dep_store
from fastapi_boot.model import AppRecord, DependencyNotFoundException, InjectFailException
from fastapi_boot.util import get_call_filename

T = TypeVar('T')

# ------------------------------------------------------- public ------------------------------------------------------ #


def _inject(app_record: AppRecord, tp: type[T], name: str | None = None) -> T:
    """inject dependency by type or name

    Args:
        app_record (AppRecord)
        tp (type[T])
        name (str | None)

    Returns:
        T: instance
    """
    start = time.time()
    while True:
        if res := dep_store.inject_by_type(tp) if name is None else dep_store.inject_by_name(name, tp):
            return res
        time.sleep(app_record.inject_retry_step)
        if time.time() - start > app_record.inject_timeout:
            name_info=f"with name '{name}'" if name is not None else ''
            raise DependencyNotFoundException(f"Dependency '{tp}' {name_info} not found")


def inject_params_deps(app_record: AppRecord, params: list[Parameter]):
    """find dependencies of params
    Args:
        app_record (AppRecord)
        params (list[Parameter]): param list without self
    """
    params_dict = {}
    for param in params:
        # 1. with default
        if param.default != _empty:
            params_dict.update({param.name: param.default})
        else:
            # 2. no default
            if param.annotation == _empty:
                # 2.1 not annotation
                raise InjectFailException(
                    f'The annotation of param {param.name} is missing, add an annotation or give it a default value'
                )
            # 2.2. with annotation
            if get_origin(param.annotation) == Annotated:
                # 2.2.1 Annotated
                tp, name, *_ = get_args(param.annotation)
                if isinstance(name, str):
                    # 2.2.1.1 name is str, as dependency's name to _inject
                    params_dict.update({param.name: _inject(app_record, tp, name)})
                else:
                    # 2.2.1.2 name is not str
                    params_dict.update({param.name: _inject(app_record, tp)})
            else:
                # 2.2.2 other
                params_dict.update({param.name: _inject(app_record, param.annotation)})
    return params_dict


# ------------------------------------------------------- Bean ------------------------------------------------------- #


def collect_bean(app_record: AppRecord, func: Callable, name: str | None = None):
    """
    1. run function decorated by Bean decorator
    2. add the result to deps_store

    Args:
        app_record (AppRecord)
        func (Callable): func
        name (str | None, optional): name of dep
    """
    params: list[Parameter] = list(signature(func).parameters.values())
    return_annotations = signature(func).return_annotation
    instance = func(**inject_params_deps(app_record, params))
    tp = return_annotations if return_annotations != _empty else type(instance)
    if name is None:
        dep_store.add_dep_by_type(tp,instance)
    else:
        dep_store.add_dep_by_name(name,tp, instance)


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
    app_record = app_store.get(get_call_filename())

    if callable(value):
        collect_bean(app_record, value)
        return value
    else:

        def wrapper(func: Callable[..., T]) -> Callable[..., T]:
            collect_bean(app_record, func, value)
            return func

        return wrapper


# ---------------------------------------------------- Injectable ---------------------------------------------------- #
def inject_init_deps_and_get_instance(app_record: AppRecord, cls: type[T]) -> T:
    """_inject cls's __init__ params and get params deps"""
    old_params = list(signature(cls.__init__).parameters.values())[1:]  # self
    new_params = [
        i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]  # *args、**kwargs
    return cls(**inject_params_deps(app_record, new_params))


def collect_dep(app_record: AppRecord, cls: type, name: str | None = None):
    """init class decorated by Inject decorator and collect it's instance as dependency"""
    if hasattr(cls.__init__, '__globals__'):
        cls.__init__.__globals__[cls.__name__] = cls  # avoid error when getting cls in __init__ method
    instance = inject_init_deps_and_get_instance(app_record, cls)
    if name is None:
        dep_store.add_dep_by_type(cls, instance)
    else:
        dep_store.add_dep_by_name(name,cls, instance)


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


# ------------------------------------------------------ Inject ------------------------------------------------------ #
class AtUsable(type):
    """support @"""

    def __matmul__(self: type['Inject'], other: type[T]) -> T:
        filename = get_call_filename()
        app_record = app_store.get(filename)
        return _inject(app_record, other, self.latest_named_deps_record.get(filename))

    def __rmatmul__(self: type['Inject'], other: type[T]) -> T:
        filename = get_call_filename()
        app_record = app_store.get(filename)
        return _inject(app_record, other, self.latest_named_deps_record.get(filename))


class Inject(Generic[T], metaclass=AtUsable):
    """inject dependency anywhere
    # Example
    - inject by **type**
    ```python
    a = Inject(Foo)
    b = Inject @ Foo
    c = Foo @ Inject

    @Injectable
    class Bar:
        a = Inject(Foo)
        b = Inject @ Foo
        c = Foo @ Inject

        def __init__(self,ia: Foo, ic: Foo):
            self.ia = ia
            self.ib = Inject @ Foo
            self.ic = ic
    ```

    - inject by **name**
    ```python
    a = Inject(Foo, 'foo1')
    b = Inject.Qualifier('foo2') @ Foo
    c = Foo @ Inject.Qualifier('foo3')

    @Injectable
    class Bar:
        a = Inject(Foo, 'foo1')
        b = Inject.Qualifier('foo2') @ Foo
        c = Foo @ Inject.Qualifier('foo3')

        def __init__(self,ia: Annotated[Foo, 'foo1'], ic: Annotated[Foo, 'foo3']):
            self.ia = ia
            self.ib = Inject.Qualifier('foo2') @ Foo
            self.ic = ic
    ```
    """

    latest_named_deps_record: dict[str, str | None] = {}

    def __new__(cls, tp: type[T], name: str | None = None) -> T:
        """Inject(Type, name = None)"""
        filename = get_call_filename()
        cls.latest_named_deps_record.update({filename: name})
        app_record = app_store.get(filename)
        res = _inject(app_record, tp, name)
        cls.latest_named_deps_record.update({filename: None})  # set name None
        return res

    @classmethod
    def Qualifier(cls, name: str) -> type['Inject']:
        """Inject.Qualifier(name)"""
        filename = get_call_filename()

        class Cls(cls):
            latest_named_deps_record: dict[str, str] = {filename: name}

        return Cls
