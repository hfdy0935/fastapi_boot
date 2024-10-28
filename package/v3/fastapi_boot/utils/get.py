import inspect
import os
from pathlib import Path
import typing
from fastapi_boot.core.var.constants import PROJ_SYS_PATH


def get_dirname(path: str) -> str:
    """
    根据系统路径名/文件名获取路径名
    """
    if os.path.isfile(path):
        return os.path.join(*Path(path).parts[:-1])
    else:
        return path


def get_dot_path(path: str):
    """获取文件（有后缀.py）相对于项目根目录的点路径"""
    # 删除开头的/和末尾的.py
    target = path.replace(PROJ_SYS_PATH, "")[1:-3]
    return ".".join(Path(target).parts)


def get_stack_path(n: int) -> str:
    """Gets the path to the file called in the call stack

    Args:
        n (int): Index in the stack to find

    Returns:
        str: result
    """
    # n + 1, Considering that this function occupies one position
    caller_frame = inspect.stack()[n + 1]
    name = caller_frame.frame.f_code.co_filename
    return name[0].upper() + name[1:]


def get_forward_ref_args(tp: typing.ForwardRef) -> str:
    """取出ForwardRef中的类型字符串"""
    return tp.__forward_arg__
