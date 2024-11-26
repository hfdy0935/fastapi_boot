from typing import Generic, TypeVar

from fastapi_boot.store import app_store,dep_store
from fastapi_boot.util import get_call_filename

from .util import inject

T = TypeVar('T')


class AtUsable(type):
    """support @"""

    def __matmul__(self: type['Inject'], other: type[T]) -> T:
        filename=get_call_filename()
        inject_timeout = app_store.get(filename).inject_timeout
        return inject(inject_timeout, other, self.latest_named_deps_record.get(filename))

    def __rmatmul__(self: type['Inject'], other: type[T]) -> T:
        filename=get_call_filename()
        inject_timeout = app_store.get(filename).inject_timeout
        return inject(inject_timeout, other, self.latest_named_deps_record.get(filename))


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
    latest_named_deps_record:dict[str,str|None]={}

    def __new__(cls, tp: type[T], name: str | None = None) -> T:
        """Inject(Type, name = None)"""
        filename=get_call_filename()
        cls.latest_named_deps_record.update({filename:name})
        inject_timeout = app_store.get(filename).inject_timeout
        res=inject(inject_timeout, tp, name)
        cls.latest_named_deps_record.update({filename:None}) # set name as None
        return res

    @classmethod
    def Qualifier(cls, name: str) -> type['Inject']:
        """Inject.Qualifier(name)"""
        filename=get_call_filename()
        class Cls(cls):
            latest_named_deps_record: dict[str, str]={filename:name}
        return Cls
