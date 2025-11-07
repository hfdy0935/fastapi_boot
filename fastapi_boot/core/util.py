import inspect


def get_call_filename(layer: int = 1):
    """获取本函数调用栈中第layer+1层所在的文件名

    Args:
        layer (int, optional): 调用层级. Defaults to 1.

    Returns:
        _type_: 文件名
    """
    return inspect.stack()[layer + 1].filename.capitalize()
