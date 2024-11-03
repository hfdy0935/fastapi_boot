from fastapi import FastAPI

from fastapi_boot.core.application.main import MainApplication
from fastapi_boot.model.scan import Config
from fastapi_boot.utils import get_stack_path


class FastApiBootApplicationBuilder:
    def __init__(self) -> None:
        # 初始化为None，等最后build的时候还是空才用默认值
        self.app: FastAPI | None = None
        self.app_config: dict = {}
        self.config: Config | None = None

    def build(self, stack_path: str):
        return MainApplication(
            app=self.app or FastAPI(**self.app_config), config=self.config or Config(), stack_path=stack_path
        ).app


records: dict[str, FastApiBootApplicationBuilder] = {}


def get_current_builder(stack_path: str):
    """获取当前调用栈位置对应的FastApiBootApplicationBuilder"""
    return records.get(stack_path, FastApiBootApplicationBuilder())


class FastApiBootApplication:
    """启动类
    传了app实例再调用app_config修改配置或先修改配置再传app，则配置不生效；配置只能在没传app，由FastApiBootApplication生成配置时生效
    """

    @classmethod
    def app(cls, app: FastAPI):
        stack_path = get_stack_path(1)
        record = get_current_builder(stack_path)
        record.app = app
        records.update({stack_path: record})
        return cls

    @classmethod
    def app_config(cls, **kwargs):
        stack_path = get_stack_path(1)
        record = get_current_builder(stack_path)
        record.app_config = kwargs
        records.update({stack_path: record})
        return cls

    @classmethod
    def config(cls, config: Config):
        stack_path = get_stack_path(1)
        record = get_current_builder(stack_path)
        record.config = config
        records.update({stack_path: record})
        return cls

    @staticmethod
    def build():
        stack_path = get_stack_path(1)
        record = get_current_builder(stack_path)
        return record.build(stack_path)
