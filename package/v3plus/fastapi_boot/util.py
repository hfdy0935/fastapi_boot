import inspect
from typing import TypeVar

T = TypeVar('T')


def get_call_filename(layer: int = 1):
    """get filename of file which calls the function which calls get_call_filename"""
    filename = inspect.stack()[layer + 1].filename
    return filename[0].upper() + filename[1:]


def trans_path(path: str) -> str:
    """
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res = '/' + path.lstrip('/')
    res = res.rstrip('/')
    return '' if res == '/' else res
