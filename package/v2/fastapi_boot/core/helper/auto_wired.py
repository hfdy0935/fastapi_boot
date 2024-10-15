import time
from typing import Optional, TypeVar, Type

from fastapi_boot.core.application.scanner import ScannerApplication
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.exception.bean import AutoWiredFailException
from fastapi_boot.utils.generator import get_stack_path

T = TypeVar("T")


def find_bean(BeanType: Type[T], stack_path: str, name: str = "") -> T:
    res: Optional[T] = None
    while True:
        # 先等获取到application
        application = CommonVar.get_application(stack_path)
        if application: break

    sa: ScannerApplication = application.get_sa()
    # 开始计时，装配
    start = time.time()
    while True:
        method = sa.get_bean_by_name if name else sa.get_bean_by_type
        param = name or BeanType
        timeout_second = (
            application.get_sv().get_scan_timeout_second()
        )
        print('\r',end='')
        if res := method(param):
            break
        if time.time() - start > timeout_second:
            raise AutoWiredFailException(
                f'扫描超时，Bean {"名" + param if isinstance(param, str) else "类型" + param.__name__} 未找到'
            )
    return res


def AutoWired(BeanType: Type[T], name: str = "") -> T:
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
    stack_path = get_stack_path(1)
    return find_bean(BeanType,stack_path,name)
