from typing import TypeVar
from fastapi_boot.constants import CONTROLLER_ROUTE_RECORD
from fastapi_boot.model import PrefixRouteRecord
from fastapi_boot.util import trans_path

T = TypeVar('T')


def Prefix(prefix: str = ""):
    """ sub block in controller， can isolate inner deps and outer deps
    ```python
    def f1(p: str = Query()):
        return 'f1'
    def f2(q: int = Query()):
        return 'f2'

    @Controller()
    class UserController:
        p = use_dep(f1)

        @Prefix()
        class Foo:
            q = use_dep(f2)
            @Get()
            def get_user(self): # only need the query param 'q'
                return self.q
    ```
    """
    prefix = trans_path(prefix)

    def wrapper(cls: type[T]) -> type[T]:
        prefix_route_record = PrefixRouteRecord(
            cls=cls, prefix=prefix)
        setattr(cls, CONTROLLER_ROUTE_RECORD, prefix_route_record)
        return cls

    return wrapper
