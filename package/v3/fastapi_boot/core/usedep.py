from collections.abc import Callable
from typing import TypeVar

from fastapi import Depends
from fastapi_boot.constants import DEP_PLACEHOLDER, DepsPlaceholder


T = TypeVar("T")


def usedep(dependency: Callable[..., T] | None, use_cache: bool = True) -> T:
    """公共请求依赖参数"""
    value: T = Depends(dependency=dependency, use_cache=use_cache)
    setattr(value, DEP_PLACEHOLDER, DepsPlaceholder)
    return value
