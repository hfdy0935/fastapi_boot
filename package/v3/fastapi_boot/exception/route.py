class RequestMethodException(Exception):
    """请求方法错误"""

    msg = "请求方法错误"

    def __init__(self, msg: str = "请求方法错误") -> None:
        super().__init__(msg)


class MappingUseTypeException(Exception):
    """请求映射装饰器类型错误"""

    msg = "请求映射装饰器类型错误"

    def __init__(self, msg: str = "请求映射装饰器类型错误") -> None:
        super().__init__(msg)
