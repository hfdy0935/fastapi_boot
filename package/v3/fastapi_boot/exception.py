class InjectFailException(Exception):
    msg = "依赖注入失败"

    def __init__(self, msg: str = '依赖注入失败') -> None:
        super().__init__(msg)


class AppNotFoundException(Exception):
    msg = "app未找到，确保在app扫描路径内注入依赖"

    def __init__(self, msg: str = 'app未找到') -> None:
        super().__init__(msg)
