class InjectFailException(Exception):
    """依赖注入失败"""

    msg = "依赖注入失败"

    def __init__(self, msg: str = "依赖注入失败") -> None:
        super().__init__(msg)
