from typing import Callable, Optional, TypeVar

from fastapi import Depends


T = TypeVar('T')


def GenericDepends(dependency: Optional[Callable[..., T]], use_cache: bool = True) -> T:
    """
    - 泛型依赖
    """
    return Depends(dependency=dependency, use_cache=use_cache)
