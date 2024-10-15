

from typing import Callable


def is_top_level(obj: Callable) -> bool:
    """whether the object is a top-level object in the module.

    Args:
        obj (Callable)

    Returns:
        bool
    """
    return len(obj.__qualname__.split('.')) == 1
