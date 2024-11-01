from fastapi import FastAPI

from fastapi_boot.core.application.main import MainApplication
from fastapi_boot.model.scan import Config


class FastApiBootApplication:
    """启动类"""

    @staticmethod
    def run(app: FastAPI = FastAPI(), config: Config = Config()):
        MainApplication(app, config)
        return app

    @staticmethod
    def fastapi(config: Config = Config(), **kwargs):
        app = FastAPI(**kwargs)
        MainApplication(app, config)
        return app
