from typing import Callable, Optional, TypeVar

from fastapi import Depends
from fastapi_boot.core.var.common import CommonVar


T = TypeVar('T')


def useDeps(dependency: Optional[Callable[..., T]], use_cache: bool = True) -> T:
    """
    - declared as a class variable, to be public dependency of all methods in the class
    """
    value: T = Depends(dependency=dependency, use_cache=use_cache)
    setattr(value, CommonVar.DEP_PLACEHOLDER, CommonVar.DepsPlaceholder)
    return value
