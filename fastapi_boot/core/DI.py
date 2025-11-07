from collections.abc import Callable
from inspect import Parameter, _empty, signature, isclass
from typing import Annotated, TypeVar, cast, get_args, get_origin, no_type_check, overload

from .const import dep_store
from .model import DependencyNotFoundException, InjectFailException
from .util import get_call_filename

T = TypeVar('T')


def _inject(tp: type[T], name: str | None) -> T:
    """inject instance by type or name

    Args:
        tp (type[T])
        name (str | None)

    Returns:
        T: instance
    """
    if res := dep_store.inject_dep(tp, name):
        return res
    name_info = f"with name '{name}'" if name is not None else ''
    raise DependencyNotFoundException(
        f"依赖 {tp} {name_info} 未找到")


def inject_params_deps(params: list[Parameter]):
    """解析参数，注入依赖
    Args:
        params (list[Parameter]): 参数列表
    """
    params_dict = {}
    for param in params:
        # 1. with default
        if param.default != _empty:
            params_dict.update({param.name: param.default})
        else:
            # 2. no default
            if param.annotation == _empty:
                # 2.1 no annotation
                raise InjectFailException(
                    f'The annotation of param {param.name} is missing, add an annotation or give it a default value'
                )
            # 2.2. with annotation
            if get_origin(param.annotation) == Annotated:
                # 2.2.1 with Annotated
                tp, name, *_ = get_args(param.annotation)
                params_dict.update({param.name: _inject(tp, name)})
            else:
                # 2.2.2 others
                params_dict.update({param.name: _inject(
                    param.annotation, None)})
    return params_dict


# ------------------------------------------------------- Bean ------------------------------------------------------- #


def collect_bean(func: Callable, name: str | None = None):
    """
    1. run function decorated by Bean decorator
    2. add the result to deps_store

    Args:
        func (Callable): func
        name (str | None, optional): name of dep
    """
    params = list(signature(func).parameters.values())
    return_annotations = signature(func).return_annotation
    instance = func(**inject_params_deps(params))
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

    @Bean('user')
    def _():
        return User(name='zs', age=20)

    @Bean('user2)
    def _():
        return User(name='zs', age=21)
    ```
    """

    if callable(func_or_name):
        collect_bean(func_or_name)
        return func_or_name
    else:
        def wrapper(func: Callable[..., T]):
            collect_bean(func, func_or_name)
            return func
        return wrapper


# ---------------------------------------------------- Injectable ---------------------------------------------------- #
def inject_init_deps_and_get_instance(cls: type[T]) -> T:
    """_inject cls's __init__ params and get params deps"""
    old_params = list(signature(cls.__init__).parameters.values())[1:]  # self
    new_params = [
        i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]  # *args、**kwargs
    return cls(**inject_params_deps(new_params))


def collect_dep(cls: type, name: str | None = None):
    """init class decorated by Inject decorator and collect it's instance as dependency"""
    if hasattr(cls.__init__, '__globals__'):
        cls.__init__.__globals__[cls.__name__] = cls  # type: ignore
    instance = inject_init_deps_and_get_instance(cls)
    dep_store.add_dep(cls, name, instance)


@overload
def Injectable(class_or_name: str) -> Callable[[type[T]], type[T]]: ...


@overload
def Injectable(class_or_name: type[T]) -> type[T]: ...


def Injectable(class_or_name: str | type[T]):
    """decorate a class and collect it's instance as a dependency
    # Example
    ```python
    @Injectable
    class Foo:...

    @Injectable('bar1')
    class Bar:...
    ```

    """
    if isclass(class_or_name):
        collect_dep(class_or_name)
        return class_or_name
    else:

        def wrapper(cls: type[T]):
            collect_dep(cls, class_or_name)
            return cls

        return cast(Callable[[type[T]], type[T]], wrapper)


# ------------------------------------------------------ Inject ------------------------------------------------------ #
class AtUsable(type):
    """support @"""

    def __matmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        return _inject(other, cast(type[Inject], self).latest_named_deps_record.get(filename))

    def __rmatmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        return _inject(other, cast(type[Inject], self).latest_named_deps_record.get(filename))


class Inject(metaclass=AtUsable):
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
        res = _inject(tp, name)
        cls.latest_named_deps_record.update({filename: None})  # set name None
        return res

    @classmethod
    def Qualifier(cls, name: str):
        """Inject.Qualifier(name)"""
        filename = get_call_filename()
        cls.latest_named_deps_record.update({filename: name})
        return cls
