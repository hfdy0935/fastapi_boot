from collections.abc import Callable
from typing import TypeVar, no_type_check

from fastapi import APIRouter, Depends
from fastapi_boot.constants import ControllerRoutePlaceholderContainer, REQ_DEP_PLACEHOLDER


T = TypeVar("T")


def usedep(dependency: Callable[..., T] | None, use_cache: bool = True) -> T:
    """公共请求依赖，参数同FastAPI的Depends

    Args:
        dependency (Callable[..., T] | None): 依赖，函数或类
        use_cache (bool, optional): 是否使用缓存. Defaults to True.

    Returns:
        T: 依赖执行结果
    """
    value: T = Depends(dependency=dependency, use_cache=use_cache)
    setattr(value, REQ_DEP_PLACEHOLDER, True)
    return value


@no_type_check
def use_router(*path: str) -> APIRouter:
    """提取路由，可用于微服务中挂载其他应用的路由

    Returns:
        APIRouter: 直接返回占位符，等扫描时替换为APIRouter
    """
    return ControllerRoutePlaceholderContainer(list(path))
