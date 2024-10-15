from concurrent.futures import ThreadPoolExecutor
import time
from typing import Callable, Optional, TypeVar, Type

from fastapi_boot.core.application.scanner import ScannerApplication
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.exception.bean import AutoWiredFailException
from fastapi_boot.utils.generator import get_stack_path

T = TypeVar('T')


def fn(method: Callable, param: Type[T] | str,timeout_second:int|float) -> T:
    res: Optional[T] = None
    start = time.time()
    while True:
        if (res := method(param)):
            break
        if time.time()-start > timeout_second:
            raise AutoWiredFailException(
                f'扫描超时，Bean {"名"+param if isinstance(param,str) else "类型"+param.__name__} 未找到')
    return res




def AutoWired(BeanType: Type[T]|Callable, name: str = '') -> T:
    """解析每个AutoWired自动装配对象，开启一个线程，在遍历项目模块过程中一直找
        1. 只传类型或类型 + 空字符串 => 按类型装配
        2. 类型 + 不为空的字符串 => 则按名装配，此时类型仅用于代码提示
        3. 一般不用装配Controller，如果要获取，用name装配；根据控制类被装饰的类型找不到原类型

        Args:
            BeanType (Type[T]): 类型
            name (str, optional): 名，Defaults to ''.

        Returns:
            T: 装配结果实例
        """
    sa:ScannerApplication = CommonVar.get_application(get_stack_path(1)).sa
    method = sa.get_bean_by_name if name else sa.get_bean_by_type
    param = name or BeanType
    timeout_second=CommonVar.get_application(get_stack_path(1)).get_sv().get_scan_timeout_second()
    with ThreadPoolExecutor() as executor:
        future = executor.submit(fn, method, param,timeout_second)
        return future.result()
