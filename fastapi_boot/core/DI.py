import time
from collections.abc import Callable
from inspect import Parameter, _empty, signature, isclass
from typing import Annotated, Generic, TypeVar, cast, get_args, get_origin, no_type_check, overload

from .const import app_store, dep_store
from .model import AppRecord, DependencyNotFoundException, InjectFailException
from .util import get_call_filename

T = TypeVar('T')


# ------------------------------------------------------- public ------------------------------------------------------ #


def _inject(app_record: AppRecord, tp: type[T], name: str | None) -> T:
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
        if res := dep_store.inject_dep(tp, name):
            return res
        time.sleep(app_record.inject_retry_step)
        if time.time() - start > app_record.inject_timeout:
            name_info = f"with name '{name}'" if name is not None else ''
            raise DependencyNotFoundException(
                f"Dependency '{tp}' {name_info} not found")


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
                params_dict.update({param.name: _inject(app_record, tp, name)})
            else:
                # 2.2.2 other
                params_dict.update({param.name: _inject(
                    app_record, param.annotation, None)})
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
    dep_store.add_dep(tp, name, instance)


@overload
def Bean(func_or_name: str): ...


@overload
def Bean(func_or_name: Callable[..., T]): ...


@no_type_check
def Bean(func_or_name: str | Callable[..., T]) -> Callable[..., T]:
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
    app_record = app_store.get_or_raise(get_call_filename())

    if callable(func_or_name):
        collect_bean(app_record, func_or_name)
        return func_or_name
    else:
        def wrapper(func: Callable[..., T]):
            collect_bean(app_record, func, func_or_name)
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
        # avoid error when getting cls in __init__ method
        cls.__init__.__globals__[cls.__name__] = cls
    instance = inject_init_deps_and_get_instance(app_record, cls)
    dep_store.add_dep(cls, name, instance)


@overload
def Injectable(class_or_name: str): ...


@overload
def Injectable(class_or_name: type[T]): ...


@no_type_check
def Injectable(class_or_name: str | type[T]) -> type[T]:
    """decorate a class and collect it's instance as a dependency
    # Example
    ```python
    @Injectable
    class Foo:...

    @Injectable('bar1')
    class Bar:...
    ```

    """
    app_record = app_store.get_or_raise((get_call_filename()))
    if isclass(class_or_name):
        collect_dep(app_record, class_or_name)
        return class_or_name
    else:

        def wrapper(cls: type[T]):
            collect_dep(app_record, cls, class_or_name)
            return cls

        return wrapper


# ------------------------------------------------------ Inject ------------------------------------------------------ #
class AtUsable(type):
    """support @"""

    def __matmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        app_record = app_store.get_or_raise(filename)
        return _inject(app_record, other, cast(type[Inject], self).latest_named_deps_record.get(filename))

    def __rmatmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        app_record = app_store.get_or_raise(filename)
        return _inject(app_record, other, cast(type[Inject], self).latest_named_deps_record.get(filename))


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
        app_record = app_store.get_or_raise(filename)
        res = _inject(app_record, tp, name)
        cls.latest_named_deps_record.update({filename: None})  # set name None
        return res

    @classmethod
    def Qualifier(cls, name: str):
        """Inject.Qualifier(name)"""
        filename = get_call_filename()
        cls.latest_named_deps_record.update({filename: name})
        return cls
