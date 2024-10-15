class UnExpectedWebsocketInRequestMappingException(Exception):
    '''
    - RequestMapping使用了websocket
    - 因为websocket和其他方法的参数和处理方式不同，所以需要分开写
    '''

    def __init__(self, v: str = 'websocket不能和其他方法一起写进methods，建议使用WebsocketMapping') -> None:
        super().__init__(v)


class RequestMethodNotFoundException(Exception):
    """
    - 请求方法错误
    """

    def __init__(self, v: str = '请求方法错误') -> None:
        super().__init__(v)


class ClassWithSpecificDecoratorException(Exception):
    """
    - 具体的请求方法装饰器不能装饰类
    """

    def __init__(self, v: str = '具体的请求方法装饰器不能装饰类') -> None:
        super().__init__(v)
