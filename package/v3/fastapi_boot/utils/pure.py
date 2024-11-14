import inspect
from fastapi_boot.constants import PATH_METHOD_CONNECTOR


def get_stack_path(n: int) -> str:
    """获取调用栈文件系统路径"""
    # n + 1
    filename = inspect.stack()[n + 1].filename
    return filename[0].upper() + filename[1:]


def trans_path(path: str) -> str:
    """转换请求路径
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res = '/' + path.lstrip('/')
    res = res.rstrip('/')
    return '' if res == '/' else res


def join_path_method_as_rpc_sign(path:str,method:str)->str:
    """连接endpoint在Controller中的path和method"""
    return path+PATH_METHOD_CONNECTOR+method