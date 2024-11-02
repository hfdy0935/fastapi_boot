import inspect


def get_stack_path(n: int) -> str:
    """获取调用栈文件系统路径"""
    # n + 1
    caller_frame = inspect.stack()[n + 1]
    name = caller_frame.frame.f_code.co_filename
    return name[0].upper() + name[1:]


def trans_path(path: str) -> str:
    """转换请求路径
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res = "/" + path.lstrip("/")
    res = res.rstrip("/")
    return "" if res == "/" else res
