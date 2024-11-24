from typing import Generic, TypeVar

from fastapi_boot.vars import dep_store

T = TypeVar('T')


def inject(tp: type[T], name: str | None) -> T:
    """inject dependency by type or name

    Args:
        tp (type[T])
        name (str | None)

    Returns:
        T: instance
    """
    return dep_store.inject_by_type(tp) if name is None else dep_store.inject_by_name(name, tp)


class AtUsable(type):
    """support @"""

    def __matmul__(self: type['Inject'], other: type[T]) -> T:
        return inject(other, self.name)

    def __rmatmul__(self: type['Inject'], other: type[T]) -> T:
        return inject(other, self.name)


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

    name: str | None = None

    def __new__(cls, tp: type[T], name: str | None = None) -> T:
        """Inject(Type, name = None)"""
        cls.name = name
        return inject(tp, name)

    @classmethod
    def Qualifier(cls, name: str) -> type['Inject']:
        """Inject.Qualifier(name)"""
        _name = name

        class Cls(cls):
            name = _name

        return Cls
