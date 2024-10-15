from typing import Any, Callable

from fastapi import FastAPI

from fastapi_boot.core.application.main import MainApplication
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.scan_model import Config


class FastApiBootApplication:
    """FastApiBootApplication, help you build the project, but you should start project by yourself, such as uvicorn.
    """

    def __init__(self, app: FastAPI, config: Config = Config()):
        self.app = MainApplication(app, config)
        for task in CommonVar.get_todo_list_by_app_pos(self.app.dot_prefix):
            task()
        CommonVar.clear_todo_list_by_app_pos(self.app.dot_prefix)
    def run(self):
        self.app.run()

    @staticmethod
    def run_app(app: FastAPI, config: Config = Config()):
        application = MainApplication(app, config)
        for task in CommonVar.get_todo_list_by_app_pos(application.dot_prefix):
            task()
        CommonVar.clear_todo_list_by_app_pos(application.dot_prefix)
        application.run()
