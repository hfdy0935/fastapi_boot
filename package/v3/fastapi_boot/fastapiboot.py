from fastapi import FastAPI

from fastapi_boot.core.application.main import MainApplication
from fastapi_boot.model.scan import Config
from fastapi_boot.utils import get_stack_path


class FastApiBootApplicationBuilder:
    def __init__(self) -> None:
        self.app: FastAPI | None = None
        self.app_config: dict = {}
        self.config: Config = Config()

    def build(self, stack_path: str):
        return MainApplication(
            app=self.app or FastAPI(**self.app_config), config=self.config, stack_path=stack_path
        ).app


records: dict[str, FastApiBootApplicationBuilder] = {}


class FastApiBootApplication:
    """启动类
    传了app实例再调用app_config修改配置或先修改配置再传app，则配置不生效；配置只能再没传app，由FastApiBootApplication生成配置时生效
    """

    @classmethod
    def app(cls, app: FastAPI):
        stack_path = get_stack_path(1)
        record = records.get(stack_path, FastApiBootApplicationBuilder())
        record.app = app
        records.update({stack_path: record})
        return cls

    @classmethod
    def app_config(cls, **kwargs):
        stack_path = get_stack_path(1)
        record = records.get(stack_path, FastApiBootApplicationBuilder())
        record.app_config = kwargs
        records.update({stack_path: record})
        return cls

    @classmethod
    def config(cls, config: Config):
        stack_path = get_stack_path(1)
        record = records.get(stack_path, FastApiBootApplicationBuilder())
        record.config = config
        records.update({stack_path: record})
        return cls

    @staticmethod
    def build():
        stack_path = get_stack_path(1)
        record = records.get(stack_path, FastApiBootApplicationBuilder())
        records.pop(stack_path)
        return record.build(stack_path)
