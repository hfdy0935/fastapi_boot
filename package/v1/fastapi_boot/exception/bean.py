class NotSupportFunctionBeanException(Exception):
    """
    - 不支持函数作为bean
    """

    def __init__(self, value: str = '不支持函数作为bean') -> None:
        super().__init__(value)


class ComponentUsePositionException(Exception):
    """
    - 组件只能定义在模块顶层
    """

    def __init__(self, v: str = '组件只能定义在模块顶层') -> None:
        super().__init__(v)


class BeanUsePositionException(Exception):
    """
    - Bean装饰器只能写在模块顶层函数上
    """

    def __init__(self, v: str = 'Bean装饰器只能写在模块顶层函数上') -> None:
        super().__init__(v)


class BeanDecoratedFunctionHasNoReturnAnnotationException(Exception):
    """
    - Bean装饰器必须返回一个对象
    """

    def __init__(self, v: str = 'Bean装饰器必须返回一个对象') -> None:
        super().__init__(v)


class BeanAutoWiredFailException(Exception):
    """
    - Bean自动注入失败
    """

    def __init__(self, v: str = 'Bean自动注入失败') -> None:
        super().__init__(v)


class UnExpectedConstructorException(Exception):
    """
    - 不期望的构造器
    """

    def __init__(self, v: str = '不期望的构造器') -> None:
        super().__init__(v)


class AutoWiredFailException(Exception):
    """自动装配失败，找不到Bean或找到多个Bean
    """

    def __init__(self, v: str = '自动装配失败') -> None:
        super().__init__(v)
