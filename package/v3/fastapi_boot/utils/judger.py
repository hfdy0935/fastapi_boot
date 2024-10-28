from collections.abc import Callable
from copy import deepcopy
import inspect
from pathlib import Path
import typing


def is_top_level(obj: Callable) -> bool:
    """是否在顶层"""
    return len(obj.__qualname__.split(".")) == 1


def is_parent(path1: str, path2: str) -> bool:
    """判断path1是否是path2的父级元素"""
    return Path(path2).parent == Path(path1)


def is_ancestor(path1: str, path2: str) -> bool:
    """判断path1是否是path2的祖先目录"""
    p1 = Path(path1)
    p2 = Path(path2)
    # 找到头时p2.parent=p2
    while p2.parent != p2:
        p2 = p2.parent
        if p2 == p1:
            return True
    return False


def is_forward_ref(tp: type) -> bool:
    """判断是不是typing.ForwardRef类型"""
    return isinstance(tp, typing.ForwardRef)
