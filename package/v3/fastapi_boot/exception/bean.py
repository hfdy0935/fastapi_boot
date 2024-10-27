class DependencyTypeException(Exception):
    """依赖类型错误"""

    msg = "依赖类型错误"

    def __init__(self, msg: str = "依赖类型错误") -> None:

        super().__init__(msg)


class DependencyPositionException(Exception):
    """依赖位置错误"""

    msg = "依赖位置错误"

    def __init__(self, msg: str = "依赖位置错误") -> None:
        super().__init__(msg)


class BeanUsePositionException(Exception):
    """Bean装饰器只能写在模块顶层函数上"""

    msg = "Bean装饰器只能写在模块顶层函数上"

    def __init__(self, msg: str = "Bean装饰器只能写在模块顶层函数上") -> None:
        super().__init__(msg)


class BeanTypeException(Exception):
    """Bean装饰器必须返回一个对象"""

    msg = "Bean装饰器必须返回一个对象"

    def __init__(self, msg: str = "Bean装饰器必须返回一个对象") -> None:
        super().__init__(msg)


class InjectFailException(Exception):
    """依赖注入失败"""

    msg = "依赖注入失败"

    def __init__(self, msg: str = "依赖注入失败") -> None:
        super().__init__(msg)
